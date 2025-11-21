import os

# Database settings
DATABASE_PATH = "study_assistant.db"

# Telegram bot settings
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN_HERE")

# AI model settings
BERT_MODEL_NAME = "asafaya/bert-base-arabic"
GPT_MODEL_NAME = "aubmindlab/aragpt2-base"

# Groq API settings
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")
GROQ_MODEL_NAME = "openai/gpt-oss-120b"

# RAG system settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
TOP_K_RESULTS = 5

# Text processing settings
MIN_TEXT_LENGTH = 50
MAX_TEXT_LENGTH = 1000

# File paths
PDF_DIRECTORY = "pdfs"
EXTRACTED_TEXT_DIRECTORY = "extracted_texts"