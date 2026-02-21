# NotebookLM Automation Tools

This project is an extension toolkit based on [notebooklm-py](https://github.com/teng-lin/notebooklm-py), designed to automate the analysis workflow of Google NotebookLM. It supports deep analysis of YouTube videos, web URLs, and various local files (PDF, MP4, MP3, etc.), and provides an MCP (Model Context Protocol) server for AI agents to invoke.

## ✨ Key Features

1.  **Multi-Format File Analysis**: Supports uploading and analyzing local files, including PDF documents, MP4 videos, MP3 audio, etc.
2.  **YouTube Batch Analysis**: Automatically grabs videos from a playlist, transcribes them, and generates deep reports in Traditional Chinese.
3.  **MCP Server Integration**: Provides a standard MCP interface, allowing AI assistants like Claude or Cursor to directly invoke NotebookLM for analysis.
4.  **Automated Report Generation**: All analysis results are automatically exported as structured reports in Markdown format.

## 🛠️ Setup

It is recommended to use [uv](https://github.com/astral-sh/uv) for Python environment management and package installation to ensure dependency stability.

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

## 🚀 Usage Guide

### 1. Authentication (Required for First Run)

Since the tool needs to access your NotebookLM account, you must log in first:

**With Browser Environment (Local):**
```bash
uv run notebooklm login
```
After logging into your Google account, close the window and press Enter in the terminal.

**Headless Mode (Remote/Headless):**
Run `notebooklm login` on your **local machine**, then copy the generated `storage_state.json` (usually located in `~/.notebooklm-py/` or `%LOCALAPPDATA%/notebooklm-py/`) to the same location in this project environment, or set the environment variable `NOTEBOOKLM_AUTH_JSON`.

### 2. Analyze Local Files (PDF, MP4, MP3)

Use `analyze_files.py` to analyze a single file. The program will automatically upload the file, create a notebook, perform question-answering analysis, and save the report.

```bash
# Analyze PDF
uv run python scripts/analyze_files.py /path/to/document.pdf

# Analyze Video (MP4)
uv run python scripts/analyze_files.py /path/to/video.mp4

# Analyze Audio (MP3)
uv run python scripts/analyze_files.py /path/to/audio.mp3
```
The report will be saved as `[filename]_analysis.md`.

### 3. YouTube / URL Batch Analysis

Batch analysis for YouTube playlists or specific URLs.

**Step A: Collect URLs**
Modify and run `collect_urls.py` out of `utils/youtube/` to grab playlist links (defaults to the first 60 videos):
```bash
uv run python utils/youtube/collect_urls.py
```
This will generate `video_urls.json`.

**Step B: Execute Analysis**
```bash
uv run python scripts/analyze_urls.py
```
The program will read the json list, analyze them sequentially, and save the results in the `analysis_reports/` folder.

### 4. Start MCP Server (For AI Agents)

This project includes an MCP Server (`mcp_server.py`) that provides the following tools for AI to avail:
- `analyze_file_with_notebooklm`: Analyze local files (supports various formats)
- `analyze_remote_file_with_notebooklm`: Analyze remote files via HTTP URLs
- `analyze_url_with_notebooklm`: Analyze web pages or YouTube links

**Start MCP Server (SSE Mode):**
```bash
uv run fastmcp run scripts/mcp_server.py --transport sse --port 52500
```

### 5. Start FastAPI Server (REST API)

If you prefer a standard REST API interface instead of MCP, you can use the FastAPI server. It provides endpoints for local file upload (`upload`), remote file URL (`remote-file`), or standard URL (`url`) analysis.

**Start FastAPI Server:**
```bash
# Default port is 52501
uv run python scripts/fastapi_server.py
```
After starting the server, you can view the interactive API documentation at: http://localhost:52501/docs

**Usage Example:**
A dedicated client script `fastapi_client.py` has been provided which can upload local files and trigger analysis directly from your terminal:
```bash
# Basic usage
uv run python scripts/fastapi_client.py /path/to/my_document.pdf

# Add a custom prompt
uv run python scripts/fastapi_client.py /path/to/my_video.mp4 --prompt "Please summarize the first three minutes of this video"
```

### 6. Running with Docker

You can also run the MCP server or FastAPI Server using Docker.

You need to pass your authentication credentials. The easiest way is to pass the `NOTEBOOKLM_AUTH_JSON` environment variable.

> **Where to find `storage_state.json`?**
> After running `notebooklm login` locally, the file is usually located at:
> - **Windows**: `%LOCALAPPDATA%\notebooklm\storage_state.json`
> - **macOS / Linux**: `~/.notebooklm/storage_state.json`

You can pass the entire JSON string via an environment variable (Recommended during `docker run`):
```bash
export AUTH_JSON=$(cat ~/.notebooklm/storage_state.json)
```

#### Option A: Run MCP Server

**Build the image:**
```bash
docker build -t gy-notebooklm-mcp -f dockerfile/Dockerfile.mcp .
```

**Run the container:**
```bash
docker run -d -p 52500:8000 \
  --name gy-notebooklm-mcp \
  -e NOTEBOOKLM_AUTH_JSON="$AUTH_JSON" \
  gy-notebooklm-mcp
```
*Note: We map container port 8000 to host port 52500.*

#### Option B: Run FastAPI Server

**Build the image:**
```bash
docker build -t gy-notebooklm-fastapi -f dockerfile/Dockerfile.fastapi .
```

**Run the container:**
```bash
docker run -d -p 52501:52501 \
  --name gy-notebooklm-fastapi \
  -e NOTEBOOKLM_AUTH_JSON="$AUTH_JSON" \
  gy-notebooklm-fastapi
```

**MCP Client Example:**
You can run `mcp_client.py` or `mcp_http_client.py` to test the connection and tool invocation.

## 📂 Project Structure

- `scripts/analyze_files.py`: General file analysis script (Core tool)
- `scripts/mcp_server.py`: MCP Server implementation
- `scripts/analyze_urls.py`: URL/YouTube batch analysis script
- `scripts/fastapi_server.py`: FastAPI server for standard REST API endpoints.
- `scripts/fastapi_client.py`: FastAPI client script.
- `utils/youtube/collect_urls.py`: YouTube playlist crawler
- `dockerfile/`: Dockerfiles for MCP and FastAPI servers
- `requirements.txt`: Project dependency list
- `analysis_reports/`: Output directory for analysis reports
