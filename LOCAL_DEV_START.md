# 本地开发启动说明

本文记录本项目的前后端本地启动方式。所有命令默认在**项目根目录**执行，不依赖某个开发者的绝对路径。

## 前置要求

- 已安装 Node.js 和 npm。
- 已安装 conda。
- 已创建后端 conda 环境：`error_correction`。
- 已安装前端依赖：`cd frontend && npm install`。
- 已安装后端依赖，或 conda 环境中已经包含项目所需 Python 包。

## 后端启动

后端需要使用 conda 环境：

```text
error_correction
```

手动启动：

```powershell
cd backend
conda activate error_correction
python .\web_app.py
```

如果当前 PowerShell 没有初始化 conda，也可以在项目根目录执行：

```powershell
conda run -n error_correction python .\backend\web_app.py
```

启动成功后应看到后端监听：

```text
http://localhost:5001
```

也可能显示：

```text
http://127.0.0.1:5001
http://0.0.0.0:5001
```

## 前端启动

手动启动：

```powershell
cd frontend
npm run dev
```

启动成功后访问：

```text
http://127.0.0.1:5173
```

## 一次性启动两个 PowerShell 窗口

在项目根目录执行：

```powershell
$root = (Get-Location).Path
Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$root\backend'; conda activate error_correction; python .\web_app.py"
Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$root\frontend'; npm run dev"
```

如果当前 PowerShell 没有初始化 conda，后端窗口可改用 `conda run`：

```powershell
$root = (Get-Location).Path
Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$root'; conda run -n error_correction python .\backend\web_app.py"
Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$root\frontend'; npm run dev"
```

## 端口检查

检查后端是否监听：

```powershell
Get-NetTCPConnection -LocalPort 5001 -State Listen
```

检查前端是否监听：

```powershell
Get-NetTCPConnection -LocalPort 5173 -State Listen
```

## 当前确认过的默认值

- 后端 conda 环境：`error_correction`
- 后端入口：`backend\web_app.py`
- 后端端口：`5001`
- 前端入口命令：`npm run dev`
- 前端端口：`5173`
