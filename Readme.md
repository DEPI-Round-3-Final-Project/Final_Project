# 🎓 Smart Study Assistant - AI-Powered Telegram Bot

## 📖 Overview

An intelligent Arabic study assistant Telegram bot that helps students with their coursework through AI-powered question answering, summarization, quiz generation, and task management. The bot specializes in Biology and Arabic Language subjects for secondary education.

## ✨ Key Features

### 🤖 AI-Powered Learning
- **Smart Q&A**: Ask questions about your subjects and get accurate answers from textbook content
- **Intelligent Summarization**: Generate concise summaries of any topic
- **Quiz Generation**: Create practice quizzes with multiple-choice questions
- **Context-Aware Responses**: Uses RAG (Retrieval-Augmented Generation) for accurate answers

### 📚 Supported Subjects
- Biology (الأحياء) 🧬
- Arabic Language (اللغة العربية) 📖

### ✅ Task Management
- Create and track study tasks
- Set priorities (low, medium, high)
- Mark tasks as completed
- View pending and completed tasks

### ⏰ Smart Reminders
- Morning reminders (8:00 AM)
- Evening review reminders (6:00 PM)
- Upcoming task notifications
- Daily task summaries

### 📊 Progress Tracking
- Questions asked counter
- Summaries generated
- Quizzes taken
- Tasks completed statistics

## 🏗️ System Architecture

### Core Components

```
┌─────────────────────────────────────────┐
│         Telegram Bot Interface          │
│     (telegram_bot.py, text_classifier)  │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌─────────────┐  ┌─────────────┐
│   RAG       │  │  Database   │
│   System    │  │  Manager    │
└──────┬──────┘  └──────┬──────┘
       │                │
       ▼                ▼
┌─────────────┐  ┌─────────────┐
│AI Generator │  │  Reminder   │
│ (Groq API)  │  │  System     │
└─────────────┘  └─────────────┘
```

### Technology Stack

**AI & Machine Learning:**
- Sentence Transformers (paraphrase-multilingual-mpnet-base-v2)
- FAISS for vector similarity search
- Groq API (GPT-OSS-120B model)
- scikit-learn for text classification

**Document Processing:**
- PyMuPDF (fitz) for PDF extraction
- Pytesseract for OCR
- PIL for image processing
- Arabic text support (arabic-reshaper, python-bidi)

**Backend:**
- Python 3.8+
- SQLite database
- APScheduler for task scheduling
- python-telegram-bot for bot interface

## 📦 Installation

### Prerequisites

1. **Python 3.8 or higher**
2. **Tesseract OCR** (for PDF text extraction)
   - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - Linux: `sudo apt-get install tesseract-ocr tesseract-ocr-ara`
   - Mac: `brew install tesseract tesseract-lang`

3. **API Keys**
   - Telegram Bot Token (get from [@BotFather](https://t.me/botfather))
   - Groq API Key (get from [Groq Console](https://console.groq.com))

### Step-by-Step Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd smart-study-assistant
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**

Create a `.env` file or set environment variables:
```bash
export TELEGRAM_TOKEN="your_telegram_bot_token"
export GROQ_API_KEY="your_groq_api_key"
```

Or edit `config.py` directly (not recommended for production):
```python
TELEGRAM_TOKEN = "your_telegram_bot_token"
GROQ_API_KEY = "your_groq_api_key"
```

4. **Update Tesseract path** (Windows only)

Edit `data_extractor.py`, line 8:
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

5. **Prepare PDF textbooks**

Place your PDF files in the `pdfs/` directory:
- `biology.pdf` - Biology textbook
- `arabic.pdf` - Arabic language textbook

6. **Initialize the system**
```bash
python main.py
```

First run will:
- Create directory structure
- Extract text from PDFs
- Build FAISS index
- Initialize database
- Cache embeddings for faster subsequent runs

## 🚀 Usage

### Starting the Bot

```bash
python main.py
```

You should see:
```
✅ Loaded X text chunks into RAG system
⏰ Reminder system activated
✅ Bot is running with all features!
```

### Telegram Commands

**Basic Commands:**
- `/start` - Initialize bot and show main menu

**Main Menu Options:**
- 📚 Biology - Access biology subject features
- 📖 Arabic - Access Arabic language features  
- ✅ Add Task - Create a new study task
- 📋 My Tasks - View and manage tasks
- 📊 My Statistics - View learning progress

**Subject-Specific Features:**
- ❓ Ask Question - Get answers from textbook content
- 📚 Get Summary - Generate topic summaries
- 🎯 Take Quiz - Practice with generated quizzes

### Example Interactions

**Asking a Question:**
```
User: ما هو التكاثر الخلوي؟
Bot: [Provides detailed answer with sources]
```

**Getting a Summary:**
```
User: Choose Biology → Get Summary
User: التكاثر
Bot: [Generates comprehensive summary]
```

**Taking a Quiz:**
```
User: Choose Biology → Take Quiz
User: الخلية
Bot: [Generates 5 MCQ questions with explanations]
```

## 📁 Project Structure

```
smart-study-assistant/
│
├── main.py                    # Application entry point
├── config.py                  # Configuration settings
├── requirements.txt           # Python dependencies
│
├── 🗄️ Database Layer
│   └── database_manager.py    # SQLite operations
│
├── 📄 Data Processing
│   ├── data_extractor.py      # PDF extraction with OCR
│   ├── text_preprocessor.py   # Text cleaning & chunking
│   └── data_loader.py         # Data loading utilities
│
├── 🤖 AI Components
│   ├── rag_system.py          # RAG implementation
│   ├── ai_generator.py        # Groq API integration
│   └── quiz_generator.py      # Quiz generation
│
├── 💬 Bot Interface
│   ├── telegram_bot.py        # Main bot logic
│   ├── text_classifier.py     # Intent classification
│   └── reminder_system.py     # Scheduled reminders
│
├── 📚 Data Directories
│   ├── pdfs/                  # Input PDF textbooks
│   ├── extracted_texts/       # Extracted text cache
│   └── rag_cache/            # FAISS index & embeddings
│
└── 🗃️ Database
    └── study_assistant.db     # SQLite database
```

## 🔧 Configuration

### Key Settings in `config.py`

```python
# Database
DATABASE_PATH = "study_assistant.db"

# AI Models
GROQ_MODEL_NAME = "openai/gpt-oss-120b"
BERT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# RAG Settings
CHUNK_SIZE = 1000              # Text chunk size
CHUNK_OVERLAP = 100            # Overlap between chunks
TOP_K_RESULTS = 5              # Number of results to retrieve

# Directories
PDF_DIRECTORY = "pdfs"
EXTRACTED_TEXT_DIRECTORY = "extracted_texts"
```

## 🗄️ Database Schema

### Tables

**users**
- user_id (PRIMARY KEY)
- username
- first_name
- last_name
- registration_date

**tasks**
- id (PRIMARY KEY)
- user_id (FOREIGN KEY)
- task_name
- due_date
- priority (1=low, 2=medium, 3=high)
- status (pending/completed)
- created_at
- completed_at

**textbook_content**
- id (PRIMARY KEY)
- subject (biology/arabic)
- grade_level
- chapter
- content (text chunk)
- page_number
- content_type

**user_stats**
- user_id (PRIMARY KEY)
- questions_asked
- summaries_generated
- quizzes_taken
- tasks_completed
- last_active

## 🤖 RAG System Details

### How It Works

1. **Document Processing**
   - PDFs are extracted page-by-page
   - Text is cleaned and normalized for Arabic
   - Content is chunked into 800-character segments with 100-character overlap

2. **Embedding Generation**
   - Uses multilingual Sentence Transformers model
   - Supports 50+ languages including Arabic
   - Embeddings are cached for performance

3. **Vector Search**
   - FAISS IndexFlatIP for inner product similarity
   - L2 normalization for cosine similarity
   - Quality filtering with minimum score threshold

4. **Answer Generation**
   - Top-K relevant chunks retrieved (default: 5)
   - Context passed to Groq API
   - Subject-specific filtering ensures accuracy

### Quality Mechanisms

- **Relevance Scoring**: Minimum similarity threshold of 0.4
- **Subject Filtering**: Ensures answers come from correct subject
- **Keyword Matching**: Validates presence of query terms
- **Length Validation**: Filters very short or very long chunks
- **Diversity Scoring**: Checks content variety

## 🧪 Testing

### Test Groq API Connection
```bash
python test_groq.py
```

Expected output:
```
✅ Connection successful! Groq response:
مرحباً
```

### Verify Database
After first run, check that `study_assistant.db` exists and contains data:
```bash
python -c "from database_manager import DatabaseManager; db = DatabaseManager(); print(len(db.get_textbook_content('biology')), 'biology chunks')"
```

## ⏰ Reminder System

The bot includes an automated reminder system:

- **8:00 AM**: Morning greeting with pending tasks
- **6:00 PM**: Evening review reminder
- **Hourly**: Check for upcoming tasks (next day)

Reminders use Cairo timezone (Africa/Cairo) by default. Modify in `reminder_system.py` to change timezone.

## 📊 Performance Optimization

### Caching Strategy

The system implements aggressive caching:

1. **Embedding Cache**: Stores computed embeddings on disk
2. **FAISS Index**: Saved to `rag_cache/faiss_index.bin`
3. **Text Chunks**: Pickled in `rag_cache/texts.pkl`
4. **Metadata**: Cached in `rag_cache/metadata.pkl`

**First Run**: 2-5 minutes (building index)  
**Subsequent Runs**: 5-10 seconds (loading cache)

### To Clear Cache

```bash
rm -rf rag_cache/
```

Next run will rebuild the index.

## 🛠️ Troubleshooting

### Common Issues

**1. "Tesseract not found"**
- Install Tesseract OCR
- Update path in `data_extractor.py`

**2. "GROQ_API_KEY not found"**
- Set environment variable or update `config.py`
- Verify API key is valid at [Groq Console](https://console.groq.com)

**3. "No context found for question"**
- Ensure PDFs are in `pdfs/` directory
- Check PDFs contain text (not just images)
- Try different phrasing of question

**4. "Module not found"**
- Run `pip install -r requirements.txt`
- Ensure Python 3.8+ is being used

**5. Database errors**
- Delete `study_assistant.db` and restart
- Check file permissions

## 🔒 Security Considerations

**Production Deployment:**
1. Never commit API keys to version control
2. Use environment variables for sensitive data
3. Implement rate limiting for API calls
4. Add user authentication if needed
5. Regular database backups
6. Monitor API usage and costs

## 📈 Future Enhancements

- [ ] Support for additional subjects
- [ ] Voice message support
- [ ] Image-based question answering
- [ ] Spaced repetition system
- [ ] Study group features
- [ ] Progress analytics dashboard
- [ ] Multi-language interface
- [ ] Mobile app integration

## 🙏 Acknowledgments

- Groq for powerful AI inference
- Sentence Transformers for multilingual embeddings
- Telegram for bot API
- Open source community for libraries

