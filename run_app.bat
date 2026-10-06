@echo off
chcp 65001 >nul
echo ========================================================
echo   Taiwan Weather Forecast 氣象預報互動系統 啟動中...
echo ========================================================
echo.
echo 正在檢查 Python 與 Streamlit 環境...
py -m streamlit run app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 啟動失敗，請確認已安裝相依套件：py -m pip install -r requirements.txt
    pause
)
