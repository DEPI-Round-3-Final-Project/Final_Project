from groq import Groq
import time
import random
from config import GROQ_API_KEY, GROQ_MODEL_NAME


class AIGenerator:
    def __init__(self):
        # Insert the new API key (token) directly here
        self.api_key = GROQ_API_KEY
        self.model_name = GROQ_MODEL_NAME
        self.client = Groq(api_key=self.api_key)
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def _make_api_call_with_retry(self, messages, temperature=None):
        """Make API call with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if temperature is not None:
                    chat_completion = self.client.chat.completions.create(
                        messages=messages,
                        model=self.model_name,
                        temperature=temperature
                    )
                else:
                    chat_completion = self.client.chat.completions.create(
                        messages=messages,
                        model=self.model_name
                    )
                return chat_completion.choices[0].message.content
            except Exception as e:
                if attempt < self.max_retries - 1:
                    # Exponential backoff with jitter
                    delay = self.retry_delay * \
                        (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(delay)
                else:
                    # Last attempt failed, return error message
                    return f"عذراً، حدث خطأ في الاتصال بالخدمة: {str(e)}"

        return None

    def generate_answer(self, question, context):
        """Generate an answer based on the question and context"""
        prompt = f"""بناءً على السياق التالي من كتاب دراسي، أجب عن السؤال بدقة ووضوح. ركز فقط على المعلومات المفيدة في السياق وتجاهل أي أخطاء إملائية أو كلام غير مفهوم.

السياق:
{context}

السؤال: {question}

الإجابة المباشرة:"""

        messages = [{"role": "user", "content": prompt}]
        answer = self._make_api_call_with_retry(messages)

        if answer is None:
            return "عذراً، لم أتمكن من توليد إجابة حالياً. يرجى المحاولة مرة أخرى لاحقاً."

        return answer.strip()

    def generate_summary(self, text):
        """Generate a summary of the text"""
        prompt = f"""لخص النص التالي في نقاط أساسية وواضحة. ركز فقط على المعنى العام وتجاهل الأخطاء الإملائية أو الكلمات المقطوعة.

النص:
{text}

الملخص:"""

        messages = [{"role": "user", "content": prompt}]
        summary = self._make_api_call_with_retry(messages)

        if summary is None:
            return "عذراً، لم أتمكن من توليد ملخص حالياً. يرجى المحاولة مرة أخرى لاحقاً."

        return summary.strip()

    def generate_questions(self, text, num_questions=5):
        """Generate questions based on the text"""
        prompt = f"""ولد {num_questions} أسئلة مهمة بناءً على النص التالي.

النص:
{text}

الأسئلة:"""

        messages = [{"role": "user", "content": prompt}]
        questions = self._make_api_call_with_retry(messages)

        if questions is None:
            return "عذراً، لم أتمكن من توليد أسئلة حالياً. يرجى المحاولة مرة أخرى لاحقاً."

        return questions.strip()
    