
import asyncio
import os
import argparse
from notebooklm import NotebookLMClient

async def analyze_file(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    file_name = os.path.basename(file_path)
    print(f"--- Processing File: {file_name} ---")

    print("\nConnecting to NotebookLM...")
    try:
        async with await NotebookLMClient.from_storage() as client:
            # 1. Create a new notebook
            nb_title = f"Analysis: {file_name}"
            print(f"Creating notebook: '{nb_title}'...")
            nb = await client.notebooks.create(nb_title)
            print(f"Notebook created: {nb.id}")

            # 2. Add File source
            print(f"Uploading File: {file_path}...")
            # Note: add_file handles local file upload (PDF, MP3, MP4, etc.)
            await client.sources.add_file(nb.id, file_path)
            
            # Wait for processing
            print("Waiting for NotebookLM to process the file (15s)...")
            await asyncio.sleep(15)

            # 3. Query
            # Using the optimized prompt for deep analysis
            query = (
                f"請針對這份檔案 ({file_name}) 進行深度分析，並以繁體中文與 Markdown 格式輸出詳細報告。內容應包含：\n"
                "1. **核心摘要**：這份檔案的主要內容目的與結論。\n"
                "2. **關鍵觀點與發現**：列出內容中最重要的數據、論點或洞察（Golden Nuggets）。\n"
                "3. **作者/講者立場**：分析作者或講者的觀點與潛在意圖。\n"
                "4. **問題與解決方案**：提到的主要挑戰及其對應解法。\n"
                "5. **行動建議**：基於內容，讀者接下來可以採取的具體行動。\n"
            )
            print(f"Querying analysis...")
            result = await client.chat.ask(nb.id, query)
            
            # 4. Save result
            output_file = f"{os.path.splitext(file_name)[0]}_analysis.md"
            with open(output_file, "w", encoding='utf-8') as f:
                f.write(f"# 檔案分析報告：{file_name}\n\n")
                f.write(f"**來源檔案**: {file_name}\n\n")
                f.write(result.answer)
                
            print(f"Saved report to: {output_file}")
            
            # 5. Cleanup
            print(f"Deleting temporary notebook: {nb.id}...")
            await client.notebooks.delete(nb.id)
            print("Notebook deleted.")
            
    except Exception as e:
        print(f"Error analyzing {file_name}: {e}")
        print("Tip: Ensure you have run 'notebooklm login' first.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a file (PDF, MP3, MP4, etc.) using NotebookLM.")
    parser.add_argument("file_path", help="Path to the file to analyze")
    args = parser.parse_args()

    asyncio.run(analyze_file(args.file_path))
