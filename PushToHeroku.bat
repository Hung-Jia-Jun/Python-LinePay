:git add .
@echo off
set /p var=½Ð¿é¤JCommit:
git commit -a --amend --no-edit %version%
git push heroku master