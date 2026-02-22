import os
import asyncio
import tempfile
import urllib.request
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, ConfigDict
from notebooklm import NotebookLMClient
import uvicorn

app = FastAPI(title="NotebookLM API Server", description="REST API for analyzing files and URLs with Google NotebookLM")

class AnalyzeFileRequest(BaseModel):
    file_url: str
    custom_prompt: str = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_url": "https://example.com/sample.pdf",
                "custom_prompt": "請給我這份文件的三點核心摘要"
            }
        }
    )

class AnalyzeUrlRequest(BaseModel):
    url: str
    title: str = "URL Analysis"
    custom_prompt: str = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "title": "Rick Astley Video",
                "custom_prompt": "請分析這部影片的內容"
            }
        }
    )

@app.post("/analyze/remote-file")
async def analyze_remote_file(request: AnalyzeFileRequest):
    """
    透過 HTTP URL 下載檔案並使用 Google NotebookLM 深度分析。
    """
    # 1. 準備暫存檔路徑
    parsed_url = urlparse(request.file_url)
    file_name = os.path.basename(parsed_url.path)
    if not file_name or "." not in file_name:
        file_name = "downloaded_file.pdf" # 給個預設名稱
        
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, file_name)
    
    # 2. 下載檔案 (使用 asyncio.to_thread 防止下載過程阻塞 Server 的非同步迴圈)
    try:
        await asyncio.to_thread(urllib.request.urlretrieve, request.file_url, temp_file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"下載遠端檔案時發生錯誤 {e}")

    # 3. 準備 Prompt 分析文字
    prompt = request.custom_prompt or (
        f"請針對這份檔案 ({file_name}) 進行深度分析，並以繁體中文與 Markdown 格式輸出詳細報告。內容應包含：\n"
        "1. **核心摘要**：這份檔案的主要內容目的與結論。\n"
        "2. **關鍵觀點與發現**：列出內容中最重要的數據、論點或洞察（Golden Nuggets）。\n"
        "3. **作者/講者立場**：分析作者或講者的觀點與潛在意圖。\n"
        "4. **問題與解決方案**：提到的主要挑戰及其對應解法。\n"
        "5. **行動建議**：基於內容，讀者接下來可以採取的具體行動。\n"
    )
        
    # 4. 上傳至 NotebookLM 並執行分析流程
    try:
        async with await NotebookLMClient.from_storage() as client:
            nb_title = f"API Remote File: {file_name}"
            nb = await client.notebooks.create(nb_title)
            
            # 使用我們下載下來的「暫存檔路徑」上傳給 NotebookLM
            await client.sources.add_file(nb.id, temp_file_path)
            await asyncio.sleep(15) # 等待 NotebookLM 處理檔案
            
            result = await client.chat.ask(nb.id, prompt)
            
            # 清理：分析完後刪除筆記本
            await client.notebooks.delete(nb.id)
            
            return {"status": "success", "result": result.answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析檔案時發生錯誤: {e}\n請確認您已正確設定 notebooklm 的登入狀態。")
    finally:
        # 5. 無論成功或失敗，一定要刪除 Server 上的這份暫存檔，避免塞爆硬碟
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/analyze/upload")
async def analyze_uploaded_file(file: UploadFile = File(...), custom_prompt: str = Form(None)):
    """
    上傳本地檔案並使用 Google NotebookLM 深度分析。
    """
    file_name = file.filename
    if not file_name or "." not in file_name:
        file_name = "uploaded_file.pdf"
        
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, file_name)
    
    try:
        content = await file.read()
        with open(temp_file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"儲存上傳檔案時發生錯誤 {e}")

    prompt = custom_prompt or (
        f"請針對這份檔案 ({file_name}) 進行深度分析，並以繁體中文與 Markdown 格式輸出詳細報告。內容應包含：\n"
        "1. **核心摘要**：這份檔案的主要內容目的與結論。\n"
        "2. **關鍵觀點與發現**：列出內容中最重要的數據、論點或洞察（Golden Nuggets）。\n"
        "3. **作者/講者立場**：分析作者或講者的觀點與潛在意圖。\n"
        "4. **問題與解決方案**：提到的主要挑戰及其對應解法。\n"
        "5. **行動建議**：基於內容，讀者接下來可以採取的具體行動。\n"
    )
        
    try:
        async with await NotebookLMClient.from_storage() as client:
            nb_title = f"API Uploaded File: {file_name}"
            print(f"Creating notebook: '{nb_title}'...")
            nb = await client.notebooks.create(nb_title)
            
            source = await client.sources.add_file(
                nb.id, 
                temp_file_path,
                wait=True,             # 設定為 True 以等待上傳與處理完畢
                wait_timeout=120.0     # 可選：預設 120 秒超時，您可以自行延長
            )
            if source.is_ready:
                # print("檔案已上傳且處理完畢！")
                pass
            else:
                # print("檔案上傳失敗或超時！")
                # await asyncio.sleep(15) 
                pass
            # print(f"Querying analysis...")
            result = await client.chat.ask(nb.id, prompt)
            # print(f"Analysis result: {result.answer}")
            await client.notebooks.delete(nb.id)
            
            return {"status": "success", "result": result.answer}
    except Exception as e:
        print(f"分析檔案時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"分析檔案時發生錯誤: {e}\n請確認您已正確設定 notebooklm 的登入狀態。")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/analyze/url")
async def analyze_url(request: AnalyzeUrlRequest):
    """
    使用 Google NotebookLM 深度分析網頁 URL 或 YouTube 影片連結。
    """
    prompt = request.custom_prompt or (
        "請針對這個網頁或影片進行深度分析，並以繁體中文與 Markdown 格式輸出詳細報告。內容應包含：\n"
        "1. **講者個人想法**：分析講者/作者對主題的主觀看法、立場與態度。\n"
        "2. **關鍵重要觀念**：列出內容中強調的核心理念或獨特見解（Golden Nuggets）。\n"
        "3. **專案規劃與行動**：是否提到具體的專案、未來計畫或行動步驟？\n"
        "4. **問題與解決方案**：討論中提到的挑戰及其對應解法。\n"
        "5. **總結**：整部內容的精華摘要。"
    )
        
    try:
        async with await NotebookLMClient.from_storage() as client:
            nb_title = f"API URL Analysis: {request.title}"
            nb = await client.notebooks.create(nb_title)
            
            await client.sources.add_url(nb.id, request.url)
            await asyncio.sleep(5) # 等待 NotebookLM 處理 URL
            
            result = await client.chat.ask(nb.id, prompt)
            
            # 清理：分析完後刪除筆記本
            await client.notebooks.delete(nb.id)
            
            return {"status": "success", "result": result.answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析 URL 時發生錯誤: {e}\n請確認您已正確設定 notebooklm 的登入狀態。")

if __name__ == "__main__":
    uvicorn.run("fastapi_server:app", host="0.0.0.0", port=52501, reload=True)
