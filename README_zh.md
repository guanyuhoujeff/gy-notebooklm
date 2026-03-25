# NotebookLM 自動化分析工具 (NotebookLM Automation Tools)

本專案是一個基於 [notebooklm-py](https://github.com/teng-lin/notebooklm-py) 的擴充工具箱，旨在自動化 Google NotebookLM 的分析流程。支援 YouTube 影片、網頁連結以及各種本地檔案 (PDF, MP4, MP3 等) 的深度分析，並提供 MCP (Model Context Protocol) 伺服器供 AI 代理人調用。

## ✨ 主要功能

1.  **多格式檔案分析**：支援上傳並分析本地檔案，包括 PDF 文件、MP4 影片、MP3 音訊等。
2.  **YouTube 批次分析**：自動抓取播放清單影片，轉錄並生成繁體中文深度報告。
3.  **MCP 伺服器整合**：提供標準 MCP 介面，讓 Claude、Cursor 等 AI 助手可以直接調用 NotebookLM 進行分析。
4.  **自動化報告生成**：所有分析結果皆自動匯出為 Markdown 格式的結構化報告。

## 🛠️ 環境建置

本專案建議使用 [uv](https://github.com/astral-sh/uv) 進行 Python 環境管理與套件安裝，以確保依賴套件的穩定性。

```bash
# 1. Update system & install python (if needed)
sudo apt update && sudo apt install -y python3.12 python3.12-venv ffmpeg

# 2. Setup environment
curl -lsAf https://astral.sh/uv/install.sh | sh
python3.12 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
uv pip install -r requirements.txt
playwright install chromium
```

## 🚀 使用說明

### 1. 身份驗證 (首次執行必要)

由於工具需存取您的 NotebookLM 帳號，請先進行登入：

**有瀏覽器環境 (Local):**
```bash
uv run notebooklm login
```
登入 Google 帳號後，關閉視窗並在終端機按 Enter。

**無頭模式 (Remote/Headless):**
在本地電腦執行 `notebooklm login`，將產生的 `storage_state.json` (通常在 `~/.notebooklm-py/` 或 `%LOCALAPPDATA%/notebooklm-py/`) 複製到伺服器的同樣位置，或設定環境變數 `NOTEBOOKLM_AUTH_JSON`。

### 2. 分析本地檔案 (PDF, MP4, MP3)

使用 `analyze_files.py` 來分析單一檔案。程式會自動上傳檔案、建立筆記本、進行問答分析並儲存報告。

```bash
# 分析 PDF
uv run python scripts/analyze_files.py /path/to/document.pdf

# 分析 影片 (MP4)
uv run python scripts/analyze_files.py /path/to/video.mp4

# 分析 音訊 (MP3)
uv run scripts/python analyze_files.py /path/to/audio.mp3
```
報告將儲存為 `[檔名]_analysis.md`。

### 3. YouTube / URL 批次分析

針對 YouTube 播放清單或特定網址進行批次分析。

**步驟 A：收集連結**
修改並執行位於 `utils/youtube/` 內的 `collect_urls.py` 來抓取播放清單連結 (預設抓取前 60 部)：
```bash
uv run python utils/youtube/collect_urls.py
```
這會產生 `video_urls.json`。

**步驟 B：執行分析**
```bash
uv run python scripts/analyze_urls.py
```
程式會讀取 json 清單，依序分析並將結果存入 `analysis_reports/` 資料夾。

### 4. 啟動 MCP 伺服器 (供 AI Agent 使用)

本專案包含一個 MCP Server (`mcp_server.py`)，提供以下工具供 AI 調用：
- `analyze_file_with_notebooklm`: 分析本地檔案 (支援各格式)
- `analyze_remote_file_with_notebooklm`: 透過 HTTP URL 分析遠端檔案
- `analyze_url_with_notebooklm`: 分析網頁或 YouTube 連結

**啟動 MCP Server (SSE 模式):**
```bash
uv run fastmcp run scripts/mcp_server.py --transport sse --port 52500
```

### 5. 啟動 FastAPI 伺服器 (REST API)

如果您偏好標準的 REST API 介面而非 MCP，可以使用 FastAPI 伺服器。它提供了用於分析本地檔案 (`upload`)、遠端檔案 (`remote-file`) 或是普通網址 (`url`) 的端點。

**啟動 FastAPI 伺服器:**
```bash
# 預設 Port 為 52501
uv run python scripts/fastapi_server.py
```
啟動伺服器後，您可以前往 http://localhost:52501/docs 查看互動式的 API 測試文件。

**呼叫 FastAPI 的客戶端範例:**
提供了一個專用的客戶端腳本 `fastapi_client.py`，可以直接在終端機上傳本地檔案並進行分析：
```bash
# 基本用法
uv run python scripts/fastapi_client.py /path/to/my_document.pdf

# 附加自訂 Prompt
uv run python scripts/fastapi_client.py /path/to/my_video.mp4 --prompt "請幫我摘要這部影片前三分鐘的重點"
```

### 6. 使用 Docker 執行

您也可以透過 Docker 來執行 MCP 或 FastAPI Server。

您需要傳遞身份驗證資訊。最簡單的方法是掛載您的 `storage_state.json` 或傳遞 `NOTEBOOKLM_AUTH_JSON` 環境變數。

> **如何找到 `storage_state.json`？**
> 在本地執行 `notebooklm login` 後，檔案通常位於：
> - **Windows**: `%LOCALAPPDATA%\notebooklm\storage_state.json`
> - **macOS / Linux**: `~/.notebooklm/storage_state.json`

如果不想掛載檔案，您可以使用環境變數傳入整個 JSON 字串 (docker run 時，建議使用環境變數)：
```bash
export AUTH_JSON=$(cat ~/.notebooklm/storage_state.json)
```

#### 選項 A: 執行 MCP Server

**建置映像檔:**
```bash
docker build -t gy-notebooklm-mcp -f dockerfile/Dockerfile.mcp .
```

**啟動容器:**
```bash
docker run -d -p 52500:8000 \
  --name gy-notebooklm-mcp \
  -e NOTEBOOKLM_AUTH_JSON="$AUTH_JSON" \
  gy-notebooklm-mcp
```
*注意：我們將容器的 8000 port 對應到主機的 52500 port。*

#### 選項 B: 執行 FastAPI Server

**建置映像檔:**
```bash
docker build -t gy-notebooklm-fastapi -f dockerfile/Dockerfile.fastapi .
```

**啟動容器:**
```bash
docker run -d -p 52501:52501 \
  --restart always \
  --name gy-notebooklm-fastapi \
  -e NOTEBOOKLM_AUTH_JSON="$AUTH_JSON" \
  gy-notebooklm-fastapi
```

**MCP Client 範例:**
您可以執行 `mcp_client.py` 或 `mcp_http_client.py` 來測試連線與工具呼叫。

## 📂 專案結構

- `scripts/analyze_files.py`: 通用檔案分析腳本 (核心工具)
- `scripts/mcp_server.py`: MCP 伺服器實作
- `scripts/analyze_urls.py`: URL/YouTube 批次分析腳本
- `scripts/fastapi_server.py`: 標準 REST API 伺服器
- `scripts/fastapi_client.py`: FastAPI 互動腳本
- `utils/youtube/collect_urls.py`: YouTube 播放清單爬蟲
- `dockerfile/`: MCP 和 FastAPI 的 Dockerfile 目錄
- `requirements.txt`: 專案依賴列表
- `analysis_reports/`: 存放分析報告的輸出目錄


## 常見問題

### 1. 認證已過期。storage_state.json 裡的 Google 登入 cookie 已經失效了。

您需要先刪除原來的 storage_state.json，然後再一次本機重新登入