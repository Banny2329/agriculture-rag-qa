@echo off
chcp 65001 >nul
title 农技问答 RAG 系统 - 一键启动
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-demo.ps1"
echo.
pause