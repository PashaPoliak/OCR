import os
import time
import logging
from pathlib import Path
from PIL import Image
import easyocr
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='image_watcher.log', filemode='a')

SERVER_URL = 'http://localhost:3000/api/text'
SERVER_URL = 'https://ocr-vh1p.onrender.com/api/text'

class ImageHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            filepath = event.src_path
            if Path(filepath).suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']:
                logging.info(f"New image detected: {filepath}")
                self.process_image(filepath)

    def process_image(self, filepath):
        try:
            # Initialize OCR reader (English)
            reader = easyocr.Reader(['en'])
            
            # Extract text using OCR
            results = reader.readtext(filepath)
            text = ' '.join([result[1] for result in results]).strip()
            
            if not text:
                logging.warning(f"No text extracted from {filepath}")
                return
            
            # Prepare JSON data
            json_data = {
                'filename': os.path.basename(filepath),
                'text': text
            }
            
            # Send to server
            response = requests.post(SERVER_URL, json=json_data, timeout=10)
            response.raise_for_status()
            logging.info(f"Successfully sent OCR data for {filepath} to server")

        except requests.RequestException as e:
            logging.error(f"Failed to send data to server: {e}")
        except Exception as e:
            logging.error(f"Error processing image {filepath}: {e}")

def process_existing_images(screenshots_path, process_func):
    logging.info("Processing existing images...")
    for file in screenshots_path.glob('*'):
        if file.is_file() and file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']:
            logging.info(f"Processing existing image: {file}")
            process_func(str(file))

def main():
    # Path to Screenshots folder
    screenshots_path = Path(os.environ['USERPROFILE']) / 'Pictures' / 'Screenshots'
    
    if not screenshots_path.exists():
        logging.error(f"Screenshots directory does not exist: {screenshots_path}")
        return
    
    event_handler = ImageHandler()
    observer = Observer()
    observer.schedule(event_handler, str(screenshots_path), recursive=False)
    
    logging.info(f"Starting to watch {screenshots_path} for new images...")
    observer.start()
    
    # Process any existing images
    process_existing_images(screenshots_path, event_handler.process_image)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Stopping image watcher...")

    observer.join()

if __name__ == "__main__":
    main()