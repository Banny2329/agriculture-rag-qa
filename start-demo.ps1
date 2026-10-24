# 一键启动农技问答 RAG 系统（后端 + 前端 + 浏览器）
# 用法：双击 start-demo.bat，或在 PowerShell 中运行 .\start-demo.ps1
# 前置：backend 依赖已装（pip install -r requirements.txt）、frontend 已装（npm install）
$ErrorActionPreference = "Stop"

$Root      = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir  = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "   农技问答 RAG 智能系统 - 一键启动" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# 启动后端（独立窗口）
Write-Host "[1/3] 启动后端 FastAPI 服务..." -ForegroundColor Cyan
Start-Process -FilePath "python" `
  -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" `
  -WorkingDirectory $BackendDir -WindowStyle Normal

# 启动前端（独立窗口）
Write-Host "[2/3] 启动前端 Vite 开发服务器..." -ForegroundColor Cyan
Start-Process -FilePath "cmd.exe" `
  -ArgumentList "/k", "npm run dev" `
  -WorkingDirectory $FrontendDir -WindowStyle Normal

# 等待服务就绪后打开浏览器
Write-Host "[3/3] 等待服务就绪，即将打开浏览器..." -ForegroundColor Cyan
Start-Sleep -Seconds 10
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "启动完成！" -ForegroundColor Green
Write-Host "  前端页面 : http://localhost:5173"
Write-Host "  后端文档 : http://127.0.0.1:8000/docs"
Write-Host "提示：首次页面出现「知识库未建档」时，点击「扫描建档」建立向量索引即可问答。"