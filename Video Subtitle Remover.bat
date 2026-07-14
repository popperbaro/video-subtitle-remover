@echo off
chcp 65001 >nul 2>&1
title Video Subtitle Remover
cd /d "%~dp0"

REM ===== Video Subtitle Remover =====
REM Tool xoa phu de khoi video su dung AI

if not exist ".venv" (
    echo ============================================
    echo   Setting up Video Subtitle Remover...
    echo ============================================
    echo.
    echo [1/4] Creating virtual environment...
    python -m venv .venv
    echo.
    echo [2/4] Installing base tools...
    .\.venv\Scripts\python -m pip install setuptools wheel
    echo.
    echo [3/4] Installing PaddlePaddle GPU...
    .\.venv\Scripts\python -m pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
    echo.
    echo [4/4] Installing PyTorch and dependencies...
    .\.venv\Scripts\python -m pip install torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu118
    .\.venv\Scripts\python -m pip install -r requirements.txt
    echo.
    echo ============================================
    echo   Setup complete!
    echo ============================================
    echo.
)

echo Starting Video Subtitle Remover...
start "" .\.venv\Scripts\pythonw.exe gui.py
exit
