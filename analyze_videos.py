
import asyncio
import os
import glob
from notebooklm import NotebookLMClient

# Configuration
DOWNLOAD_DIR = "downloads"
NOTEBOOK_TITLE = "YouTube Playlist Analysis"

async def main():
    # Check for downloaded files
    audio_files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.mp3")) + \
                  glob.glob(os.path.join(DOWNLOAD_DIR, "*.m4a")) + \
                  glob.glob(os.path.join(DOWNLOAD_DIR, "*.webm")) # yt-dlp might download webm
    
    if not audio_files:
        print("No audio files found in downloads directory.")
        return

    print(f"Found {len(audio_files)} audio files to analyze.")
    for f in audio_files:
        print(f" - {os.path.basename(f)}")

    print("\nConnecting to NotebookLM...")
    try:
        async with await NotebookLMClient.from_storage() as client:
            # Create a new notebook
            print(f"Creating notebook: '{NOTEBOOK_TITLE}'...")
            nb = await client.notebooks.create(NOTEBOOK_TITLE)
            print(f"Notebook created with ID: {nb.id}")

            # Add sources
            for file_path in audio_files:
                print(f"Uploading source: {file_path}...")
                try:
                    await client.sources.add_file(nb.id, file_path)
                    print(f"Successfully added: {file_path}")
                except Exception as e:
                    print(f"Failed to add {file_path}: {e}")

            # Wait for processing? The library usually handles this or we might need to wait for ingestion.
            # NotebookLM implementation might take a moment to process audio.
            print("Waiting for sources to be processed (10 seconds)...")
            await asyncio.sleep(10)

            # Query the notebook
            queries = [
                "Summarize the key themes across these videos.",
                "What are the main takeaways from these discussions?",
                "Identify any common challenges or solutions mentioned."
            ]

            results = []
            for query in queries:
                print(f"\nQuerying: '{query}'...")
                result = await client.chat.ask(nb.id, query)
                print("Answer received.")
                results.append(f"## Query: {query}\n\n{result.answer}\n")

            # Save results
            output_file = "analysis_results.md"
            with open(output_file, "w") as f:
                f.write(f"# Analysis Results for {NOTEBOOK_TITLE}\n\n")
                for res in results:
                    f.write(res + "\n")
            
            print(f"\nAnalysis complete. Results saved to {output_file}")
            
    except Exception as e:
        print(f"\nError: {e}")
        print("Ensure you have authenticated with 'notebooklm login' or have a valid auth token.")

if __name__ == "__main__":
    asyncio.run(main())
