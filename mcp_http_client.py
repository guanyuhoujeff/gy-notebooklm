import asyncio
import sys

# 嘗試導入 MCP 相關模組
try:
    from mcp import ClientSession
    from mcp.client.sse import sse_client
except ImportError:
    print("錯誤: 找不到 'mcp' 模組。請確保已安裝 'mcp' 套件。")
    print("你可以執行: pip install mcp[sse]") # SSE 支援通常需要額外依賴
    sys.exit(1)

async def main():
    # 這裡假設你的 MCP Server 運行在 http://localhost:8000/sse
    # 你可以使用 fastmcp 命令來啟動 server: 
    # fastmcp run mcp_server.py --transport sse --port 8000
    sse_url = "http://localhost:52500/sse"

    print(f"正在連接 MCP SSE 伺服器: {sse_url} ...")

    try:
        # 建立 SSE 連線
        async with sse_client(sse_url) as (read, write):
            async with ClientSession(read, write) as session:
                # 初始化連線
                await session.initialize()
                
                # 列出可用工具
                print("\n--- 可用工具列表 ---")
                try:
                    tools = await session.list_tools()
                    for tool in tools.tools:
                        print(f"- {tool.name}: {tool.description}")
                except Exception as e:
                     print(f"列出工具時發生錯誤: {e}")
                     return

                # 範例 1：呼叫 analyze_url_with_notebooklm 工具
                print("\n--- 測試呼叫工具: analyze_url_with_notebooklm ---")
                
                tool_name = "analyze_url_with_notebooklm"
                tool_args = {
                    "url": "https://www.youtube.com/watch?v=jH5VjcapyC0",
                    "title": "Gemini Demo HTTP",
                    "custom_prompt": "請簡短摘要這段影片的重點 (繁體中文)"
                }

                # 範例 2 (可選)：呼叫 analyze_file_with_notebooklm 工具
                # tool_name = "analyze_file_with_notebooklm"
                # tool_args = {
                #     "file_path": "/path/to/your/file.pdf" # 或 .mp4, .mp3
                # }

                try:
                    print(f"正在透過 HTTP 呼叫 {tool_name}，請稍候...")
                    # 設定 timeout，因為分析可能需要較長時間
                    # 注意: ClientSession.call_tool 本身沒有簡單的 timeout 參數，
                    # 這裡依賴底層 transport 或 server 端的處理，
                    # 但我們可以 wrap 在 asyncio.wait_for 裡 (雖然這只會中斷 client 等待)
                    result = await session.call_tool(tool_name, tool_args)
                    
                    print("工具執行成功！結果如下：")
                    print("-" * 20)
                    for content in result.content:
                        if content.type == 'text':
                            print(content.text)
                        else:
                            print(f"[{content.type} content]")
                    print("-" * 20)

                except Exception as e:
                    print(f"呼叫工具時發生錯誤: {e}")

    except ConnectionRefusedError:
        print(f"\n錯誤: 無法連接到 {sse_url}")
        print("請確認伺服器是否已啟動，指令範例：")
        print("fastmcp run mcp_server.py --transport sse --port 8000")
    except Exception as e:
        print(f"\n發生未預期的錯誤: {e}")

if __name__ == "__main__":
    # Windows 平台上 asyncio 的事件循環策略調整
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main())
