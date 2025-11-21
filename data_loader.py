import os
import json
from database_manager import DatabaseManager
from text_preprocessor import TextPreprocessor

class DataLoader:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.preprocessor = TextPreprocessor()
    
    def load_from_json(self, json_file):
        """Load data from a JSON file"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for subject in data:
            for chapter in data[subject]:
                for content in data[subject][chapter]:
                    # Clean the content
                    cleaned_content = self.preprocessor.preprocess_text(content['text'])
                    
                    # Save to database
                    self.db_manager.add_textbook_content(
                        subject,
                        content.get('grade_level', 'secondary'),
                        chapter,
                        cleaned_content,
                        content.get('page_number', 0),
                        content.get('content_type', 'text')
                    )
    
    def load_from_txt(self, txt_file, subject, chapter_name="Chapter 1"):
        """Load data from a text file"""
        with open(txt_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Split the text into chunks
        chunks = self.preprocessor.chunk_text(text)
        
        # Save the chunks to the database
        for i, chunk in enumerate(chunks):
            cleaned_chunk = self.preprocessor.preprocess_text(chunk)
            
            self.db_manager.add_textbook_content(
                subject,
                "secondary",
                chapter_name,
                cleaned_chunk,
                i + 1,
                "text"
            )
            