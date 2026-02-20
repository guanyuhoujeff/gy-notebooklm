import asyncio
import os
from fastmcp import FastMCP
from notebooklm import NotebookLMClient

# 初始化 FastMCP 伺服器
mcp = FastMCP("NotebookLM Analyzer")

@mcp.tool()
async def analyze_pdf_with_notebooklm(pdf_path: str, custom_prompt: str = None) -> str:
    """
    使用 Google NotebookLM 深度分析本地的 PDF 檔案。
    
    Args:
        pdf_path: 本地 PDF 檔案的絕對路徑。
        custom_prompt: (可選) 自訂的分析指令。若未提供，將使用預設的深度分析指令。
    """
    if not os.path.exists(pdf_path):
        return f"錯誤：找不到檔案 {pdf_path}"

    prompt = custom_prompt or (
        "請針對這份文件進行深度分析，並以繁體中文與 Markdown 格式輸出詳細報告。內容應包含：\n"
        "1. **文件核心摘要**：這份文件的主要目的與結論。\n"
        "2. **關鍵觀點與發現**：列出文件中最重要的數據、論點或洞察（Golden Nuggets）。\n"
        "3. **作者立場與意圖**：分析作者或撰寫單位的觀點與潛在目標。\n"
        "4. **問題與解決方案**：文中提到的主要挑戰及其對應解法。\n"
        "5. **行動建議**：基於文件內容，讀者接下來可以採取的具體行動。\n"
    )
        
    try:
        async with await NotebookLMClient.from_storage() as client:
            pdf_name = os.path.basename(pdf_path)
            nb_title = f"MCP PDF Analysis: {pdf_name}"
            nb = await client.notebooks.create(nb_title)
            
            await client.sources.add_file(nb.id, pdf_path)
            await asyncio.sleep(10) # 等待 NotebookLM 處理檔案
            
            result = await client.chat.ask(nb.id, prompt)
            
            # 清理：分析完後刪除筆記本
            await client.notebooks.delete(nb.id)
            
            return result.answer
    except Exception as e:
        return f"分析 PDF 時發生錯誤: {e}\n請確認您已正確設定 notebooklm 的登入狀態。"

@mcp.tool()
async def analyze_url_with_notebooklm(url: str, title: str = "URL Analysis", custom_prompt: str = None) -> str:
    """
    使用 Google NotebookLM 深度分析網頁 URL 或 YouTube 影片連結。
    
    Args:
        url: 欲分析的目標網址 (支援 YouTube 影片)。
        title: (可選) 該網址的標題，用於建立暫存筆記本名稱。
        custom_prompt: (可選) 自訂的分析指令。若未提供，將使用預設的深度分析指令。
    """
    prompt = custom_prompt or (
        "請針對這個網頁或影片進行深度分析，並以繁體中文與 Markdown 格式輸出詳細報告。內容應包含：\n"
        "1. **講者個人想法**：分析講者/作者對主題的主觀看法、立場與態度。\n"
        "2. **關鍵重要觀念**：列出內容中強調的核心理念或獨特見解（Golden Nuggets）。\n"
        "3. **專案規劃與行動**：是否提到具體的專案、未來計畫或行動步驟？\n"
        "4. **問題與解決方案**：討論中提到的挑戰及其對應解法。\n"
        "5. **總結**：整部內容的精華摘要。"
    )
        
    try:
        async with await NotebookLMClient.from_storage() as client:
            nb_title = f"MCP URL Analysis: {title}"
            nb = await client.notebooks.create(nb_title)
            
            await client.sources.add_url(nb.id, url)
            await asyncio.sleep(5) # 等待 NotebookLM 處理 URL
            
            result = await client.chat.ask(nb.id, prompt)
            
            # 清理：分析完後刪除筆記本
            await client.notebooks.delete(nb.id)
            
            return result.answer
    except Exception as e:
        return f"分析 URL 時發生錯誤: {e}\n請確認您已正確設定 notebooklm 的登入狀態。"

if __name__ == "__main__":
    mcp.run()
