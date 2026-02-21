import requests
import argparse
import os

API_URL = "http://localhost:52501"

def analyze_local_file_via_api(file_path: str, custom_prompt: str = None):
    """
    將本地檔案上傳給 FastAPI Server 進行分析。
    使用 multipart/form-data 格式。
    """
    if not os.path.exists(file_path):
        print(f"錯誤：找不到檔案 {file_path}")
        return

    url = f"{API_URL}/analyze/upload"
    
    print(f"=====================================")
    print(f"上傳檔案中: {file_path}")
    print(f"API 端點: {url}")
    print(f"這可能需要 15-30 秒的時間，請稍候...")
    
    # 準備表單資料
    files = {"file": open(file_path, "rb")}
    data = {}
    if custom_prompt:
        data["custom_prompt"] = custom_prompt
        
    try:
        response = requests.post(url, files=files, data=data)
        response.raise_for_status() # 檢查 HTTP 錯誤
        
        result = response.json()
        print("\n✅ 分析完成！")
        print("=====================================\n")
        print(result.get("result", "找不到分析結果。"))
        
    except requests.exceptions.HTTPError as err:
        print(f"\n❌ API 錯誤: {err}")
        try:
            print(f"詳細錯誤訊息: {response.json()}")
        except:
            pass
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 連線錯誤：無法連線至 {API_URL}。請確保 FastAPI 伺服器已啟動。")
    except Exception as e:
        print(f"\n❌ 發生未知的錯誤: {e}")
    finally:
        files["file"].close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FastAPI NotebookLM 分析客戶端 (支援檔案上傳)")
    parser.add_argument("file_path", help="要分析的本地檔案路徑 (例如: doc.pdf, video.mp4)")
    parser.add_argument("--prompt", "-p", help="自訂分析指令 (選填)", default=None)
    
    args = parser.parse_args()
    
    analyze_local_file_via_api(args.file_path, args.prompt)
