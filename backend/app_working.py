import json
import os
import uuid
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename


# Basic configuration
class Config:
    SECRET_KEY = 'Fathi98843'
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'uploads')
    MAX_FILE_SIZE = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}
    GEMINI_API_KEY = 'AIzaSyCpGo9qtU9Gz2qfc5Rnh-BNbJ-UGlulKbI'


app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Create upload directory
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# Initialize components with error handling
document_processor = None
gemini_analyzer = None
prompt_generator = None

try:
    from utils.document_processor import DocumentProcessor

    document_processor = DocumentProcessor()
    print("✅ Document processor initialized")
except Exception as e:
    print(f"❌ Document processor failed: {e}")

try:
    from utils.gemini_analyzer import GeminiAnalyzer

    if Config.GEMINI_API_KEY:
        gemini_analyzer = GeminiAnalyzer(Config.GEMINI_API_KEY)
        print("✅ Gemini analyzer initialized")
    else:
        print("⚠️ No Gemini API key")
except Exception as e:
    print(f"❌ Gemini analyzer failed: {e}")

try:
    from utils.prompt_generator import PromptGenerator

    prompt_generator = PromptGenerator()
    print("✅ Prompt generator initialized")
except Exception as e:
    print(f"❌ Prompt generator failed: {e}")

# Simple document storage
documents = {}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)


@app.route('/api/health')
def health_check():
    return jsonify(
        {
            'status': 'healthy',
            'components': {
                'document_processor': document_processor is not None,
                'gemini_analyzer': gemini_analyzer is not None,
                'prompt_generator': prompt_generator is not None,
            },
        }
    )


@app.route('/api/upload', methods=['POST'])
def upload_document():
    try:
        if 'document' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['document']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file'}), 400

        # Save file
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        file.save(file_path)

        # Process document
        document_id = str(uuid.uuid4())

        if document_processor:
            try:
                processed_data = document_processor.process_document(file_path, filename)
                document_id = processed_data['document_id']
            except Exception as e:
                # Fallback processing
                processed_data = {
                    'document_id': document_id,
                    'filename': filename,
                    'text': f"File {filename} uploaded - processing failed: {str(e)}",
                    'chunks': [f"Content of {filename}"],
                    'chunk_count': 1,
                    'metadata': {'filename': filename, 'word_count': 0},
                }
        else:
            # Basic file processing
            try:
                if filename.lower().endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                else:
                    text = f"File {filename} uploaded successfully"

                processed_data = {
                    'document_id': document_id,
                    'filename': filename,
                    'text': text,
                    'chunks': [text],
                    'chunk_count': 1,
                    'metadata': {'filename': filename, 'word_count': len(text.split())},
                }
            except Exception as e:
                processed_data = {
                    'document_id': document_id,
                    'filename': filename,
                    'text': f"File {filename} uploaded - text extraction failed",
                    'chunks': [f"Content of {filename}"],
                    'chunk_count': 1,
                    'metadata': {'filename': filename, 'word_count': 0},
                }

        # Store document
        documents[document_id] = {
            'filename': filename,
            'file_path': file_path,
            'processed_data': processed_data,
            'upload_time': datetime.now().isoformat(),
            'status': 'uploaded',
        }

        return jsonify(
            {
                'success': True,
                'document_id': document_id,
                'filename': filename,
                'chunk_count': processed_data['chunk_count'],
            }
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analyze/<document_id>', methods=['POST'])
def analyze_document(document_id):
    try:
        if document_id not in documents:
            return jsonify({'success': False, 'error': 'Document not found'}), 404

        doc_data = documents[document_id]
        processed_data = doc_data['processed_data']
        documents[document_id]['status'] = 'analyzing'

        # Basic analysis
        word_count = len(processed_data.get('text', '').split())
        text_lower = processed_data.get('text', '').lower()

        # Simple document type detection
        doc_type = 'Legal Document'
        if any(word in text_lower for word in ['employment', 'employee', 'job']):
            doc_type = 'Employment Contract'
        elif any(word in text_lower for word in ['service', 'services']):
            doc_type = 'Service Agreement'
        elif any(word in text_lower for word in ['confidential', 'non-disclosure']):
            doc_type = 'Non-Disclosure Agreement'
        elif any(word in text_lower for word in ['lease', 'rent']):
            doc_type = 'Lease Agreement'

        analysis = {
            'document_type': doc_type,
            'summary': f'This appears to be a {doc_type} containing {word_count} words.',
            'parties': [],
            'dates': [],
            'financial_terms': [],
            'key_terms': [
                {'term': 'Document Processing', 'definition': f'Successfully processed {doc_data["filename"]}'}
            ],
            'rights_obligations': {},
            'risks': [
                {'title': 'Basic Analysis', 'description': 'Document processed with basic analysis', 'level': 'Low'}
            ],
            'recommendations': [],
        }

        # Try Gemini analysis if available
        if gemini_analyzer:
            try:
                gemini_analysis = gemini_analyzer.analyze_document(processed_data.get('text', ''))
                if gemini_analysis:
                    analysis.update(gemini_analysis)
            except Exception as e:
                print(f"Gemini analysis failed: {e}")

        documents[document_id]['analysis'] = analysis
        documents[document_id]['status'] = 'completed'

        return jsonify({'success': True, 'data': analysis})

    except Exception as e:
        if document_id in documents:
            documents[document_id]['status'] = 'error'
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate-prompts', methods=['POST'])
def generate_prompts():
    try:
        data = request.get_json()
        document_id = data.get('document_id')
        analysis_data = data.get('analysis_data', {})

        if not document_id or document_id not in documents:
            return jsonify({'success': False, 'error': 'Document not found'}), 404

        doc_data = documents[document_id]
        document_text = doc_data['processed_data']['text']

        if prompt_generator:
            prompts = prompt_generator.generate_prompts(document_text, analysis_data)
        else:
            # Fallback prompts based on document type
            doc_type = analysis_data.get('document_type', 'Legal Document')
            if 'Employment' in doc_type:
                prompts = [
                    "What is the salary and compensation?",
                    "What are the termination conditions?",
                    "Are there any non-compete clauses?",
                    "What benefits are included?",
                ]
            elif 'Service' in doc_type:
                prompts = [
                    "What services are provided?",
                    "What are the payment terms?",
                    "What are the deliverables?",
                    "How is performance measured?",
                ]
            elif 'Disclosure' in doc_type:
                prompts = [
                    "What information is confidential?",
                    "How long does confidentiality last?",
                    "What are the penalties?",
                    "What are the exceptions?",
                ]
            else:
                prompts = [
                    "What are the main obligations?",
                    "What are the payment terms?",
                    "When does this expire?",
                    "What are the breach consequences?",
                ]

        return jsonify({'success': True, 'prompts': prompts})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/question', methods=['POST'])
def ask_question():
    try:
        data = request.get_json()
        document_id = data.get('document_id')
        question = data.get('question')

        if not document_id or not question:
            return jsonify({'success': False, 'error': 'Document ID and question required'}), 400

        if document_id not in documents:
            return jsonify({'success': False, 'error': 'Document not found'}), 404

        doc_data = documents[document_id]
        text = doc_data['processed_data']['text']

        # Try Gemini Q&A if available
        if gemini_analyzer:
            try:
                context = doc_data.get('analysis', {})
                answer = gemini_analyzer.answer_question(text, question, context)
                return jsonify({'success': True, 'answer': answer, 'question': question})
            except Exception as e:
                print(f"Gemini Q&A failed: {e}")

        # Fallback keyword search
        question_lower = question.lower()
        text_lower = text.lower()
        keywords = [w for w in question_lower.split() if len(w) > 3]
        found = [w for w in keywords if w in text_lower]

        if found:
            answer = f"Found relevant keywords: {', '.join(found[:3])}. Configure Gemini API key for detailed analysis."
        else:
            answer = "Could not find specific information. Try different keywords or check document content."

        return jsonify({'success': True, 'answer': answer, 'question': question})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/documents', methods=['GET'])
def list_documents():
    try:
        doc_list = []
        for doc_id, doc_data in documents.items():
            doc_list.append(
                {
                    'document_id': doc_id,
                    'filename': doc_data['filename'],
                    'upload_time': doc_data['upload_time'],
                    'status': doc_data['status'],
                }
            )
        return jsonify({'success': True, 'documents': doc_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/document/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    try:
        if document_id not in documents:
            return jsonify({'success': False, 'error': 'Document not found'}), 404

        doc_data = documents[document_id]
        file_path = doc_data['file_path']

        if os.path.exists(file_path):
            os.remove(file_path)

        del documents[document_id]
        return jsonify({'success': True, 'message': 'Document deleted'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.errorhandler(413)
def file_too_large(e):
    return jsonify({'success': False, 'error': 'File too large'}), 413


if __name__ == '__main__':
    print("🚀 Starting AI Legal Assistant (Working Version)")
    print("=" * 50)
    print(f"📁 Upload folder: {Config.UPLOAD_FOLDER}")
    print(f"🔐 Gemini API: {'✅' if Config.GEMINI_API_KEY else '❌'}")
    print(f"📄 Document Processor: {'✅' if document_processor else '⚠️ Basic'}")
    print(f"🤖 Gemini Analyzer: {'✅' if gemini_analyzer else '⚠️ Basic'}")
    print(f"🎯 Prompt Generator: {'✅' if prompt_generator else '⚠️ Basic'}")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=5000)
