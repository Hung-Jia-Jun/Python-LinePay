git add .
@echo off
set /p var=�п�JCommit:
git commit -am %version%
git push heroku master