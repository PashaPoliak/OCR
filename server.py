from flask import Flask, request, jsonify, render_template_string
import logging
import os
from datetime import datetime

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='server.log', filemode='a')

@app.route('/api/text', methods=['POST'])
def receive_text():
    try:
        data = request.get_json()
        if not data or 'filename' not in data or 'text' not in data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        filename = data['filename']
        text = data['text']
        
        logging.info(f"Received text from {filename}: {text[:100]}...")  # Log first 100 chars
        
        # Save to file
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
                    # Extract only the text content (after "Text:\n")
                    lines = content.split('\n')
                    text_content = '\n'.join(lines[3:]) if len(lines) > 3 else ''
                    texts.append(text_content.strip())
        
        return jsonify({'texts': texts})
    
    except Exception as e:
        logging.error(f"Error retrieving texts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    html = '''
<!DOCTYPE html>
<html>
<head>
    <title>OCR Texts</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .text-item { border: 1px solid #ccc; padding: 10px; margin: 10px 0; white-space: pre-wrap; }
        .loading { color: #666; }
    </style>
</head>
<body>
    <h1>Extracted OCR Texts</h1>
    <div id="texts-container">
        <div class="loading">Loading texts...</div>
    </div>

    <script>
        async function fetchTexts() {
            try {
                const response = await fetch('/api/texts');
                const data = await response.json();
                const container = document.getElementById('texts-container');
                
                if (data.texts && data.texts.length > 0) {
                    container.innerHTML = data.texts.map(text => 
                        `<div class="text-item">${text}</div>`
                    ).join('');
                } else {
                    container.innerHTML = '<div class="loading">No texts available yet.</div>';
                }
            } catch (error) {
                document.getElementById('texts-container').innerHTML = 
                    '<div class="loading">Error loading texts. Please try again.</div>';
                console.error('Error fetching texts:', error);
            }
        }

        // Fetch texts immediately and then every 5 seconds
        fetchTexts();
        setInterval(fetchTexts, 5000);
    </script>
</body>
</html>
'''
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=False)