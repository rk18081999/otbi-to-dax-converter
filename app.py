from flask import Flask, render_template, request, jsonify, send_file
import os
from io import BytesIO
from llm_reasoner import LLMReasoner

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize LLM reasoner (will be created per request to handle API key)
def get_reasoner():
    """Get LLM reasoner instance"""
    try:
        return LLMReasoner()
    except ValueError as e:
        raise Exception(f"LLM API not configured: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    from datetime import datetime
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'OTBI to DAX Converter'
    })

@app.route('/convert', methods=['POST'])
def convert():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.sql'):
            return jsonify({'error': 'Please upload a .sql file'}), 400
        
        # Read SQL content
        sql_text = file.read().decode('utf-8')
        
        # Get LLM reasoner
        reasoner = get_reasoner()
        
        # Convert using LLM reasoning
        result = reasoner.convert_sql_to_dax(sql_text)
        
        # Return DAX content and analysis
        return jsonify({
            'success': True,
            'dax': result['dax'],
            'filename': file.filename.replace('.sql', '.dax'),
            'semantic_analysis': result.get('semantic_analysis', {}),
            'join_analysis': result.get('join_analysis', {})
        })
        
    except Exception as e:
        error_msg = str(e)
        if "API not configured" in error_msg:
            error_msg += "\n\nPlease set GEMINI_API_KEY in llm_config.py"
        return jsonify({'error': error_msg}), 500

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        dax_content = data.get('dax', '')
        filename = data.get('filename', 'output.dax')
        
        # Create file in memory
        buffer = BytesIO()
        buffer.write(dax_content.encode('utf-8'))
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 OTBI to DAX Converter - LLM-Powered")
    print("=" * 60)
    print("\n📝 Make sure to set your GEMINI_API_KEY in llm_config.py")
    print("   Get one at: https://makersuite.google.com/app/apikey\n")
    print("🌐 Server starting at: http://127.0.0.1:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)
