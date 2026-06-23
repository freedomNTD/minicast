@echo off
REM MiniCast 一键启动脚本
REM 双击运行即可，会自动切到脚本所在目录并启动 MiniCast
chcp 65001 >nul
cd /d "%~dp0"

REM 优先用 py launcher，回退到默认 python
where py >nul 2>&1
if %errorlevel%==0 (
    py -3 minicast.py
) else (
    python minicast.py
)

if %errorlevel% neq 0 (
    echo.
    echo [启动失败] 请检查:
    echo   1. 已安装 Python 3.9+
    echo   2. 已安装依赖: pip install -r requirements\common.txt
    echo   3. Windows 下需要 pywin32: pip install pywin32
    echo   4. bin\mpv.exe 已就位 (投屏播放需要)
    echo.
    pause
)
