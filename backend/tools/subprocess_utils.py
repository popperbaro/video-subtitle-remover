# -*- coding: utf-8 -*-
"""
@desc: Subprocess utilities to hide console windows on Windows.
"""
import sys
import subprocess

# On Windows, set CREATE_NO_WINDOW flag to prevent terminal windows from appearing.
# This is especially important when running with pythonw.exe (GUI mode).
if sys.platform == 'win32':
    SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW
else:
    SUBPROCESS_FLAGS = 0
