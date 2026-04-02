import urllib.request
import sys

def download_with_prompt(url: str, dest_path: str, what: str, why: str) -> bool:
    print(f"\n--- DOWNLOAD REQUIRED ---")
    print(f"Downloading: {what}")
    print(f"Reason: {why}")
    print(f"URL: {url}")
    print("\n! DISCLAIMER: We are not responsible for the contents, safety, or any potential damage caused by this software. Use at your own risk.")
    
    while True:
        choice = input("\nDo you agree to download and run this file? (y/yes to agree, n/no to decline): ").strip().lower()
        if choice in['y', 'yes']:
            break
        elif choice in ['n', 'no']:
            print("Download declined by user. Operation cancelled.")
            return False
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
            
    print(f"Starting download...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            total_length = response.info().get('Content-Length')
            total_size = int(total_length) if total_length else 0
            downloaded = 0
            block_size = 8192
            
            with open(dest_path, 'wb') as f:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    f.write(buffer)
                    downloaded += len(buffer)
                    if total_size:
                        percent = (downloaded / total_size) * 100
                        bar_length = 40
                        filled = int(bar_length * downloaded / total_size)
                        bar = '#' * filled + '-' * (bar_length - filled)
                        sys.stdout.write(f"\r[{bar}] {percent:.1f}% ({downloaded}/{total_size} bytes)")
                        sys.stdout.flush()
                    else:
                        sys.stdout.write(f"\rDownloaded {downloaded} bytes...")
                        sys.stdout.flush()
        print("\nDownload complete!\n")
        return True
    except Exception as e:
        print(f"\nError during download: {e}\n")
        return False