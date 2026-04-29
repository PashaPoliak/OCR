from flask import Flask, request, jsonify
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=False)