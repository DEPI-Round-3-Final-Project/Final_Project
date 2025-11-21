import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import pickle
import os


class TextClassifier:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.classes = ['question', 'add_task', 'greeting', 'other']

        # Attempt to load the pre-trained model
        self._load_model()

        # If the model does not exist, create a simple model
        if self.model is None:
            self._create_simple_model()

    def _load_model(self):
        """Load the pre-trained model if it exists"""
        model_path = 'text_classifier_model.pkl'
        vectorizer_path = 'text_vectorizer.pkl'

        if os.path.exists(model_path) and os.path.exists(vectorizer_path):
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            with open(vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)

    def _create_simple_model(self):
        """Create a simple rule-based model"""
        # In a real application, the model should be trained on a dataset
        self.model = 'rule_based'

    def _normalize_arabic(self, text):
        """Normalize Arabic text for easier comparison"""
        # Remove diacritics
        text = re.sub(r'[\u064B-\u0652]', '', text)
        # Normalize Alif character
        text = re.sub(r'[أإآ]', 'ا', text)
        # Normalize Taa Marbuta
        text = re.sub(r'ة', 'ه', text)
        return text

    def classify(self, text):
        """Classify the text to determine its purpose"""
        if self.model == 'rule_based':
            return self._classify_by_rules(text)
        else:
            # Use the trained model
            text_vector = self.vectorizer.transform([text])
            prediction = self.model.predict(text_vector)[0]
            return prediction

    def _classify_by_rules(self, text):
        """Classify the text based on enhanced rules"""
        text_lower = text.lower()
        # Apply text normalization function
        normalized_text = self._normalize_arabic(text_lower)

        # Keywords for questions
        question_keywords = ['ما هو', 'ما هي', 'متى', 'اين',
                             'كيف', 'لماذا', 'اشرح', 'عرف', 'قارن', 'اذكر', 'سوال',
                             'عندى', 'كويز', 'اختبار', 'امتحان']

        # Keywords for tasks
        task_keywords = ['مهمة', 'واجب', 'دراسة', 'مراجعة',
                         'اختبار', 'امتحان', 'حل', 'انجاز', 'ذاكر',
                         'بكره', 'الساعه', 'بليل']

        # Keywords for greetings (expanded list)
        greeting_keywords = [
            'مرحبا', 'اهلا', 'أهلا', 'السلام', 'مساء', 'صباح', 'تحية',
            'ابدا', 'ابدأ', 'start', 'هلا', 'هاي', 'السلام عليكم', 'وعليكم السلام'
        ]

        # --- New step: Check for subject keywords ---
        subject_keywords = ['احياء', 'عربي', 'لغة عربية', 'ديوان', 'تلخيص']
        for keyword in subject_keywords:
            if keyword in normalized_text:
                return 'question'

        # Check for greetings first
        for keyword in greeting_keywords:
            if keyword in text_lower or keyword in normalized_text:
                return 'greeting'

        # Check for questions
        for keyword in question_keywords:
            if keyword in text_lower or keyword in normalized_text:
                return 'question'

        # Check for tasks
        for keyword in task_keywords:
            if keyword in text_lower or keyword in normalized_text:
                return 'add_task'

        # If nothing is found, return 'other'
        return 'other'
    