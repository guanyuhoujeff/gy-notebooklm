
import sys
sys.path.append("/home/barai/.local/lib/python3.12/site-packages")

import os
import yt_dlp
import json

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLnaQkVsMNAvCFj1C7C_NJEimhvS1-DUVN"
URLS_FILE = "video_urls.json"

def collect_urls(playlist_url, limit=240):
    print(f"Collecting top {limit} video URLs from playlist: {playlist_url}")
    
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'playlist_items': f'1-240',
        'ignoreerrors': True,
    }
    
    video_data = []
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(playlist_url, download=False)
        if 'entries' in result:
            for entry in result['entries']:
                if entry:
                    video_data.append({
                        'title': entry.get('title'),
                        'url': entry.get('url') if entry.get('url') else f"https://www.youtube.com/watch?v={entry.get('id')}"
                    })
        
    print(f"Components found: {len(video_data)}")
    
    # Save to file
    with open(URLS_FILE, 'w', encoding='utf-8') as f:
        json.dump(video_data, f, indent=2, ensure_ascii=False)
        
    print(f"URLs saved to {URLS_FILE}")
    for i, v in enumerate(video_data[:5]): # Print first 5 as sample
        print(f" - [{i+1}] {v['title']}: {v['url']}")

if __name__ == "__main__":
    collect_urls(PLAYLIST_URL)
