:git add .
@echo off
set /p var=�п�JCommit:
git commit -a --amend --no-edit %version%
git push heroku master