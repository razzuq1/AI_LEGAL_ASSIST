#!/usr/bin/env python3
"""
Windows Installation Fix Script for AI Legal Assistant
Handles Python 3.12 compatibility issues
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
    """Run command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("✅ Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False


def upgrade_pip():
    """Upgrade pip to latest version"""
    print("📦 Upgrading pip...")
    return run_command(f"{sys.executable} -m pip install --upgrade pip setuptools wheel", "Upgrading pip")


def install_minimal_packages():
    """Install packages one by one"""
    packages = ["Flask", "Flask-CORS", "python-dotenv", "PyPDF2", "google-generativeai", "requests"]

    failed_packages = []

    for package in packages:
        print(f"📦 Installing {package}...")
        if run_command(f"{sys.executable} -m pip install {package}", f"Installing {package}"):
            print(f"✅ {package} installed")
        else:
            print(f"❌ {package} failed")
            failed_packages.append(package)

    return failed_packages


def install_optional_packages():
    """Try to install optional packages"""
    optional = [
        ("python-docx", "Word document support"),
        ("sentence-transformers", "Text embeddings (optional)"),
        ("faiss-cpu", "Vector search (optional)"),
    ]

    for package, description in optional:
        print(f"📦 Installing {package} ({description})...")
        if not run_command(f"{sys.executable} -m pip install {package}", f"Installing {package}"):
            print(f"⚠️ {package} failed - continuing without it")


def create_simple_app():
    """Create a simplified app.py that works without optional packages"""
    app_content = '''import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Fathi98843'
app.config['UPLOAD_FOLDER'] = 'data/uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

CORS(app)

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Simple document storage
documents = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'txt', 'doc', 'docx'}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'mode': 'basic'})

@app.route('/api/upload', methods=['POST'])
def upload():
    try:
        if 'document' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['document']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file'}), 400
        
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Basic text extraction
        try:
            if filename.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            elif filename.lower().endswith('.pdf'):
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() + "\\n"
                except:
                    text = "PDF processing failed - install PyPDF2"
            else:
                text = f"File {filename} uploaded but text extraction not available"
            
            doc_id = str(uuid.uuid4())
            documents[doc_id] = {
                'filename': filename,
                'text': text,
                'file_path': file_path,
                'upload_time': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'document_id': doc_id,
                'filename': filename,
                'chunk_count': 1
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': f'Processing failed: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analyze/<document_id>', methods=['POST'])
def analyze(document_id):
    try:
        if document_id not in documents:
            return jsonify({'success': False, 'error': 'Document not found'}), 404
        
        doc = documents[document_id]
        word_count = len(doc['text'].split())
        
        # Basic analysis
        analysis = {
            'document_type': 'Legal Document',
            'summary': f'Document "{doc["filename"]}" contains {word_count} words. Basic processing completed.',
            'key_terms': [
                {'term': 'File Processing', 'definition': f'Document uploaded and processed successfully'}
            ],
            'risks': [
                {'title': 'Basic Mode', 'description': 'Install additional packages for AI analysis', 'level': 'Low'}
            ]
        }
        
        return jsonify({'success': True, 'data': analysis})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/question', methods=['POST'])
def question():
    try:
        data = request.get_json()
        doc_id = data.get('document_id')
        question = data.get('question')
        
        if doc_id not in documents:
            return jsonify({'success': False, 'error': 'Document not found'}), 404
        
        # Basic keyword search
        doc = documents[doc_id]
        text_lower = doc['text'].lower()
        question_lower = question.lower()
        
        keywords = [w for w in question_lower.split() if len(w) > 3]
        found = [w for w in keywords if w in text_lower]
        
        if found:
            answer = f"Found keywords: {', '.join(found)}. Install AI packages for detailed answers."
        else:
            answer = "No specific information found. Try different keywords."
        
        return jsonify({'success': True, 'answer': answer})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting AI Legal Assistant (Basic Mode)")
    print("Install additional packages for AI features:")
    print("  pip install google-generativeai sentence-transformers faiss-cpu")
    app.run(debug=True, host='0.0.0.0', port=5000)
'''

    with open('app_basic.py', 'w') as f:
        f.write(app_content)
    print("✅ Created app_basic.py (fallback version)")


def main():
    print("🔧 Windows Installation Fix")
    print("=" * 40)

    # Upgrade pip first
    if not upgrade_pip():
        print("❌ Could not upgrade pip - continuing anyway")

    # Install core packages
    failed = install_minimal_packages()

    if failed:
        print(f"\n⚠️ Some packages failed: {failed}")
        print("Creating basic version that works without them...")
        create_simple_app()

    # Try optional packages
    install_optional_packages()

    # Create directories
    os.makedirs('data/uploads', exist_ok=True)
    os.makedirs('utils', exist_ok=True)
    Path('utils/__init__.py').touch()

    print("\n" + "=" * 40)
    print("✅ Installation complete!")

    if failed:
        print("\n🏃 Run basic version:")
        print("  python app_basic.py")
    else:
        print("\n🏃 Run full version:")
        print("  python run.py")

    print("\n🌐 Then open: http://localhost:5000")


if __name__ == '__main__':
    main()
