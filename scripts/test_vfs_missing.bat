@echo off
cd /d "%~dp0.."
py src\main.py --vfs vfs_no_such --script scripts\stage3.vsh
