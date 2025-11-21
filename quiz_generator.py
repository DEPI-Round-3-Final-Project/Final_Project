from groq import Groq
import json
import re
import time
import random
from config import GROQ_API_KEY, GROQ_MODEL_NAME


class QuizGenerator:
    """
    🆕 Multiple Choice Question (MCQ) generation system

    Features:
    - Automatic MCQ generation
    - 4 options per question
    - Automatic correction
    - Save results
    """

    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.model_name = GROQ_MODEL_NAME
        self.client = Groq(api_key=self.api_key)
        self.max_retries = 3
        self.retry_delay = 2  # seconds

        # Store active quizzes
        self.active_quizzes = {}

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

    def generate_structured_quiz(self, context, num_questions=5):
        """Generate a structured quiz with genuine questions"""
        prompt = f"""
    أنت معلم محترف في المواد الدراسية. قم بإنشاء {num_questions} أسئلة اختيار من متعدد بناءً على النص التالي.
    
    النص:
    {context}
    
    المتطلبات:
    1. كل سؤال يجب أن يكون واضحاً ومباشراً
    2. 4 خيارات لكل سؤال (أ، ب، ج، د)
    3. إجابة واحدة صحيحة فقط
    4. شرح مختصر للإجابة الصحيحة
    5. الأسئلة يجب أن تغطي نقاطاً مهمة من النص
    
    أرجع النتيجة كـ JSON فقط بهذا الشكل:
    [
      {{
        "question": "نص السؤال هنا؟",
        "options": {{
          "أ": "الخيار الأول",
          "ب": "الخيار الثاني", 
          "ج": "الخيار الثالث",
          "د": "الخيار الرابع"
        }},
        "correct_answer": "أ",
        "explanation": "شرح الإجابة الصحيحة"
      }}
    ]
    
    لا تكتب أي نص إضافي قبل أو بعد الـ JSON.
    ابدأ مباشرة بـ [ 
    """

        messages = [{"role": "user", "content": prompt}]
        response = self._make_api_call_with_retry(messages, temperature=0.7)

        if response is None:
            return self._generate_fallback_quiz()

        response = self._clean_json_response(response)

        try:
            questions = json.loads(response)
            return questions
        except json.JSONDecodeError:
            # If JSON parsing fails, return fallback quiz
            return self._generate_fallback_quiz()

    def _clean_json_response(self, response):
        """Clean the JSON response from any additional text"""
        # Remove any text before [
        if '[' in response:
            response = '[' + response.split('[', 1)[1]

        # Remove any text after ]
        if ']' in response:
            response = response.split(']', 1)[0] + ']'

        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)

        return response.strip()

    def _generate_fallback_quiz(self):
        """Generate a fallback quiz in case of failure"""
        return [
            {
                "question": "هذا سؤال تجريبي. ما هي أهمية المراجعة المنتظمة؟",
                "options": {
                    "أ": "تساعد على تثبيت المعلومات",
                    "ب": "تضيع الوقت",
                    "ج": "غير مهمة",
                    "د": "فقط للامتحانات"
                },
                "correct_answer": "أ",
                "explanation": "المراجعة المنتظمة تساعد على تثبيت المعلومات في الذاكرة طويلة المدى"
            }
        ]

    def format_quiz_for_telegram(self, questions, quiz_id=None):
        """
        Format questions for display in Telegram

        Args:
            questions: List of questions
            quiz_id: Quiz identifier (optional)

        Returns:
            Formatted text for display
        """
        if not questions:
            return "❌ عذراً، فشل توليد الأسئلة"

        formatted_text = "🎯 **اختبار تدريبي**\n\n"

        for i, q in enumerate(questions, 1):
            formatted_text += f"**السؤال {i}:**\n"
            formatted_text += f"{q['question']}\n\n"

            for key, value in q['options'].items():
                formatted_text += f"{key}) {value}\n"

            formatted_text += "\n"

        if quiz_id:
            formatted_text += f"\n📝 للإجابة، أرسل: `إجابة_{quiz_id}_1أ_2ب_3ج...`\n"
        else:
            formatted_text += "\n💡 **نصيحة:** فكر جيداً قبل الإجابة!\n"

        return formatted_text

    def format_quiz_with_answers(self, questions):
        """
        Format questions with correct answers

        Args:
            questions: List of questions

        Returns:
            Formatted text containing questions and answers
        """
        if not questions:
            return "❌ عذراً، لا توجد أسئلة"

        formatted_text = "✅ **الإجابات الصحيحة:**\n\n"

        for i, q in enumerate(questions, 1):
            formatted_text += f"**السؤال {i}:**\n"
            formatted_text += f"{q['question']}\n\n"

            for key, value in q['options'].items():
                if key == q['correct_answer']:
                    formatted_text += f"✅ **{key}) {value}**\n"
                else:
                    formatted_text += f"   {key}) {value}\n"

            formatted_text += f"\n💡 **الشرح:** {q['explanation']}\n\n"

        return formatted_text

    def check_answer(self, question_index, user_answer, questions):
        """
        Check the user's answer

        Args:
            question_index: Question number (from 0)
            user_answer: User's answer (A, B, C, D)
            questions: List of questions

        Returns:
            dict with result and explanation
        """
        if question_index >= len(questions):
            return {
                "correct": False,
                "message": "رقم السؤال غير صحيح"
            }

        question = questions[question_index]
        correct_answer = question['correct_answer']

        is_correct = user_answer.strip() == correct_answer

        return {
            "correct": is_correct,
            "correct_answer": correct_answer,
            "explanation": question['explanation'],
            "message": "✅ إجابة صحيحة!" if is_correct else "❌ إجابة خاطئة"
        }

    def calculate_score(self, user_answers, questions):
        """
        Calculate the total score

        Args:
            user_answers: List of user answers
            questions: List of questions

        Returns:
            dict with score and percentage
        """
        if len(user_answers) != len(questions):
            return {
                "score": 0,
                "total": len(questions),
                "percentage": 0,
                "message": "عدد الإجابات غير مطابق لعدد الأسئلة"
            }

        correct_count = 0

        for i, user_answer in enumerate(user_answers):
            if user_answer.strip() == questions[i]['correct_answer']:
                correct_count += 1

        percentage = (correct_count / len(questions)) * 100

        # Determine the grade
        if percentage >= 90:
            grade = "ممتاز جداً! 🌟"
        elif percentage >= 80:
            grade = "ممتاز! 🎉"
        elif percentage >= 70:
            grade = "جيد جداً! 👏"
        elif percentage >= 60:
            grade = "جيد! 👍"
        else:
            grade = "يحتاج تحسين 📚"

        return {
            "score": correct_count,
            "total": len(questions),
            "percentage": percentage,
            "grade": grade,
            "message": f"حصلت على {correct_count}/{len(questions)} ({percentage:.0f}%) - {grade}"
        }

    def save_quiz(self, user_id, quiz_id, questions):
        """Save an active quiz"""
        self.active_quizzes[f"{user_id}_{quiz_id}"] = questions

    def get_quiz(self, user_id, quiz_id):
        """Retrieve an active quiz"""
        return self.active_quizzes.get(f"{user_id}_{quiz_id}")

    def clear_quiz(self, user_id, quiz_id):
        """Delete a quiz after completion"""
        key = f"{user_id}_{quiz_id}"
        if key in self.active_quizzes:
            del self.active_quizzes[key]
            