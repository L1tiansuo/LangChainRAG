@echo off
echo ========================================
echo   Stopping RAG services...
echo ========================================

echo.
echo Killing all Python processes...
taskkill /F /IM python.exe 2>nul

echo Killing all Node.js processes...
taskkill /F /IM node.exe 2>nul

echo.
echo ========================================
echo   Done. All services stopped.
echo ========================================
pause
