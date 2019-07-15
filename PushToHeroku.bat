git add .
@echo off
set /p var=½Ð¿é¤JCommit:
git commit -am %version%
git push heroku master