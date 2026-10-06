@echo off
chcp 65001 >nul
echo ========================================================
echo   正在推送專案至 GitHub: https://github.com/nelson0914/HW1.git
echo ========================================================
echo.
"C:\Users\user\AppData\Local\GitHubDesktop\app-3.4.9\resources\app\git\cmd\git.exe" push -u origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   [成功] 專案已順利推送到 GitHub (https://github.com/nelson0914/HW1)！
    echo ========================================================
) else (
    echo.
    echo 推送遭遇認證問題，請檢查 GitHub 登入狀態或權限。
)
echo.
pause
