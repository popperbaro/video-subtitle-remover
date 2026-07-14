@echo off
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Installing dependencies...
    .\.venv\Scripts\python -m pip install setuptools wheel
    .\.venv\Scripts\python -m pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
    .\.venv\Scripts\python -m pip install torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu118
    .\.venv\Scripts\python -m pip install -r requirements.txt
)
echo Starting Video Subtitle Remover...
start "" .\.venv\Scripts\pythonw.exe gui.py
exit
