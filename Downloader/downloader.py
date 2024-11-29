import requests
import os
import sys
import time
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_image(url, folder, progress, total, times=1):
    try:
        response = requests.get(url)
        response.raise_for_status()
        if len(response.content) < 5120:
            print_progress(progress, total, f"Skipped {url}: Image size is less than 5KB.")
            return
        filename = os.path.join(folder, os.path.basename(urlparse(url).path))
        with open(filename, 'wb') as f:
            f.write(response.content)
        print_progress(progress, total, f"Downloaded {url}")
    except requests.RequestException as e:
        if times<=3:
            time.sleep(1)
            download_image(url, folder, progress, total, times=times+1)
        else:
            with open("./Error.txt", 'a') as f:
                f.write(url+"\n")
            print_progress(progress, total, f"Error downloading {url}")
    except OSError as e:
        with open("./OSError.txt", 'a') as f:
            f.write(url+"\n")
        print_progress(progress, total, f"Error downloading {url}")

def print_progress(progress, total, message):
    print(f"Progress: {progress['count']}/{total} - {message}")

def download_images_from_file(file_path, max_threads=64):
    with open(file_path, 'r') as file:
        urls = [url.strip() for url in file.readlines()]
    folder = os.path.dirname(file_path)
    total = len(urls)
    progress = {'count': 0}
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(download_image, url, folder, progress, total): url for url in urls if url}
        for future in as_completed(futures):
            url = futures[future]
            try:
                future.result(timeout=120)
                progress['count'] += 1
            except TimeoutError:
                print(f"TimeoutError for URL: {url}")
            except Exception as e:
                print(f"Error downloading {url}: {e}")
    print(f"Downloaded {progress['count']} out of {total} images")

def process_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            print(f"Processing file: {file_path}")
            download_images_from_file(file_path)

if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print("Usage: python script.py <folder1> <folder2> ...")
        sys.exit(1)
    for folder_path in sys.argv[1:]:
        if os.path.isdir(folder_path):
            print(f"Processing folder: {folder_path}")
            process_folder(folder_path)
        else:
            print(f"{folder_path} is not a valid folder.")