@echo off
cd /d "%~dp0.."
py src\main.py --vfs vfs_deep --script scripts\stage4.vsh
