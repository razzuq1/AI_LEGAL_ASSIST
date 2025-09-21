import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-legal-assistant-2024'

    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}

    # AI settings with CORRECT model names
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GEMINI_MODEL = 'gemini-1.5-flash'  # CORRECTED MODEL NAME
    EMBEDDING_MODEL = 'text-embedding-004'  # CORRECTED EMBEDDING MODEL

    # Document processing settings
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    # Vector store settings
    VECTOR_STORE_PATH = os.path.join(os.getcwd(), 'data', 'vector_store')

    # Analysis settings
    MAX_TOKENS = 2000
    TEMPERATURE = 0.1

    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(os.path.join(os.getcwd(), 'data'), exist_ok=True)
        os.makedirs(Config.VECTOR_STORE_PATH, exist_ok=True)
