
import asyncio
import os
import json
import re
from notebooklm import NotebookLMClient

# Configuration
URLS_FILE = "video_urls.json"
OUTPUT_DIR = "analysis_reports2"

def sanitize_filename(name):
    """Sanitize filename to be safe for file systems."""
    return re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")

async def analyze_single_video(client, video):
    title = video['title']
    url = video['url']
    safe_title = sanitize_filename(title)
    output_file = os.path.join(OUTPUT_DIR, f"{safe_title}_analysis_result.md")
    
    if os.path.exists(output_file):
        print(f"Skipping {title} (Report already exists)")
        return

    print(f"--- Processing: {title} ---")
    
    try:
        # Create a new notebook for this SPECIFIC video
        nb_title = f"Analysis: {title}"
        print(f"Creating notebook: '{nb_title}'...")
        nb = await client.notebooks.create(nb_title)

        # Add source
        print(f"Adding source: {url}...")
        await client.sources.add_url(nb.id, url)
        
        # Wait for processing
        print("Waiting for source processing (5s)...")
        await asyncio.sleep(5)

        # Query
        query = (
            "請針對這部影片進行深度分析，並以繁體中文與 Markdown 格式輸出詳細報告。內容應包含：\n"
            "1. **講者個人想法**：分析講者對主題的主觀看法、立場與態度。\n"
            "2. **關鍵重要觀念**：列出講者強調的核心理念或獨特見解（Golden Nuggets）。\n"
            "3. **專案規劃與行動**：講者是否提到具體的專案、未來計畫或行動步驟？\n"
            "4. **問題與解決方案**：討論中提到的挑戰及其對應解法。\n"
            "5. **總結**：整部影片的精華摘要。"
            "6. **其他**：是否有提到講者參考甚麼youtube影片或是其他教學資源。"
        )
        print(f"Querying analysis...")
        result = await client.chat.ask(nb.id, query)
        
        # Save result
        with open(output_file, "w", encoding='utf-8') as f:
            f.write(f"# 分析報告：{title}\n\n")
            f.write(f"**來源影片**: [{title}]({url})\n\n")
            f.write(result.answer)
            
        print(f"Saved report to: {output_file}")
        
        # Cleanup: Delete notebook
        print(f"Deleting temporary notebook: {nb.id}...")
        await client.notebooks.delete(nb.id)
        print("Notebook deleted.")
        
    except Exception as e:
        print(f"Error analyzing {title}: {e}")

async def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    if not os.path.exists(URLS_FILE):
        print(f"URLs file not found: {URLS_FILE}")
        return

    with open(URLS_FILE, 'r', encoding='utf-8') as f:
        video_data = json.load(f)
    
    if not video_data:
        print("No URLs found to analyze.")
        return

    print(f"Found {len(video_data)} videos to analyze individually.")

    print("\nConnecting to NotebookLM...")
    async with await NotebookLMClient.from_storage() as client:
        # Process videos one by one (or in small batches if needed)
        for i, video in enumerate(video_data):
            print(f"\n[{i+1}/{len(video_data)}]")
            await analyze_single_video(client, video)
            if i < len(video_data) - 1:
                print("Cooling down (2s)...")
                await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
