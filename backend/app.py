import json
import os
import uuid
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import configuration
try:
    from config import Config

    print("✅ Config imported")
except ImportError:
    print("⚠️ Config not found, using defaults")

    class Config:
        SECRET_KEY = 'dev-key-123'
        UPLOAD_FOLDER = 'uploads'
        MAX_CONTENT_LENGTH = 50 * 1024 * 1024
        ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}
        CHUNK_SIZE = 1000
        CHUNK_OVERLAP = 200
        VECTOR_STORE_PATH = 'data/vector_store'
        GEMINI_API_KEY = 'AIzaSyCpGo9qtU9Gz2qfc5Rnh-BNbJ-UGlulKbI'
        GEMINI_MODEL = 'gemini-1.5-flash'
        EMBEDDING_MODEL = 'text-embedding-004'

        @staticmethod
        def init_app(app):
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            os.makedirs('data', exist_ok=True)
            os.makedirs(Config.VECTOR_STORE_PATH, exist_ok=True)


# Import RAGPipeline from the correct file
try:
    from utils.pipeline import RAGPipeline

    print("✅ RAGPipeline imported from pipeline.py")
    RAG_AVAILABLE = True
except ImportError:
    print("❌ RAGPipeline not found in utils.pipeline")
    RAG_AVAILABLE = False

# Try to import other components, with fallbacks
try:
    from utils.document_processor import DocumentProcessor

    DOCUMENT_PROCESSOR_AVAILABLE = True
    print("✅ DocumentProcessor imported")
except ImportError:
    print("⚠️ DocumentProcessor not available")
    DOCUMENT_PROCESSOR_AVAILABLE = False

try:
    from utils.gemini_analyzer import GeminiAnalyzer

    GEMINI_ANALYZER_AVAILABLE = True
    print("✅ GeminiAnalyzer imported")
except ImportError:
    print("⚠️ GeminiAnalyzer not available")
    GEMINI_ANALYZER_AVAILABLE = False

try:
    from utils.vector_store import VectorStore

    VECTOR_STORE_AVAILABLE = True
    print("✅ VectorStore imported")
except ImportError:
    print("⚠️ VectorStore not available")
    VECTOR_STORE_AVAILABLE = False

try:
    from utils.prompt_generator import PromptGenerator

    PROMPT_GENERATOR_AVAILABLE = True
    print("✅ PromptGenerator imported")
except ImportError:
    print("⚠️ PromptGenerator not available")
    PROMPT_GENERATOR_AVAILABLE = False

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize components with CORRECT model names
document_processor = None
if DOCUMENT_PROCESSOR_AVAILABLE:
    try:
        document_processor = DocumentProcessor(chunk_size=Config.CHUNK_SIZE, chunk_overlap=Config.CHUNK_OVERLAP)
        print("✅ Document processor initialized")
    except Exception as e:
        print(f"❌ Document processor failed: {e}")

gemini_analyzer = None
if GEMINI_ANALYZER_AVAILABLE:
    try:
        if Config.GEMINI_API_KEY:
            gemini_analyzer = GeminiAnalyzer(Config.GEMINI_API_KEY)
            print("✅ Gemini analyzer initialized")
    except Exception as e:
        print(f"❌ Gemini analyzer failed: {e}")

# RAGPipeline with EXPLICIT correct model names
rag_pipeline = None
if RAG_AVAILABLE:
    try:
        if Config.GEMINI_API_KEY:
            # EXPLICITLY use correct model names to prevent 404 error
            rag_pipeline = RAGPipeline(
                api_key=Config.GEMINI_API_KEY, model="gemini-1.5-flash", embedding_model="text-embedding-004"
            )
            print("✅ RAG pipeline initialized with gemini-1.5-flash")
        else:
            rag_pipeline = RAGPipeline(api_key=None)
            print("⚠️ No Gemini API key - using basic analysis")
    except Exception as e:
        print(f"❌ RAG pipeline failed: {e}")
        try:
            rag_pipeline = RAGPipeline(api_key=None) if RAG_AVAILABLE else None
        except:
            rag_pipeline = None

vector_store = None
if VECTOR_STORE_AVAILABLE:
    try:
        vector_store = VectorStore(Config.VECTOR_STORE_PATH)
        print("✅ Vector store initialized")
    except Exception as e:
        print(f"❌ Vector store failed: {e}")

prompt_generator = None
if PROMPT_GENERATOR_AVAILABLE:
    try:
        prompt_generator = PromptGenerator()
        print("✅ Prompt generator initialized")
    except Exception as e:
        print(f"❌ Prompt generator failed: {e}")

# In-memory document storage
documents = {}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def basic_document_processing(file_path, filename):
    """Fallback document processing if DocumentProcessor not available"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()

        # Simple chunking
        words = text.split()
        chunk_size = 200  # words per chunk
        chunks = []

        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i : i + chunk_size])
            chunks.append(chunk)

        if not chunks:
            chunks = [f"File {filename} uploaded but no text extracted"]

        return {
            'document_id': str(uuid.uuid4()),
            'text': text,
            'chunks': chunks,
            'chunk_count': len(chunks),
            'metadata': {'filename': filename, 'word_count': len(words), 'char_count': len(text)},
        }
    except Exception as e:
        return {
            'document_id': str(uuid.uuid4()),
            'text': f"Error processing {filename}: {str(e)}",
            'chunks': [f"File {filename} uploaded with processing error"],
            'chunk_count': 1,
            'metadata': {'filename': filename, 'error': str(e)},
        }


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
                'rag_pipeline': rag_pipeline is not None and getattr(rag_pipeline, 'ai_available', False),
                'vector_store': vector_store is not None,
                'prompt_generator': prompt_generator is not None,
            },
            'gemini_api_configured': bool(Config.GEMINI_API_KEY),
            'model_info': {
                'gemini_model': getattr(Config, 'GEMINI_MODEL', 'gemini-1.5-flash'),
                'embedding_model': getattr(Config, 'EMBEDDING_MODEL', 'text-embedding-004'),
            },
        }
    )


@app.route('/api/test-ai', methods=['GET'])
def test_ai():
    """Test AI connection endpoint"""
    if rag_pipeline:
        result = rag_pipeline.test_ai_connection()
        return jsonify({'result': result})
    else:
        return jsonify({'result': 'RAG pipeline not available'})


@app.route('/api/upload', methods=['POST'])
def upload_document():
    try:
        if 'document' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['document']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400

        # Save file
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        file.save(file_path)

        # Process document
        if document_processor:
            try:
                processed_data = document_processor.process_document(file_path, filename)
            except Exception as e:
                print(f"⚠️ Document processor failed, using fallback: {e}")
                processed_data = basic_document_processing(file_path, filename)
        else:
            processed_data = basic_document_processing(file_path, filename)

        document_id = processed_data['document_id']

        # Add to vector store if available
        if vector_store:
            try:
                vector_store.add_document(document_id, processed_data['chunks'], processed_data['metadata'])
            except Exception as e:
                print(f"⚠️ Vector store add failed: {e}")

        # Store in memory
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
        app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analyze/<document_id>', methods=['POST'])
def analyze_document(document_id):
    try:
        if document_id not in documents:
            return jsonify({'success': False, 'error': 'Document not found'}), 404

        doc_data = documents[document_id]
        processed_data = doc_data['processed_data']
        documents[document_id]['status'] = 'analyzing'

        # Create document chunks for RAG
        chunks = []
        for chunk_text in processed_data['chunks']:
            chunks.append({'page_content': chunk_text})

        # Analyze with RAG pipeline (which now uses correct model)
        if rag_pipeline:
            try:
                print(f"🔍 Starting RAG analysis for {doc_data['filename']} using gemini-1.5-flash")
                rag_analysis = rag_pipeline.analyze_document(chunks, document_id)

                # Format analysis for frontend
                analysis = {
                    'document_type': rag_analysis.get('document_type', 'Legal Document'),
                    'summary': rag_analysis.get(
                        'summary', f'Document "{doc_data["filename"]}" processed successfully.'
                    ),
                    'parties': [],
                    'dates': [],
                    'financial_terms': [],
                    'key_terms': [],
                    'rights_obligations': {},
                    'risks': [],
                    'recommendations': [],
                }

                # Parse key terms
                key_terms_text = rag_analysis.get('key_terms', '')
                key_terms = []

                if key_terms_text and isinstance(key_terms_text, str):
                    for line in key_terms_text.split('\n'):
                        if line.strip() and ':' in line:
                            parts = line.strip().replace('- ', '').split(':', 1)
                            if len(parts) == 2:
                                key_terms.append({'term': parts[0].strip(), 'definition': parts[1].strip()})

                if not key_terms:
                    key_terms = [
                        {
                            'term': 'Document Processing',
                            'definition': 'Document successfully analyzed and processed with AI',
                        }
                    ]

                analysis['key_terms'] = key_terms

                # Parse risks
                risks_text = rag_analysis.get('risks_analysis', '')
                if rag_pipeline and hasattr(rag_pipeline, 'parse_risks'):
                    risks = rag_pipeline.parse_risks(risks_text)
                else:
                    risks = [
                        {
                            'title': 'Analysis Complete',
                            'description': 'Document processed successfully with AI analysis',
                            'level': 'Low',
                        }
                    ]

                analysis['risks'] = risks

                # Add AI-specific fields if available
                if rag_analysis.get('ai_enhanced'):
                    analysis['parties'] = rag_analysis.get('parties', [])
                    analysis['important_dates'] = rag_analysis.get('important_dates', [])
                    analysis['financial_terms'] = rag_analysis.get('financial_terms', [])
                    analysis['ai_powered'] = True
                else:
                    analysis['ai_powered'] = False

                documents[document_id]['analysis'] = analysis
                documents[document_id]['status'] = 'completed'

                print("✅ RAG analysis completed successfully with gemini-1.5-flash")
                return jsonify({'success': True, 'data': analysis})

            except Exception as e:
                print(f"❌ RAG analysis error: {str(e)}")
                app.logger.error(f"RAG analysis error: {str(e)}")
                # Fall through to basic analysis

        # Fallback basic analysis
        print("⚠️ Using fallback basic analysis")
        word_count = len(processed_data.get('text', '').split())
        analysis = {
            'document_type': 'Legal Document',
            'summary': f'Document "{doc_data["filename"]}" uploaded successfully with {word_count} words. Basic analysis completed.',
            'parties': [],
            'dates': [],
            'financial_terms': [],
            'key_terms': [{'term': 'Document Upload', 'definition': 'File processed successfully'}],
            'rights_obligations': {},
            'risks': [
                {
                    'title': 'Basic Processing',
                    'description': 'Document processed with basic analysis. Configure Gemini API key for enhanced analysis.',
                    'level': 'Low',
                }
            ],
            'recommendations': ['Configure Gemini API key for detailed AI analysis'],
            'ai_powered': False,
        }

        documents[document_id]['analysis'] = analysis
        documents[document_id]['status'] = 'completed'

        return jsonify({'success': True, 'data': analysis})

    except Exception as e:
        app.logger.error(f"Analysis error: {str(e)}")
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
        document_text = doc_data['processed_data'].get('text', '')

        if prompt_generator:
            try:
                prompts = prompt_generator.generate_prompts(document_text, analysis_data)
                return jsonify({'success': True, 'prompts': prompts})
            except Exception as e:
                print(f"⚠️ Prompt generator failed: {e}")

        # Fallback prompts based on document type
        doc_type = analysis_data.get('document_type', 'Legal Document').lower()

        if 'employment' in doc_type:
            fallback_prompts = [
                "What are my job responsibilities?",
                "What is my salary and benefits?",
                "What are the working hours?",
                "How can this employment be terminated?",
                "What are the confidentiality requirements?",
            ]
        elif 'service' in doc_type:
            fallback_prompts = [
                "What services are being provided?",
                "What are the payment terms?",
                "When does this agreement expire?",
                "What are the deliverables?",
                "What happens if services are not satisfactory?",
            ]
        elif 'lease' in doc_type:
            fallback_prompts = [
                "What is the monthly rent?",
                "When does the lease expire?",
                "What are the tenant's responsibilities?",
                "Are pets allowed?",
                "What is the security deposit?",
            ]
        else:
            fallback_prompts = [
                "What are the main obligations of each party?",
                "What are the payment terms and amounts?",
                "When does this agreement expire?",
                "What happens if someone breaches the contract?",
                "What are the key dates and deadlines?",
                "Are there any penalties mentioned?",
            ]

        return jsonify({'success': True, 'prompts': fallback_prompts})

    except Exception as e:
        app.logger.error(f"Prompt generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/question', methods=['POST'])
def ask_question():
    """Fixed question route with comprehensive debugging"""
    try:
        data = request.get_json()
        document_id = data.get('document_id')
        question = data.get('question')

        print(f"🔍 Question route called")
        print(f"📄 Document ID: {document_id}")
        print(f"❓ Question: {question}")

        if not document_id or not question:
            return jsonify({'success': False, 'error': 'Document ID and question required'}), 400

        if document_id not in documents:
            print(f"❌ Document {document_id} not found in app documents")
            print(f"Available documents: {list(documents.keys())}")
            return jsonify({'success': False, 'error': 'Document not found'}), 404

        # Debug: Check document status
        if rag_pipeline:
            debug_info = rag_pipeline.debug_document_status(document_id)
            print(f"🔍 Debug info: {debug_info}")

        # Use RAG pipeline for Q&A
        if rag_pipeline:
            try:
                print(f"🤖 Using RAG pipeline for Q&A")
                answer = rag_pipeline.answer_question(document_id, question)

                return jsonify(
                    {
                        'success': True,
                        'answer': answer,
                        'question': question,
                        'ai_powered': getattr(rag_pipeline, 'ai_available', False),
                    }
                )
            except Exception as e:
                print(f"❌ RAG Q&A error in app.py: {str(e)}")
                app.logger.error(f"RAG Q&A error: {str(e)}")

        # Fallback response
        return jsonify(
            {
                'success': True,
                'answer': "I'm unable to process questions right now. Please check that the document was properly analyzed.",
                'question': question,
                'ai_powered': False,
            }
        )

    except Exception as e:
        print(f"❌ Question route error: {str(e)}")
        app.logger.error(f"Question error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/documents', methods=['GET'])
def list_documents():
    try:
        doc_list = []
        for doc_id, doc_data in documents.items():
            word_count = 0
            if 'processed_data' in doc_data and 'metadata' in doc_data['processed_data']:
                word_count = doc_data['processed_data']['metadata'].get('word_count', 0)

            doc_list.append(
                {
                    'document_id': doc_id,
                    'filename': doc_data['filename'],
                    'upload_time': doc_data['upload_time'],
                    'status': doc_data['status'],
                    'word_count': word_count,
                }
            )

        return jsonify({'success': True, 'documents': doc_list})
    except Exception as e:
        app.logger.error(f"List documents error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/document/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    try:
        if document_id not in documents:
            return jsonify({'success': False, 'error': 'Document not found'}), 404

        doc_data = documents[document_id]
        file_path = doc_data['file_path']

        # Remove file
        if os.path.exists(file_path):
            os.remove(file_path)

        # Remove from vector store
        if vector_store:
            try:
                vector_store.delete_document(document_id)
            except Exception as e:
                print(f"⚠️ Vector store delete failed: {e}")

        # Remove from RAG pipeline
        if rag_pipeline and hasattr(rag_pipeline, 'vector_store') and document_id in rag_pipeline.vector_store:
            del rag_pipeline.vector_store[document_id]

        if rag_pipeline and hasattr(rag_pipeline, 'documents') and document_id in rag_pipeline.documents:
            del rag_pipeline.documents[document_id]

        # Remove from memory
        del documents[document_id]

        return jsonify({'success': True, 'message': 'Document deleted successfully'})

    except Exception as e:
        app.logger.error(f"Delete error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.errorhandler(413)
def file_too_large(e):
    return jsonify({'success': False, 'error': 'File size too large'}), 413


@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("🚀 Starting AI Legal Assistant with FIXED Chatbot")
    print("=" * 60)
    print(f"📁 Upload folder: {Config.UPLOAD_FOLDER}")
    print(f"🔐 Gemini API: {'✅ Configured' if Config.GEMINI_API_KEY else '❌ Not configured'}")
    print(f"🤖 Gemini Model: {getattr(Config, 'GEMINI_MODEL', 'gemini-1.5-flash')}")
    print(f"📊 Embedding Model: {getattr(Config, 'EMBEDDING_MODEL', 'text-embedding-004')}")
    print(f"📄 Document Processor: {'✅' if document_processor else '⚠️ Using fallback'}")
    print(f"🤖 Gemini Analyzer: {'✅' if gemini_analyzer else '⚠️ Not available'}")
    print(
        f"🔗 RAG Pipeline: {'✅ AI-powered with gemini-1.5-flash' if rag_pipeline and getattr(rag_pipeline, 'ai_available', False) else '⚠️ Basic mode'}"
    )
    print(f"🗃️ Vector Store: {'✅' if vector_store else '⚠️ Not available'}")
    print(f"💡 Prompt Generator: {'✅' if prompt_generator else '⚠️ Using fallback'}")
    print("=" * 60)
    print("🔧 Debug endpoints:")
    print("   http://localhost:5000/api/health")
    print("   http://localhost:5000/api/test-ai")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
