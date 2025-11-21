import re
import unicodedata


class TextPreprocessor:
    def __init__(self):
        # Basic Arabic stop words list
        self.arabic_stopwords = {
            'في', 'من', 'إلى', 'على', 'هذا', 'هذه', 'ذلك', 'التي',
            'الذي', 'التى', 'هو', 'هي', 'أن', 'إن', 'كان', 'يكون'
        }

    def clean_text(self, text):
        """Comprehensive text cleaning"""
        if not text:
            return ""

        # Unicode normalization
        text = unicodedata.normalize('NFKC', text)

        # Remove diacritics
        text = re.sub(r'[\u064B-\u0652\u0640]', '', text)

        # Normalize characters
        text = re.sub(r'[إأآا]', 'ا', text)
        text = re.sub(r'[ىي]', 'ي', text)
        text = re.sub(r'ة', 'ه', text)

        # Remove unwanted characters
        text = re.sub(
            r'[^\u0600-\u06FF\u0750-\u077Fa-zA-Z0-9\s\.\,\:\?\!\-\(\)\n]',
            ' ',
            text
        )

        # Clean up spacing
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)

        return text.strip()

    def preprocess_text(self, text):
        """Complete text processing"""
        # Basic cleaning
        text = self.clean_text(text)

        # Split into lines
        lines = text.split('\n')
        clean_lines = []

        for line in lines:
            line = line.strip()

            # Skip short lines
            if len(line) < 15:
                continue

            # Skip lines full of numbers
            if sum(c.isdigit() for c in line) / max(len(line), 1) > 0.5:
                continue

            clean_lines.append(line)

        return '\n'.join(clean_lines)

    def chunk_text(self, text, chunk_size=1000, overlap=100):
        """
        Split text into chunks suitable for RAG

        Smart strategy:
        - Try to split at the end of sentences
        - Retain overlap for context
        """
        if not text or len(text) < chunk_size:
            yield text
            return

        # Split text into sentences
        sentences = re.split(r'[.!؟\n]+', text)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_length = len(sentence)

            # If a single sentence is larger than chunk_size
            if sentence_length > chunk_size:
                # Split it using the simple method
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_length = 0

                for i in range(0, sentence_length, chunk_size - overlap):
                    chunks.append(sentence[i:i + chunk_size])
                continue

            # If adding the sentence makes the chunk too large
            if current_length + sentence_length > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))

                # Keep the last sentence for overlap
                if len(current_chunk) > 1:
                    current_chunk = [current_chunk[-1], sentence]
                    current_length = len(current_chunk[-1]) + sentence_length
                else:
                    current_chunk = [sentence]
                    current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        # Add the last chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        # Return the chunks
        for chunk in chunks:
            chunk = chunk.strip()
            if len(chunk) > 50:  # Only meaningful chunks
                yield chunk

    def extract_keywords(self, text, top_n=5):
        """Extract keywords"""
        # Clean
        text = self.clean_text(text)

        # Extract words
        words = re.findall(r'[\u0600-\u06FF]+', text.lower())

        # Filter stop words
        words = [
            w for w in words if w not in self.arabic_stopwords and len(w) > 3]

        # Calculate frequency
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(
            word_freq.items(), key=lambda x: x[1], reverse=True)

        return [word for word, freq in sorted_words[:top_n]]

    def is_meaningful_text(self, text):
        """Check if the text is meaningful"""
        if not text or len(text) < 50:
            return False

        # Calculate Arabic character ratio
        arabic = len(re.findall(r'[\u0600-\u06FF]', text))
        total = len(re.sub(r'\s', '', text))

        if total == 0:
            return False

        return arabic / total > 0.3
    