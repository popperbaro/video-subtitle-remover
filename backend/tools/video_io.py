import os
import queue
import subprocess
import threading

from .subprocess_utils import SUBPROCESS_FLAGS

import cv2
import numpy as np

from .ffmpeg_cli import FFmpegCLI
from .diag_log import log as diag_log


class FramePrefetcher:
    """
    后台线程预解码视频帧，使 I/O 与模型推理重叠。
    接口兼容 cv2.VideoCapture（read/release）。
    """

    def __init__(self, video_cap, buffer_size=10):
        self.cap = video_cap
        self._buffer = queue.Queue(maxsize=buffer_size)
        self._stopped = False
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self):
        while not self._stopped:
            ret, frame = self.cap.read()
            self._buffer.put((ret, frame))
            if not ret:
                break

    def read(self):
        """读取下一帧，接口与 cv2.VideoCapture.read() 一致。"""
        return self._buffer.get()

    def get(self, propId):
        return self.cap.get(propId)

    def stop(self):
        """停止预读取，不释放底层 video_cap。"""
        self._stopped = True
        try:
            while not self._buffer.empty():
                self._buffer.get_nowait()
        except queue.Empty:
            pass
        self._thread.join(timeout=5)

    def release(self):
        self.stop()
        self.cap.release()


class FFmpegVideoWriter:
    """
    通过 FFmpeg 管道写入帧，使用 libx264 编码。
    接口兼容 cv2.VideoWriter（write/release）。
    """

    def __init__(self, output_path, fps, size):
        w, h = size
        self._output_path = output_path
        self._fps = fps
        self._size = (w, h)
        self._fallback_writer = None
        self._frames_written = 0
        self._stderr_buf = []
        cmd = [
            FFmpegCLI.instance().ffmpeg_path,
            '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{w}x{h}',
            '-pix_fmt', 'bgr24',
            '-r', str(fps),
            '-i', '-',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-crf', '18',
            '-preset', 'fast',
            '-loglevel', 'error',
            output_path
        ]
        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            creationflags=SUBPROCESS_FLAGS,
        )
        self._stderr_thread = threading.Thread(
            target=self._drain_stderr, daemon=True
        )
        self._stderr_thread.start()

    def _drain_stderr(self):
        try:
            while True:
                chunk = self._process.stderr.readline()
                if not chunk:
                    break
                try:
                    line = chunk.decode('utf-8', errors='replace').rstrip()
                except Exception:
                    line = str(chunk)
                if line:
                    self._stderr_buf.append(line)
                    if len(self._stderr_buf) > 50:
                        self._stderr_buf = self._stderr_buf[-50:]
                    print(f"[ffmpeg] {line}")
                    diag_log(f"[ffmpeg] {line}")
        except Exception:
            pass

    def _ensure_fallback_writer(self):
        if self._fallback_writer is None:
            self._fallback_writer = cv2.VideoWriter(
                self._output_path,
                cv2.VideoWriter_fourcc(*'mp4v'),
                self._fps,
                self._size
            )
            if not self._fallback_writer.isOpened():
                self._fallback_writer = None
                raise RuntimeError(
                    f"failed to initialize cv2 fallback video writer for {self._output_path}"
                )

    def _switch_to_fallback(self, reason):
        tail = " | ".join(self._stderr_buf[-10:])
        msg = f"[FFmpegVideoWriter] switch to cv2 fallback: {reason}; ffmpeg stderr tail: {tail}"
        print(msg)
        diag_log(msg)
        try:
            if self._process and self._process.stdin:
                self._process.stdin.close()
        except Exception:
            pass
        try:
            if self._process:
                self._process.wait(timeout=2)
        except Exception:
            try:
                self._process.terminate()
            except Exception:
                pass
        self._ensure_fallback_writer()

    def write(self, frame):
        """写入一帧（numpy BGR 数组）。"""
        if frame.dtype != np.uint8:
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        h_in, w_in = frame.shape[:2]
        if (w_in, h_in) != self._size:
            frame = cv2.resize(frame, self._size)
        if self._fallback_writer is not None:
            self._fallback_writer.write(frame)
            self._frames_written += 1
            return
        if self._process.poll() is not None:
            self._switch_to_fallback(
                f"ffmpeg exited with code {self._process.returncode}"
            )
            self._fallback_writer.write(frame)
            self._frames_written += 1
            return
        try:
            self._process.stdin.write(frame.tobytes())
            self._frames_written += 1
        except (BrokenPipeError, OSError) as e:
            self._switch_to_fallback(str(e))
            self._fallback_writer.write(frame)
            self._frames_written += 1

    def release(self):
        """关闭管道并等待编码完成。"""
        mode = "cv2-fallback" if self._fallback_writer is not None else "ffmpeg"
        if self._fallback_writer is not None:
            self._fallback_writer.release()
        else:
            try:
                self._process.stdin.close()
            except BrokenPipeError:
                pass
            try:
                self._process.wait(timeout=600)
            except subprocess.TimeoutExpired:
                self._process.terminate()
                self._process.wait(timeout=5)
            if self._process.returncode not in (0, None):
                tail = " | ".join(self._stderr_buf[-10:])
                err_msg = (
                    f"[FFmpegVideoWriter] ffmpeg exited with code "
                    f"{self._process.returncode}; stderr tail: {tail}"
                )
                print(err_msg)
                diag_log(err_msg)
        try:
            size = os.path.getsize(self._output_path) if os.path.exists(self._output_path) else 0
        except Exception:
            size = -1
        summary = (
            f"[FFmpegVideoWriter] release: mode={mode}, "
            f"frames_written={self._frames_written}, file_size={size}, path={self._output_path}"
        )
        print(summary)
        diag_log(summary)
