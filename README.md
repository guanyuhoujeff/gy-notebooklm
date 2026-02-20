# YouTube 影片分析專案 (使用 NotebookLM)

本專案旨在自動下載指定 YouTube 播放清單中的最新影片音訊，並使用 Google NotebookLM 進行內容分析。

## 功能

1.  **自動下載**：抓取播放清單中最新的 10 部影片，並轉換為 MP3 音訊。
2.  **AI 分析**：自動上傳音訊至 NotebookLM，建立專屬筆記本，並生成關鍵總結與洞察。

## 環境建置 (使用 `uv`)

本專案建議使用 [uv](https://github.com/astral-sh/uv) 進行 Python 環境管理與套件安裝。

<!-- 環境建置 -->
```bash
conda deactivate

sudo apt update && sudo apt upgrade -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.12 -y
sudo apt install python3.12-venv
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12
pip --version
python3.12 -m venv .venv
source .venv/bin/activate
pip install uv
uv pip install -r requirements.txt
```
uv pip install jupyter notebook
uv run jupyter notebook

<!-- run python pdf analysis -->
uv run python analyze_pdf.py test.pdf

<!-- run python url analysis -->
uv run python analyze_urls.py

<!-- run mcp server -->
uv run fastmcp run mcp_server.py --transport sse --port 8005


```bash
# 安裝 Playwright 瀏覽器 (用於 NotebookLM 登入)
playwright install chromium
```

## 使用說明

### 第一步：收集影片連結

執行以下指令，從播放清單中提取前 **60** 部影片的連結：

```bash
python collect_urls.py
```

完成後會產生 `video_urls.json` 檔案。

### 第二步：身份驗證 (重要！)

由於 `notebooklm-py` 需要存取您的 Google NotebookLM 帳號，首次使用前必須進行登入。

**本地執行 (有螢幕/瀏覽器環境)：**

```bash
notebooklm login
```
這會開啟一個瀏覽器視窗，請登入您的 Google 帳號。登入完成並看到 NotebookLM 首頁後，回到終端機按 Enter 完成驗證。

**遠端/無頭模式執行 (Headless)：**

若您在此環境無法開啟瀏覽器，請在**本地電腦**執行上述 `notebooklm login`，然後將生成的 `storage_state.json` (通常位於 `~/.notebooklm-py/` 或 `User/AppData/Local/notebooklm-py/`) 複製到此專案環境的相同位置，或者設定環境變數 `NOTEBOOKLM_AUTH_JSON`。

### 第三步：執行分析

確認已登入後，執行分析腳本：

```bash
python analyze_urls.py
```

程式將自動：
1. 讀取 `video_urls.json` 中的 60 部影片。
2. 為**每一部影片**建立一個獨立的 NotebookLM 專案。
3. 針對該影片進行繁體中文深度分析。
4. 將結果分別儲存為 `analysis_reports/[影片標題]_analysis_result.md`。

> 注意：處理 60 部影片可能需要較長時間，請耐心等待。

## 檔案結構

- `collect_urls.py`: 影片連結收集腳本
- `analyze_urls.py`: NotebookLM 分析腳本 (使用 URL)
- `video_urls.json`: 影片連結清單 (60 部)
- `analysis_reports/`: 存放個別影片分析報告的資料夾
