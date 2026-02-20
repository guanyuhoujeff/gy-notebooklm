
import asyncio
import os
import argparse
from notebooklm import NotebookLMClient

async def analyze_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    pdf_name = os.path.basename(pdf_path)
    print(f"--- Processing PDF: {pdf_name} ---")

    print("\nConnecting to NotebookLM...")
    try:
        async with await NotebookLMClient.from_storage() as client:
            # 1. Create a new notebook
            nb_title = f"Analysis: {pdf_name}"
            print(f"Creating notebook: '{nb_title}'...")
            nb = await client.notebooks.create(nb_title)
            print(f"Notebook created: {nb.id}")

            # 2. Add PDF source
            print(f"Uploading PDF: {pdf_path}...")
            # Note: add_file handles local file upload
            await client.sources.add_file(nb.id, pdf_path)
            
            # Wait for processing
            print("Waiting for NotebookLM to process the file (10s)...")
            await asyncio.sleep(10)

            # 3. Query
            # Using the optimized prompt for deep analysis
            query = (
                "請針對這份文件進行深度分析，並以繁體中文與 Markdown 格式輸出詳細報告。內容應包含：\n"
                "1. **文件核心摘要**：這份文件的主要目的與結論。\n"
                "2. **關鍵觀點與發現**：列出文件中最重要的數據、論點或洞察（Golden Nuggets）。\n"
                "3. **作者立場與意圖**：分析作者或撰寫單位的觀點與潛在目標。\n"
                "4. **問題與解決方案**：文中提到的主要挑戰及其對應解法。\n"
                "5. **行動建議**：基於文件內容，讀者接下來可以採取的具體行動。\n"
            )
            print(f"Querying analysis...")
            result = await client.chat.ask(nb.id, query)
            
            # 4. Save result
            output_file = f"{os.path.splitext(pdf_name)[0]}_analysis.md"
            with open(output_file, "w", encoding='utf-8') as f:
                f.write(f"# 文件分析報告：{pdf_name}\n\n")
                f.write(f"**來源檔案**: {pdf_name}\n\n")
                f.write(result.answer)
                
            print(f"Saved report to: {output_file}")
            
            # 5. Cleanup
            print(f"Deleting temporary notebook: {nb.id}...")
            await client.notebooks.delete(nb.id)
            print("Notebook deleted.")
            
    except Exception as e:
        print(f"Error analyzing {pdf_name}: {e}")
        print("Tip: Ensure you have run 'notebooklm login' first.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a PDF file using NotebookLM.")
    parser.add_argument("pdf_path", help="Path to the PDF file to analyze")
    args = parser.parse_args()

    asyncio.run(analyze_pdf(args.pdf_path))
