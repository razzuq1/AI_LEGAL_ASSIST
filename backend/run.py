#!/usr/bin/env python3
"""
AI Legal Assistant - Enhanced Version
Run this file to start the application
"""

import os
import sys
from pathlib import Path


def setup_directories():
    """Create necessary directories"""
    base_dir = Path(__file__).parent
    directories = [base_dir / 'data' / 'uploads', base_dir / 'data' / 'vector_store', base_dir / 'utils']

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    # Create __init__.py for utils package
    init_file = base_dir / 'utils' / '__init__.py'
    if not init_file.exists():
        init_file.touch()


def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'flask',
        'flask_cors',
        'google.generativeai',
        'PyPDF2',
        'docx',
        'sentence_transformers',
        'faiss',
        'langchain',
        'numpy',
    ]

    missing = []
    for package in required_packages:
        try:
            if package == 'docx':
                __import__('docx')
            elif package == 'google.generativeai':
                __import__('google.generativeai')
            else:
                __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)

    if missing:
        print("❌ Missing required packages:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n💡 Install missing packages with:")
        print("   pip install -r requirements.txt")
        return False
    return True


def main():
    """Main function to run the application"""
    print("🚀 AI Legal Assistant - Enhanced Version")
    print("=" * 50)

    # Setup directories
    setup_directories()
    print("✅ Directories created")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    print("✅ Dependencies verified")

    # Check environment variables
    from dotenv import load_dotenv

    load_dotenv()

    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key:
        print("✅ Gemini API key configured")
    else:
        print("⚠️  Warning: No Gemini API key found in .env file")
        print("   Limited functionality without AI API key")

    print("=" * 50)

    # Import and run app
    try:
        from app import app

        print("🌐 Starting server at http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
