@echo off
setlocal
set "PY=C:\Users\Lenovo\AppData\Local\Programs\claude-doctor\venv\Scripts\python.exe"
set "SRC=E:\claude-doctor\src"
set "PYTHONPATH=%SRC%"
"%PY%" -m claude_doctor.cli %*
endlocal
