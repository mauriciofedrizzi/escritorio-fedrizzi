@echo off
REM Coleta as contas de pesquisa\referencias.txt e manda para o GitHub
cd /d "C:\Users\mauri\escritorio-fedrizzi"
git pull
"C:\Users\mauri\AppData\Local\Programs\Python\Python312\python.exe" instagram\pesquisa\coletar.py --enviar
pause
