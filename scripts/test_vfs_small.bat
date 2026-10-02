@echo off
cd /d "%~dp0.."
py src\main.py --vfs vfs_small --script scripts\stage3.vsh
