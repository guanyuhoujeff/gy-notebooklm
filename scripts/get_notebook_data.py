
import asyncio
import json
import os
from notebooklm import NotebookLMClient

async def get_all_notebook_data():
    all_data = []
    
    print("Connecting to NotebookLM...")
    async with await NotebookLMClient.from_storage() as client:
        print("Fetching notebooks...")
        notebooks = await client.notebooks.list()
        print(f"Found {len(notebooks)} notebooks.")
        
        for i, nb in enumerate(notebooks):
            print(f"Processing ({i+1}/{len(notebooks)}): {nb.title}")
            
            nb_data = {
                "notebook_title": nb.title,
                "notebook_id": nb.id,
                "sources": [],
                "notes": []
            }
            
            # Get Sources
            if hasattr(client, 'sources') and hasattr(client.sources, 'list'):
                try:
                    sources = await client.sources.list(nb.id)
                    nb_data["sources"] = []
                    for s in sources:
                        # Handle source kind/type safely
                        kind = "unknown"
                        if hasattr(s, 'kind'):
                            kind = str(s.kind)
                        elif hasattr(s, 'source_type'):
                            kind = str(s.source_type)
                            
                        nb_data["sources"].append({
                            "id": s.id,
                            "title": s.title,
                            "type": kind,
                            "url": getattr(s, 'url', None)
                        })
                except Exception as e:
                    print(f"  Error fetching sources for {nb.title}: {e}")

            # Get Notes
            if hasattr(client, 'notes') and hasattr(client.notes, 'list'):
                try:
                    notes = await client.notes.list(nb.id)
                    nb_data["notes"] = []
                    for n in notes:
                        nb_data["notes"].append({
                            "id": n.id,
                            "title": getattr(n, 'title', 'Untitled'),
                            "content": getattr(n, 'content', '')
                        })
                except Exception as e:
                    print(f"  Error fetching notes for {nb.title}: {e}")
            
            all_data.append(nb_data)
            
            # Print brief summary for this notebook
            print(f"  -> {len(nb_data['sources'])} sources, {len(nb_data['notes'])} notes")

    # Save to file
    output_file = "all_notebook_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved all data to {output_file}")
    
    # Also print all IDs to console for easy copy-pasting
    print("\n" + "="*50)
    print("ALL NOTE IDs FOUND")
    print("="*50)
    
    count = 0
    for nb in all_data:
        if nb['notes']:
            print(f"\nNotebook: {nb['notebook_title']} (ID: {nb['notebook_id']})")
            for note in nb['notes']:
                print(f"  - Note ID: {note['id']}")
                print(f"    Title: {note['title']}")
                print(f"    Content Preview: {note['content'][:50].replace(chr(10), ' ')}...")
                count += 1
                
    if count == 0:
        print("No user-created notes found in any notebook.")
        print("\n(Note: If you were looking for 'Source IDs' instead, check the 'all_notebook_data.json' file or the sources section)")
        
        # Optionally print sources if no notes found, just in case
        print("\n" + "="*50)
        print("ALL SOURCE IDs (Fallback)")
        print("="*50)
        for nb in all_data:
            if nb['sources']:
                print(f"\nNotebook: {nb['notebook_title']}")
                for s in nb['sources']:
                    print(f"  - Source ID: {s['id']} ({s['title']})")

if __name__ == "__main__":
    asyncio.run(get_all_notebook_data())
