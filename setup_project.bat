@echo off
chcp 65001 >nul
echo ====================================
echo 🚀 راه‌اندازی پروژه دستیار حقوقی هوشمند
echo ====================================
echo.

REM ایجاد ساختار پوشه‌ها
echo 📁 ایجاد ساختار پوشه‌ها...

REM پوشه‌های اصلی
mkdir data\raw\policies 2>nul
mkdir data\raw\laws 2>nul
mkdir data\raw\regulations 2>nul
mkdir data\raw\cultural_council 2>nul
mkdir data\raw\science_council 2>nul
mkdir data\raw\ministry_circulars 2>nul
mkdir data\raw\judicial_regulations 2>nul
mkdir data\processed 2>nul
mkdir data\sample 2>nul

REM پوشه‌های کد
mkdir src\core 2>nul
mkdir src\data_processing 2>nul
mkdir src\rag 2>nul
mkdir src\comparison 2>nul
mkdir src\llm 2>nul
mkdir src\utils 2>nul

REM پوشه‌های وب
mkdir web\templates 2>nul
mkdir web\static\css 2>nul
mkdir web\static\js 2>nul
mkdir web\static\images 2>nul
mkdir web\uploads 2>nul

REM پوشه‌های تست
mkdir tests\unit 2>nul
mkdir tests\integration 2>nul
mkdir tests\fixtures 2>nul

REM سایر پوشه‌ها
mkdir scripts 2>nul
mkdir docs 2>nul
mkdir deployment 2>nul
mkdir database\vector_db 2>nul

echo ✅ ساختار پوشه‌ها ایجاد شد
echo.

REM ایجاد فایل‌های __init__.py
echo 📄 ایجاد فایل‌های __init__.py...
echo. > src\__init__.py
echo. > src\core\__init__.py
echo. > src\data_processing\__init__.py
echo. > src\rag\__init__.py
echo. > src\comparison\__init__.py
echo. > src\llm\__init__.py
echo. > src\utils\__init__.py
echo. > tests\__init__.py

echo ✅ فایل‌های __init__.py ایجاد شد
echo.

REM ایجاد فایل‌های gitkeep
echo 📌 ایجاد فایل‌های .gitkeep...
echo. > data\raw\.gitkeep
echo. > data\processed\.gitkeep
echo. > web\uploads\.gitkeep
echo. > database\.gitkeep

REM ایجاد فایل .gitignore
echo 📝 ایجاد فایل .gitignore...
(
echo # Python
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo *.so
echo .Python
echo build/
echo develop-eggs/
echo dist/
echo downloads/
echo eggs/
echo .eggs/
echo lib/
echo lib64/
echo parts/
echo sdist/
echo var/
echo wheels/
echo *.egg-info/
echo .installed.cfg
echo *.egg
echo.
echo # Conda Environment
echo conda-meta/
echo .conda/
echo.
echo # Environment Variables
echo .env
echo .env.local
echo config.ini
echo.
echo # Database
echo *.db
echo *.sqlite3
echo database/legal_assistant.db
echo database/vector_db/
echo.
echo # IDE
echo .vscode/
echo .idea/
echo *.swp
echo *.swo
echo *~
echo.
echo # OS
echo .DS_Store
echo Thumbs.db
echo desktop.ini
echo.
echo # Logs
echo *.log
echo logs/
echo.
echo # Uploads
echo web/uploads/*
echo !web/uploads/.gitkeep
echo.
echo # Cache
echo .pytest_cache/
echo .coverage
echo htmlcov/
echo.
echo # Data files
echo data/raw/*
echo !data/raw/.gitkeep
echo data/processed/*
echo !data/processed/.gitkeep
echo.
echo # Model files
echo models/
echo *.model
echo *.bin
echo *.pkl
echo.
echo # Temporary files
echo temp/
echo tmp/
echo *.tmp
) > .gitignore

REM ایجاد فایل requirements.txt
echo 📦 ایجاد فایل requirements.txt...
(
echo # Core Framework
echo flask==2.3.3
echo flask-cors==4.0.0
echo flask-wtf==1.2.1
echo.
echo # Database ^& Vector Store
echo sqlalchemy==2.0.23
echo chromadb==0.4.15
echo.
echo # LLM ^& AI
echo langchain==0.0.335
echo langchain-community==0.0.38
echo sentence-transformers==2.2.2
echo transformers==4.35.2
echo torch==2.1.1
echo.
echo # Persian Language Processing
echo hazm==0.7.0
echo parsivar==0.2.3
echo.
echo # Document Processing
echo python-docx==0.8.11
echo PyPDF2==3.0.1
echo python-magic-bin==0.4.14
echo.
echo # Text Processing
echo nltk==3.8.1
echo scikit-learn==1.3.2
echo numpy==1.25.2
echo pandas==2.1.3
echo.
echo # Web ^& UI
echo jinja2==3.1.2
echo wtforms==3.1.0
echo.
echo # Utilities
echo python-dotenv==1.0.0
echo requests==2.31.0
echo tqdm==4.66.1
echo pydantic==2.5.0
echo.
echo # Development ^& Testing
echo pytest==7.4.3
echo pytest-flask==1.3.0
echo black==23.11.0
echo flake8==6.1.0
echo.
echo # Optional Local LLM
echo # ollama==0.1.7
echo.
echo # Optional API LLM
echo # openai==1.3.6
echo # anthropic==0.7.8
) > requirements.txt

REM ایجاد فایل .env نمونه
echo 🔧 ایجاد فایل .env.example...
(
echo # API Keys
echo OPENAI_API_KEY=your_openai_api_key_here
echo ANTHROPIC_API_KEY=your_anthropic_api_key_here
echo.
echo # LLM Settings
echo LLM_TYPE=local
echo LOCAL_LLM_MODEL=llama2
echo.
echo # Database Settings
echo DATABASE_URL=sqlite:///database/legal_assistant.db
echo VECTOR_DB_PATH=database/vector_db
echo.
echo # Flask Settings
echo FLASK_ENV=development
echo FLASK_DEBUG=True
echo SECRET_KEY=your_secret_key_here
echo.
echo # Application Settings
echo MAX_UPLOAD_SIZE=16777216
echo CHUNK_SIZE=1000
echo CHUNK_OVERLAP=200
) > .env.example

echo ====================================
echo ✅ راه‌اندازی پروژه تکمیل شد!
echo ====================================