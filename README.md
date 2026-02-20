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
uv run python analyze_files.py /path/to/document.pdf

# Analyze Video (MP4)
uv run python analyze_files.py /path/to/video.mp4

# Analyze Audio (MP3)
uv run python analyze_files.py /path/to/audio.mp3
```
The report will be saved as `[filename]_analysis.md`.

### 3. YouTube / URL Batch Analysis

Batch analysis for YouTube playlists or specific URLs.

**Step A: Collect URLs**
Modify and run `collect_urls.py` to grab playlist links (defaults to the first 60 videos):
```bash
uv run python collect_urls.py
```
This will generate `video_urls.json`.

**Step B: Execute Analysis**
```bash
uv run python analyze_urls.py
```
The program will read the json list, analyze them sequentially, and save the results in the `analysis_reports/` folder.

### 4. Start MCP Server (For AI Agents)

This project includes an MCP Server (`mcp_server.py`) that provides the following tools for AI to avail:
- `analyze_file_with_notebooklm`: Analyze local files (supports various formats)
- `analyze_url_with_notebooklm`: Analyze web pages or YouTube links

**Start Server (SSE Mode):**
```bash
uv run fastmcp run mcp_server.py --transport sse --port 8005
```

### 5. Running with Docker

You can also run the MCP server using Docker.

**Build the image:**
```bash
docker build -t gy-notebooklm-mcp .
```

**Run the container:**
You need to pass your authentication credentials. The easiest way is to mount your `storage_state.json` or pass the `NOTEBOOKLM_AUTH_JSON` environment variable.

> **Where to find `storage_state.json`?**
> After running `notebooklm login` locally, the file is usually located at:
> - **Windows**: `%LOCALAPPDATA%\notebooklm\storage_state.json`
> - **macOS / Linux**: `~/.notebooklm/storage_state.json`

Option A: Mount auth file (Recommended)
```bash
docker run -d -p 8005:8000 \
  --name gy-notebooklm-mcp \
  -v /path/to/your/storage_state.json:/app/storage_state.json \
  -e NOTEBOOKLM_AUTH_JSON="/app/storage_state.json" \
  gy-notebooklm-mcp
```
*Note: We map container port 8000 to host port 8005.*

Option B: Pass env var directly
```bash
docker run -d -p 8005:8000 \
  --name gy-notebooklm-mcp \
  -e NOTEBOOKLM_AUTH_JSON='{"cookies": ...}' \
  gy-notebooklm-mcp
```

**MCP Client Example:**
You can run `mcp_client.py` or `mcp_http_client.py` to test the connection and tool invocation.

## 📂 Project Structure

- `analyze_files.py`: General file analysis script (Core tool)
- `mcp_server.py`: MCP Server implementation
- `analyze_urls.py`: URL/YouTube batch analysis script
- `collect_urls.py`: YouTube playlist crawler
- `requirements.txt`: Project dependency list
- `analysis_reports/`: Output directory for analysis reports
