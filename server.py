from flask import Flask, request, jsonify, render_template_string
import os
from datetime import datetime
import pytesseract
from PIL import Image
import io

app = Flask(__name__)
STORAGE_DIR = 'extracted_texts'
os.makedirs(STORAGE_DIR, exist_ok=True)

@app.route('/api/text', methods=['POST'])
def receive_text():
    try:
        data = request.get_json()
        if not data or 'filename' not in data or 'text' not in data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        filename = data['filename']
        text = data['text']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(STORAGE_DIR, f"{timestamp}_{filename}.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Filename: {filename}\nTimestamp: {datetime.now()}\nText:\n{text}\n")
        
        return jsonify({'status': 'success', 'file': output_file})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/image', methods=['POST'])
def receive_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
            
        file = request.files['image']
        
        # Process OCR in-memory to save I/O and disk space
        img = Image.open(file.stream)
        text = pytesseract.image_to_string(img).strip()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(STORAGE_DIR, f"{timestamp}_capture.jpg.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Filename: capture.jpg\nTimestamp: {datetime.now()}\nText:\n{text}\n")
            
        return jsonify({'status': 'success', 'text': text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/text', methods=['GET'])
def get_texts():
    try:
        texts = []
        if os.path.exists(STORAGE_DIR):
            for file in sorted(os.listdir(STORAGE_DIR), reverse=True):
                if file.endswith('.txt'):
                    filepath = os.path.join(STORAGE_DIR, file)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read().split('\n')
                        texts.append({'id': file, 'text': '\n'.join(content[3:]).strip()})
        return jsonify({'texts': texts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/text/<path:file_id>', methods=['DELETE'])
def delete_text(file_id):
    try:
        filepath = os.path.join(STORAGE_DIR, file_id)
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'status': 'success'})
        return jsonify({'error': 'Not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def camera():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body, html { width: 100%; height: 100%; overflow: hidden; background: #000; }
        video { width: 100vw; height: 100vh; object-fit: cover; }
        .shutter {
            position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%);
            width: 70px; height: 70px; background: white; border-radius: 50%; border: none;
        }
    </style>
</head>
<body>
    <video id="video" autoplay playsinline></video>
    <button class="shutter" onclick="takePhoto()"></button>
    <canvas id="canvas" style="display:none;"></canvas>
    <script>
        const video = document.getElementById('video');
        async function start() {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { 
                    facingMode: 'environment',
                    width: { ideal: window.innerWidth },
                    height: { ideal: window.innerHeight }
                }
            });
            video.srcObject = stream;
        }
        async function takePhoto() {
            const canvas = document.getElementById('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            
            canvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('image', blob, 'photo.jpg');
                await fetch('/api/image', { method: 'POST', body: formData });
            }, 'image/jpeg', 0.8);
        }
        start();
    </script>
</body>
</html>
''')

@app.route('/quiz')
def quiz():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; background: #f5f5f5; padding: 15px; margin: 0; }
        .text-item { 
            border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; 
            background: white; white-space: pre-wrap; word-break: break-all;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div id="texts-container"></div>
    <script>
        async function load() {
            const res = await fetch('/api/text');
            const data = await res.json();
            document.getElementById('texts-container').innerHTML = data.texts.map(t => 
                `<div class="text-item" onclick="cutText(this, '${t.id}')">${t.text}</div>`
            ).join('');
        }
        async function cutText(el, id) {
            await navigator.clipboard.writeText(el.textContent);
            await fetch(`/api/text/${id}`, { method: 'DELETE' });
            el.remove();
        }
        load();
        setInterval(load, 2000);
    </script>
</body>
</html>
''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
