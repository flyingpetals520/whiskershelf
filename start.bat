@echo off
title 温馨文献库
color 0E
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

echo.
echo  ============================================
echo      温馨文献库  Paper Library Manager
echo  ============================================
echo.
echo  正在启动服务，请稍候...
echo  启动后请用浏览器访问: http://127.0.0.1:8080
echo.

python app.py

echo.
echo  服务已停止。
pause
