from flask import Flask, request, jsonify, render_template_string
import logging
import os
from datetime import datetime

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/api/text', methods=['POST'])
def receive_text():
    try:
        data = request.get_json()
        if not data or 'filename' not in data or 'text' not in data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        filename = data['filename']
        text = data['text']
        
        logging.info(f"Received text from {filename}: {text[:100]}...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"extracted_texts/{timestamp}_{filename}.txt"
        os.makedirs('extracted_texts', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Filename: {filename}\n")
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write(f"Text:\n{text}\n")
        
        logging.info(f"Saved text to {output_file}")
        
        return jsonify({'status': 'success', 'file': output_file})
    
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/texts', methods=['GET'])
def get_texts():
    try:
        texts_dir = 'extracted_texts'
        if not os.path.exists(texts_dir):
            return jsonify({'texts': []})
        
        texts = []
        for file in sorted(os.listdir(texts_dir), reverse=True):  # Most recent first
            if file.endswith('.txt'):
                filepath = os.path.join(texts_dir, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    text_content = '\n'.join(lines[3:]) if len(lines) > 3 else ''
                    texts.append({'id': file, 'text': text_content.strip()})
        
        return jsonify({'texts': texts})
    
    except Exception as e:
        logging.error(f"Error retrieving texts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/text/<path:file_id>', methods=['DELETE'])
def delete_text(file_id):
    try:
        filepath = os.path.join('extracted_texts', file_id)
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'status': 'success'})
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logging.error(f"Error deleting text: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    html = '''
<!DOCTYPE html>
<html>
<head>
    <title>OCR Texts</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .text-item { 
            border: 1px solid #ddd; 
            padding: 15px; 
            margin: 15px 0; 
            white-space: pre-wrap; 
            position: relative; 
            background: white;
            border-radius: 8px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .text-item:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .text-item.removing {
            animation: fadeOut 0.5s forwards;
        }
        @keyframes fadeOut {
            to { opacity: 0; transform: scale(0.95); }
        }
        .text-item .actions { position: absolute; top: 10px; right: 10px; display: flex; gap: 5px; }
        .text-item .actions button { 
            padding: 6px 12px; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 12px;
            transition: all 0.2s ease;
            background: #e0e0e0;
        }
        .text-item .actions button:hover { 
            transform: scale(1.05);
        }
        .text-item .actions button.copy-btn { background: #4caf50; color: white; }
        .text-item .actions button.cut-btn { background: #ff9800; color: white; }
        .text-item .actions button.delete-btn { background: #f44336; color: white; }
        .text-item .actions button.copied { 
            background: #2196f3; 
            animation: pulse 0.5s;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        .loading { color: #666; }
    </style>
</head>
<body>
    <div id="texts-container"></div>
    <script>
        async function fetchTexts() {
            try {
                const response = await fetch('/api/texts');
                const data = await response.json();
                const container = document.getElementById('texts-container');
                
                if (data.texts && data.texts.length > 0) {
                    container.innerHTML = data.texts.map(item => 
                        `<div class="text-item" data-id="${item.id}">${item.text}<div class="actions"><button class="copy-btn" onclick="copyText(this)">Copy</button><button class="cut-btn" onclick="cutText(this)">Cut</button><button class="delete-btn" onclick="deleteText(this)">Delete</button></div></div>`
                    ).join('');
                }
            } catch (error) {
                document.getElementById('texts-container').innerHTML = 
                    '<div class="loading">Error loading texts. Please try again.</div>';
                console.error('Error fetching texts:', error);
            }
        }

        function copyText(button) {
            const item = button.closest('.text-item');
            const text = item.cloneNode(true);
            text.querySelector('.actions').remove();
            navigator.clipboard.writeText(text.textContent).then(() => {
                button.classList.add('copied');
                const original = button.textContent;
                button.textContent = 'Copied!';
                setTimeout(() => {
                    button.classList.remove('copied');
                    button.textContent = original;
                }, 1000);
            });
        }

        async function cutText(button) {
            const item = button.closest('.text-item');
            const text = item.cloneNode(true);
            text.querySelector('.actions').remove();
            navigator.clipboard.writeText(text.textContent).then(async () => {
                const fileId = item.dataset.id;
                await fetch(`/api/text/${fileId}`, { method: 'DELETE' });
                item.classList.add('removing');
                setTimeout(() => item.remove(), 500);
            });
        }

        async function deleteText(button) {
            const item = button.closest('.text-item');
            const fileId = item.dataset.id;
            await fetch(`/api/text/${fileId}`, { method: 'DELETE' });
            item.classList.add('removing');
            setTimeout(() => item.remove(), 500);
        }

        fetchTexts();
        setInterval(fetchTexts, 2000);
    </script>
</body>
</html>
'''
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=False)
