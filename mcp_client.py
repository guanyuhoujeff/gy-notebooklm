import asyncio
import os
import sys

# 嘗試導入 MCP 相關模組
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("錯誤: 找不到 'mcp' 模組。請確保已安裝 'mcp' 套件。")
    print("你可以執行: pip install mcp")
    sys.exit(1)

# 設定伺服器參數
# 這裡假設 mcp_server.py 在同一目錄下，並且是用 python 執行的
server_params = StdioServerParameters(
    command=sys.executable, # 使用當前 python 解釋器
    args=["mcp_server.py"], # 執行伺服器腳本
    env=os.environ.copy() # 傳遞環境變數 (例如 API keys)
)

async def main():
    print("正在連接 MCP 伺服器...")
    
    # 建立與 MCP 伺服器的 stdio 連線
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化連線
            await session.initialize()
            
            # 列出可用工具
            print("\n--- 可用工具列表 ---")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            # 範例 1：呼叫 analyze_url_with_notebooklm 工具
            # 請確保你的 NotebookLMClient 已正確配置 (例如 auth token)
            print("\n--- 測試呼叫工具: analyze_url_with_notebooklm ---")
            
            # 使用一個公開的技術影片作為範例
            tool_name = "analyze_url_with_notebooklm"
            tool_args = {
                "url": "https://www.youtube.com/watch?v=jH5VjcapyC0", # Google DeepMind Gemini 介紹影片
                "title": "Gemini Demo",
                "custom_prompt": "請簡短摘要這段影片的重點 (繁體中文)"
            }

            # 範例 2 (可選)：呼叫 analyze_file_with_notebooklm 工具
            # tool_name = "analyze_file_with_notebooklm"
            # tool_args = {
            #     "file_path": "/path/to/your/file.pdf" # 或 .mp4, .mp3
            # }

            try:
                # 呼叫工具
                print(f"正在呼叫 {tool_name}，請稍候...")
                result = await session.call_tool(tool_name, tool_args)
                
                # 顯示結果
                print("工具執行成功！結果如下：")
                print("-" * 20)
                # result.content 是一個 list，通常包含 TextContent
                for content in result.content:
                    if content.type == 'text':
                        print(content.text)
                    else:
                        print(f"[{content.type} content]")
                print("-" * 20)

            except Exception as e:
                print(f"呼叫工具時發生錯誤: {e}")

if __name__ == "__main__":
    # Windows 平台上 asyncio 的事件循環策略調整 (如果有的話)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main())
