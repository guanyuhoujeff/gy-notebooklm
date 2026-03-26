import os
import asyncio
import logging
import tempfile
import urllib.request
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, ConfigDict
from notebooklm import NotebookLMClient
import uvicorn

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

SESSION_TTL_SECONDS = 7200       # 2 hours
CLEANUP_INTERVAL_SECONDS = 300   # check every 5 minutes


@dataclass
class ChatSession:
    session_id: str
    notebook_id: str
    title: str
    source_type: str
    created_at: datetime
    conversation_id: str | None = None
    turn_count: int = 0
    turns: list[dict] = field(default_factory=list)


_sessions: dict[str, ChatSession] = {}


async def _cleanup_expired_sessions():
    """Background task: delete sessions older than SESSION_TTL_SECONDS."""
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        now = datetime.now(timezone.utc)
        expired = [
            sid for sid, s in _sessions.items()
            if (now - s.created_at).total_seconds() > SESSION_TTL_SECONDS
        ]
        for sid in expired:
            try:
                async with await NotebookLMClient.from_storage() as client:
                    await client.notebooks.delete(_sessions[sid].notebook_id)
            except Exception as e:
                logger.warning("Failed to cleanup session %s: %s", sid, e)
            _sessions.pop(sid, None)
        if expired:
            logger.info("Cleaned up %d expired session(s)", len(expired))


@asynccontextmanager
async def lifespan(_app):
    task = asyncio.create_task(_cleanup_expired_sessions())
    yield
    task.cancel()


# ---------------------------------------------------------------------------
# App & Pydantic models
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NotebookLM API Server",
    description="REST API for analyzing files and URLs with Google NotebookLM",
    lifespan=lifespan,
)


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


class CreateSessionFromUrlRequest(BaseModel):
    url: str
    title: str = "Chat Session"


class AskRequest(BaseModel):
    question: str


class SessionInfoResponse(BaseModel):
    session_id: str
    notebook_id: str
    title: str
    source_type: str
    created_at: str
    turn_count: int


class AskResponse(BaseModel):
    status: str = "success"
    answer: str
    conversation_id: str
    turn_number: int
    is_follow_up: bool


def _session_to_info(s: ChatSession) -> dict:
    return {
        "session_id": s.session_id,
        "notebook_id": s.notebook_id,
        "title": s.title,
        "source_type": s.source_type,
        "created_at": s.created_at.isoformat(),
        "turn_count": s.turn_count,
    }


def _get_session(session_id: str) -> ChatSession:
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} 不存在")
    return session


# ---------------------------------------------------------------------------
# Existing analyze endpoints (unchanged)
# ---------------------------------------------------------------------------

@app.post("/analyze/remote-file")
async def analyze_remote_file(request: AnalyzeFileRequest):
    """
    透過 HTTP URL 下載檔案並使用 Google NotebookLM 深度分析。
    """
    parsed_url = urlparse(request.file_url)
    file_name = os.path.basename(parsed_url.path)
    if not file_name or "." not in file_name:
        file_name = "downloaded_file.pdf"

    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, file_name)

    try:
        await asyncio.to_thread(urllib.request.urlretrieve, request.file_url, temp_file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"下載遠端檔案時發生錯誤 {e}")

    prompt = request.custom_prompt or (
        f"請針對這份檔案 ({file_name}) 進行深度分析，並以繁體中文與 Markdown 格式輸出詳細報告。內容應包含：\n"
        "1. **核心摘要**：這份檔案的主要內容目的與結論。\n"
        "2. **關鍵觀點與發現**：列出內容中最重要的數據、論點或洞察（Golden Nuggets）。\n"
        "3. **作者/講者立場**：分析作者或講者的觀點與潛在意圖。\n"
        "4. **問題與解決方案**：提到的主要挑戰及其對應解法。\n"
        "5. **行動建議**：基於內容，讀者接下來可以採取的具體行動。\n"
    )

    try:
        async with await NotebookLMClient.from_storage() as client:
            nb_title = f"API Remote File: {file_name}"
            nb = await client.notebooks.create(nb_title)

            await client.sources.add_file(nb.id, temp_file_path)
            await asyncio.sleep(15)

            result = await client.chat.ask(nb.id, prompt)
            await client.notebooks.delete(nb.id)

            return {"status": "success", "result": result.answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析檔案時發生錯誤: {e}\n請確認您已正確設定 notebooklm 的登入狀態。")
    finally:
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
            nb = await client.notebooks.create(nb_title)

            source = await client.sources.add_file(
                nb.id,
                temp_file_path,
                wait=True,
                wait_timeout=120.0,
            )
            result = await client.chat.ask(nb.id, prompt)
            await client.notebooks.delete(nb.id)

            return {"status": "success", "result": result.answer}
    except Exception as e:
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
            await asyncio.sleep(5)

            result = await client.chat.ask(nb.id, prompt)
            await client.notebooks.delete(nb.id)

            return {"status": "success", "result": result.answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析 URL 時發生錯誤: {e}\n請確認您已正確設定 notebooklm 的登入狀態。")


# ---------------------------------------------------------------------------
# Chat session endpoints
# ---------------------------------------------------------------------------

@app.post("/chat/sessions")
async def create_chat_session_upload(
    file: UploadFile = File(...),
    title: str = Form(None),
):
    """上傳檔案並建立對話 session，之後可透過 /chat/sessions/{id}/ask 多輪提問。"""
    file_name = file.filename
    if not file_name or "." not in file_name:
        file_name = "uploaded_file.pdf"

    session_title = title or file_name

    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, file_name)

    try:
        content = await file.read()
        with open(temp_file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"儲存上傳檔案時發生錯誤: {e}")

    try:
        async with await NotebookLMClient.from_storage() as client:
            nb = await client.notebooks.create(f"Chat: {session_title}")
            await client.sources.add_file(
                nb.id,
                temp_file_path,
                wait=True,
                wait_timeout=120.0,
            )

        session_id = str(uuid.uuid4())
        session = ChatSession(
            session_id=session_id,
            notebook_id=nb.id,
            title=session_title,
            source_type="file_upload",
            created_at=datetime.now(timezone.utc),
        )
        _sessions[session_id] = session

        return {"status": "success", "session": _session_to_info(session)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立 session 時發生錯誤: {e}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.post("/chat/sessions/url")
async def create_chat_session_url(request: CreateSessionFromUrlRequest):
    """透過 URL（網頁或 YouTube）建立對話 session。"""
    try:
        async with await NotebookLMClient.from_storage() as client:
            nb = await client.notebooks.create(f"Chat: {request.title}")
            await client.sources.add_url(nb.id, request.url)
            await asyncio.sleep(5)

        session_id = str(uuid.uuid4())
        session = ChatSession(
            session_id=session_id,
            notebook_id=nb.id,
            title=request.title,
            source_type="url",
            created_at=datetime.now(timezone.utc),
        )
        _sessions[session_id] = session

        return {"status": "success", "session": _session_to_info(session)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立 session 時發生錯誤: {e}")


@app.post("/chat/sessions/{session_id}/ask")
async def chat_ask(session_id: str, request: AskRequest):
    """在指定 session 中提問，支援多輪對話。"""
    session = _get_session(session_id)

    try:
        async with await NotebookLMClient.from_storage() as client:
            # Populate client-side conversation cache for follow-ups
            if session.conversation_id and session.turns:
                for turn in session.turns:
                    client._core.cache_conversation_turn(
                        session.conversation_id,
                        turn["query"],
                        turn["answer"],
                        turn["turn_number"],
                    )

            result = await client.chat.ask(
                session.notebook_id,
                request.question,
                conversation_id=session.conversation_id,
            )

        session.conversation_id = result.conversation_id
        session.turn_count = result.turn_number
        session.turns.append({
            "query": request.question,
            "answer": result.answer,
            "turn_number": result.turn_number,
        })

        return AskResponse(
            answer=result.answer,
            conversation_id=result.conversation_id,
            turn_number=result.turn_number,
            is_follow_up=result.is_follow_up,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提問時發生錯誤: {e}")


@app.get("/chat/sessions")
async def list_chat_sessions():
    """列出所有 active sessions。"""
    return {
        "status": "success",
        "sessions": [_session_to_info(s) for s in _sessions.values()],
    }


@app.get("/chat/sessions/{session_id}")
async def get_chat_session(session_id: str):
    """查看指定 session 的資訊。"""
    session = _get_session(session_id)
    return {"status": "success", "session": _session_to_info(session)}


@app.delete("/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """結束對話 session 並刪除對應的 NotebookLM 筆記本。"""
    session = _get_session(session_id)

    try:
        async with await NotebookLMClient.from_storage() as client:
            await client.notebooks.delete(session.notebook_id)
    except Exception as e:
        logger.warning("Failed to delete notebook %s: %s", session.notebook_id, e)

    _sessions.pop(session_id, None)
    return {"status": "success", "message": f"Session {session_id} 已刪除"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("fastapi_server:app", host="0.0.0.0", port=52501, reload=True)
