@echo off
title GitHub-ga yuklash
echo Loyihangiz GitHub-ga yuklanmoqda...
echo.

git add .
git commit -m "Yangilanish: %date% %time%"
git push origin main

echo.
echo ==========================================
echo O'zgarishlar GitHub-ga muvaffaqiyatli ketdi! ✅
echo ==========================================
echo.
pause
