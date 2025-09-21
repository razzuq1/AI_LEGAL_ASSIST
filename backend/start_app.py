#!/usr/bin/env python3
"""
Simple startup script for AI Legal Assistant
Handles missing dependencies gracefully
"""

import os
import sys
from pathlib import Path


def create_minimal_utils():
    """Create minimal utility files if they don't exist"""
    utils_dir = Path('utils')
    utils_dir.mkdir(exist_ok=True)

    # Create __init__.py
    init_file = utils_dir / '__init__.py'
    if not init_file.exists():
        init_file.write_text('')

    # Create minimal document_processor.py
    doc_processor_file = utils_dir / 'document_processor.py'
    if not doc_processor_file.exists():
        doc_processor_code = '''import uuid
import os

class DocumentProcessor:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process_document(self, file_path, filename):
        try:
            if filename.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            else:
                text = f"File {filename} uploaded successfully"
            
            return {
                'document_id': str(uuid.uuid4()),
                'filename': filename,
                'text': text,
                'chunks': [text],
                'chunk_count': 1,
                'metadata': {'filename': filename, 'word_count': len(text.split())}
            }
        except Exception as e:
            raise Exception(f"Processing failed: {e}")
'''
        doc_processor_file.write_text(doc_processor_code)

    # Create minimal gemini_analyzer.py
    gemini_file = utils_dir / 'gemini_analyzer.py'
    if not gemini_file.exists():
        gemini_code = '''class GeminiAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.available = True
        except Exception as e:
            print(f"Gemini unavailable: {e}")
            self.available = False
    
    def analyze_document(self, text):
        if not self.available:
            return {
                'document_type': 'Legal Document',
                'summary': 'Basic analysis only - Gemini API not available',
                'key_terms': [],
                'risks': [],
                'parties': [],
                'dates': [],
                'financial_terms': []
            }
        
        try:
            prompt = f"Analyze this legal document: {text[:2000]}"
            response = self.model.generate_content(prompt)
            return {
                'document_type': 'Legal Document',
                'summary': response.text[:500] if response.text else 'Analysis completed',
                'key_terms': [],
                'risks': [],
                'parties': [],
                'dates': [],
                'financial_terms': []
            }
        except Exception as e:
            return {
                'document_type': 'Legal Document', 
                'summary': f'AI analysis failed: {e}',
                'key_terms': [],
                'risks': [],
                'parties': [],
                'dates': [],
                'financial_terms': []
            }
    
    def answer_question(self, text, question, context=None):
        if not self.available:
            return "Basic mode - install google-generativeai for AI features"
        
        try:
            prompt = f"Question: {question}\\n\\nDocument: {text[:2000]}"
            response = self.model.generate_content(prompt)
            return response.text if response.text else "Could not generate answer"
        except Exception as e:
            return f"Answer generation failed: {e}"
'''
        gemini_file.write_text(gemini_code)

    # Create minimal prompt_generator.py
    prompt_file = utils_dir / 'prompt_generator.py'
    if not prompt_file.exists():
        prompt_code = '''class PromptGenerator:
    def generate_prompts(self, text, analysis_data=None):
        doc_type = analysis_data.get('document_type', 'Legal Document') if analysis_data else 'Legal Document'
        
        if 'Employment' in doc_type:
            return [
                "What is the salary and compensation?",
                "What are the termination conditions?", 
                "Are there any non-compete clauses?",
                "What benefits are included?"
            ]
        elif 'Service' in doc_type:
            return [
                "What services are provided?",
                "What are the payment terms?",
                "What are the deliverables?",
                "How is performance measured?"
            ]
        else:
            return [
                "What are the main obligations?",
                "What are the payment terms?",
                "When does this expire?",
                "What are the breach consequences?"
            ]
'''
        prompt_file.write_text(prompt_code)

    print("✅ Created minimal utility files")


def main():
    print("🔧 AI Legal Assistant Startup Fix")
    print("=" * 40)

    # Create directories
    os.makedirs('data/uploads', exist_ok=True)
    print("✅ Created data directories")

    # Create minimal utils
    create_minimal_utils()

    # Check for .env file
    env_file = Path('.env')
    if not env_file.exists():
        env_content = """GEMINI_API_KEY=AIzaSyCpGo9qtU9Gz2qfc5Rnh-BNbJ-UGlulKbI
SECRET_KEY=Fathi98843
FLASK_ENV=development
FLASK_DEBUG=1
"""
        env_file.write_text(env_content)
        print("✅ Created .env file")

    print("\n🚀 Starting application...")

    # Import and run the working app
    try:
        from app_working import app

        print("✅ Application loaded successfully")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Run: python app_working.py directly")
    except Exception as e:
        print(f"❌ Startup error: {e}")


if __name__ == '__main__':
    main()
