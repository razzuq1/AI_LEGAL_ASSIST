#!/usr/bin/env python3
"""
Setup script for AI Legal Assistant
Handles installation and configuration
"""

import os
import subprocess
import sys
from pathlib import Path


def create_directory_structure():
    """Create necessary directories"""
    base_dir = Path(__file__).parent
    directories = [base_dir / 'data' / 'uploads', base_dir / 'data' / 'vector_store', base_dir / 'utils']

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

    # Create __init__.py for utils package
    init_file = base_dir / 'utils' / '__init__.py'
    if not init_file.exists():
        init_file.touch()
        print("✅ Created utils/__init__.py")


def install_requirements():
    """Install Python packages"""
    requirements_file = Path(__file__).parent / 'requirements.txt'

    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False

    try:
        print("📦 Installing Python packages...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)])
        print("✅ All packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Package installation failed: {e}")
        return False


def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path(__file__).parent / '.env'

    if env_file.exists():
        print("✅ .env file already exists")
        return True

    env_content = """# AI API Configuration
GEMINI_API_KEY=AIzaSyCpGo9qtU9Gz2qfc5Rnh-BNbJ-UGlulKbI

# Flask Configuration
SECRET_KEY=Fathi98843
FLASK_ENV=development
FLASK_DEBUG=1

# Optional: OpenAI as fallback (if you have it)
# OPENAI_API_KEY=your_openai_key_here
"""

    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with default configuration")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False

    print(f"✅ Python version OK: {sys.version}")
    return True


def test_imports():
    """Test if key packages can be imported"""
    test_packages = [
        ('flask', 'Flask'),
        ('google.generativeai', 'Gemini AI'),
        ('PyPDF2', 'PDF processing'),
        ('docx', 'Word document processing'),
        ('sentence_transformers', 'Text embeddings'),
        ('faiss', 'Vector search'),
    ]

    failed = []
    for package, description in test_packages:
        try:
            if package == 'docx':
                import docx
            elif package == 'google.generativeai':
                import google.generativeai
            else:
                __import__(package)
            print(f"✅ {description}: OK")
        except ImportError:
            print(f"❌ {description}: Failed")
            failed.append(package)

    return len(failed) == 0


def main():
    """Main setup function"""
    print("🚀 AI Legal Assistant Setup")
    print("=" * 40)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Create directories
    create_directory_structure()

    # Create .env file
    create_env_file()

    # Install packages
    if not install_requirements():
        print("\n💡 Try installing packages manually:")
        print("   pip install flask flask-cors python-dotenv")
        print("   pip install google-generativeai PyPDF2 python-docx")
        print("   pip install sentence-transformers faiss-cpu")
        sys.exit(1)

    # Test imports
    print("\n🧪 Testing package imports...")
    if not test_imports():
        print("\n❌ Some packages failed to import")
        print("💡 Try reinstalling failed packages")
        sys.exit(1)

    print("\n" + "=" * 40)
    print("✅ Setup completed successfully!")
    print("\n🏃 Ready to run:")
    print("   python run.py")
    print("\n🌐 Then open: http://localhost:5000")
    print("\n📝 Note: Update your Gemini API key in .env file if needed")


if __name__ == '__main__':
    main()
