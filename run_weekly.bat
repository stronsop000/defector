@echo off
REM Weekly refresh: scrape, classify new low-star reviews, regenerate memo + copy.
REM Schedule via Task Scheduler (see README "Automating weekly refresh on Windows").

setlocal
cd /d "%~dp0"

set "LOGDIR=%~dp0logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set "STAMP=%date:~10,4%-%date:~4,2%-%date:~7,2%_%time:~0,2%%time:~3,2%"
set "STAMP=%STAMP: =0%"
set "LOG=%LOGDIR%\weekly_%STAMP%.txt"

echo === Defector weekly refresh @ %date% %time% === > "%LOG%"

echo --- scrape --- >> "%LOG%"
python -m src.scrape >> "%LOG%" 2>&1

echo --- classify --- >> "%LOG%"
python -m src.classify >> "%LOG%" 2>&1

echo --- synthesize --- >> "%LOG%"
python -m src.synthesize >> "%LOG%" 2>&1

echo === Done === >> "%LOG%"
type "%LOG%"
