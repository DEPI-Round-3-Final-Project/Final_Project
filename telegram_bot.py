import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from telegram.ext.dispatcher import Dispatcher
from telegram.error import TelegramError
from database_manager import DatabaseManager
from rag_system import RAGSystem
from ai_generator import AIGenerator
from text_classifier import TextClassifier

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


class StudyAssistantBot:
    def __init__(self, token):
        self.token = token
        self.db_manager = DatabaseManager()
        self.rag_system = RAGSystem()
        self.ai_generator = AIGenerator()
        self.text_classifier = TextClassifier()
        self._initialize_rag_system()

        self.updater = Updater(self.token, use_context=True)
        self.dispatcher = self.updater.dispatcher

        self.dispatcher.add_error_handler(self.error_handler)

    def _initialize_rag_system(self):
        """Initialize the RAG system with content from the database"""
        biology_content = self.db_manager.get_textbook_content("biology")
        arabic_content = self.db_manager.get_textbook_content("arabic")

        all_texts = []
        all_metadata = []

        for chapter, content, page in biology_content:
            all_texts.append(content)
            all_metadata.append({
                "subject": "biology",
                "chapter": chapter,
                "page": page
            })

        for chapter, content, page in arabic_content:
            all_texts.append(content)
            all_metadata.append({
                "subject": "arabic",
                "chapter": chapter,
                "page": page
            })

        if all_texts:
            self.rag_system.build_index(all_texts, all_metadata)
            print(f"✅ تم تحميل {len(all_texts)} قطعة نصية في نظام RAG")

    def error_handler(self, update: Update, context: CallbackContext, error: TelegramError):
        """Error handler"""
        logger.error(f"Error {error} occurred while handling update {update}")

        try:
            if update and update.effective_chat:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ حدث خطأ. يرجى المحاولة مرة أخرى."
                )
        except Exception as e:
            logger.error(f"Error in error handler: {e}")

    def _get_main_menu_keyboard(self):
        """Enhanced main menu keyboard with icons"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "📚 أحياء", callback_data='subject_biology'),
                InlineKeyboardButton("📖 عربي", callback_data='subject_arabic')
            ],
            [
                InlineKeyboardButton("✅ إضافة مهمة", callback_data='add_task'),
                InlineKeyboardButton("📋 مهامي", callback_data='show_tasks')
            ],
            [
                InlineKeyboardButton("📊 إحصائياتي", callback_data='show_stats')
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    def _get_subject_menu_keyboard(self, subject):
        """Special menu for each subject"""
        subject_name = "الأحياء 🧬" if subject == "biology" else "اللغة العربية 📝"

        keyboard = [
            [InlineKeyboardButton(f"❓ سؤال في {subject_name}",
                                     callback_data=f'ask_{subject}')],
            [InlineKeyboardButton(f"📚 ملخص من {subject_name}",
                                     callback_data=f'summary_{subject}')],
            [InlineKeyboardButton(f"🎯 اختبار في {subject_name}",
                                     callback_data=f'quiz_{subject}')],
            [InlineKeyboardButton("🔙 القائمة الرئيسية",
                                     callback_data='main_menu')]
        ]
        return InlineKeyboardMarkup(keyboard)

    def _get_back_button(self):
        """Back button"""
        keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية",
                                             callback_data='main_menu')]]
        return InlineKeyboardMarkup(keyboard)

    def _send_welcome_message(self, update: Update):
        """Enhanced welcome message"""
        user = update.effective_user
        self.db_manager.add_user(
            user.id,
            user.username,
            user.first_name,
            user.last_name
        )

        welcome_text = f"""🎓 أهلاً {user.first_name}!

أنا مساعدك الدراسي الذكي 🤖

📚 المواد المتاحة:
• الأحياء 🧬
• اللغة العربية 📝

✨ ما يمكنني مساعدتك به:
✅ الإجابة على أسئلتك
✅ تلخيص المواضيع
✅ إنشاء اختبارات تدريبية
✅ إدارة مهامك الدراسية

اختر ما تريد من القائمة أدناه 👇"""

        reply_markup = self._get_main_menu_keyboard()

        if update.message:
            update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup
            )

    def start(self, update: Update, context: CallbackContext) -> None:
        """Handle /start command"""
        self._send_welcome_message(update)

    def button(self, update: Update, context: CallbackContext) -> None:
        """Handle button presses - enhanced"""
        query = update.callback_query
        query.answer()

        # Main menu
        if query.data == 'main_menu':
            welcome_text = """🎓 القائمة الرئيسية

اختر ما تريد من الخيارات أدناه 👇"""
            query.message.reply_text(
                text=welcome_text,
                reply_markup=self._get_main_menu_keyboard()
            )

        # Subject selection
        elif query.data == 'subject_biology':
            query.message.reply_text(
                text="📚 مادة الأحياء 🧬\n\nماذا تريد أن تفعل؟",
                reply_markup=self._get_subject_menu_keyboard('biology')
            )

        elif query.data == 'subject_arabic':
            query.message.reply_text(
                text="📖 مادة اللغة العربية 📝\n\nماذا تريد أن تفعل؟",
                reply_markup=self._get_subject_menu_keyboard('arabic')
            )

        # Question in a specific subject
        elif query.data.startswith('ask_'):
            subject = query.data.split('_')[1]
            subject_name = "الأحياء" if subject == "biology" else "اللغة العربية"

            query.message.reply_text(
                text=f"❓ اكتب سؤالك في مادة {subject_name}:",
                reply_markup=self._get_back_button()
            )
            context.user_data['action'] = 'ask_question'
            context.user_data['subject'] = subject

        # Summary
        elif query.data.startswith('summary_'):
            subject = query.data.split('_')[1]
            subject_name = "الأحياء" if subject == "biology" else "اللغة العربية"

            query.message.reply_text(
                text=f"📚 اكتب الموضوع الذي تريد ملخصاً له في {subject_name}:",
                reply_markup=self._get_back_button()
            )
            context.user_data['action'] = 'get_summary'
            context.user_data['subject'] = subject

        # Quiz (new and enhanced)
        elif query.data.startswith('quiz_'):
            subject = query.data.split('_')[1]
            subject_name = "الأحياء" if subject == "biology" else "اللغة العربية"

            query.message.reply_text(
                text=f"🎯 اكتب الموضوع الذي تريد اختباراً فيه من {subject_name}:",
                reply_markup=self._get_back_button()
            )
            context.user_data['action'] = 'generate_quiz'
            context.user_data['subject'] = subject

        # Add task
        elif query.data == 'add_task':
            query.message.reply_text(
                text="✅ إضافة مهمة جديدة\n\nاكتب وصف المهمة:",
                reply_markup=self._get_back_button()
            )
            context.user_data['action'] = 'add_task'

        # Show tasks
        elif query.data == 'show_tasks':
            self.show_tasks(update, context)
        elif query.data == 'show_all_tasks':
            self.show_tasks(update, context, filter_type='all')
        elif query.data == 'show_completed_tasks':
            self.show_tasks(update, context, filter_type='completed')
        elif query.data == 'show_pending_tasks':
            self.show_tasks(update, context, filter_type='pending')

        # Complete task
        elif query.data.startswith('complete_task_'):
            task_id = int(query.data.split('_')[2])
            self.complete_task(update, context, task_id)

        # Delete task
        elif query.data.startswith('delete_task_'):
            task_id = int(query.data.split('_')[2])
            self.delete_task(update, context, task_id)

        # Enhanced statistics
        elif query.data == 'show_stats':
            self.show_detailed_statistics(update, context)

        # 🔧 Fix: End quiz button - must be before answer processing
        elif query.data == 'end_quiz':
            if 'current_quiz' in context.user_data:
                # Delete "Loading..." message if it exists
                try:
                    query.message.delete()
                except:
                    pass

                # End quiz and show results
                self.finish_quiz(update, context)
            else:
                query.message.reply_text(
                    "❌ لا يوجد اختبار نشط",
                    reply_markup=self._get_main_menu_keyboard()
                )

        # 🔧 Fix: Process quiz answers via buttons
        elif query.data.startswith('answer_'):
            answer_map = {
                'answer_a': 'أ',
                'answer_b': 'ب',
                'answer_c': 'ج',
                'answer_d': 'د'
            }
            user_answer = answer_map[query.data]

            if 'current_quiz' not in context.user_data:
                query.message.reply_text(
                    "❌ انتهى وقت الاختبار",
                    reply_markup=self._get_main_menu_keyboard()
                )
                return

            # Save answer
            quiz_data = context.user_data['current_quiz']
            quiz_data['user_answers'].append(user_answer)
            quiz_data['current_question'] += 1

            # Delete current question message
            try:
                query.message.delete()
            except:
                pass

            # Show next question
            self.show_next_question(update, context)

        else:
            query.message.reply_text(
                text="❌ أمر غير معروف، جرب مرة أخرى:",
                reply_markup=self._get_main_menu_keyboard()
            )

    def handle_message(self, update: Update, context: CallbackContext) -> None:
        """Handle text messages"""
        user_id = update.effective_user.id
        text = update.message.text

        if 'action' in context.user_data:
            action = context.user_data['action']

            if action == 'ask_question':
                subject = context.user_data.get('subject', None)
                self.answer_question(update, context, text, subject)
            elif action == 'add_task':
                self.add_task(update, context, text)
            elif action == 'get_summary':
                subject = context.user_data.get('subject', '')
                self.get_summary(update, context, subject, text)
            elif action == 'generate_quiz':
                subject = context.user_data.get('subject', '')
                self.generate_quiz(update, context, subject, text)

            context.user_data.pop('action', None)
            context.user_data.pop('subject', None)

        else:
            intent = self.text_classifier.classify(text)

            if intent == 'question':
                self.answer_question(update, context, text)
            elif intent == 'add_task':
                self.add_task(update, context, text)
            elif intent == 'greeting':
                self._send_welcome_message(update)
            else:
                update.message.reply_text(
                    "🤔 لم أفهم طلبك بالضبط.\n\nاستخدم القائمة أدناه:",
                    reply_markup=self._get_main_menu_keyboard()
                )

    def add_task(self, update: Update, context: CallbackContext, task_text: str) -> None:
        """Add a new task for the user"""
        from datetime import datetime
        user_id = update.effective_user.id
        due_date = datetime.now().strftime("%Y-%m-%d")
        priority = 1
        self.db_manager.add_task(user_id, task_text, due_date, priority)
        update.message.reply_text(
            f"✅ تمت إضافة المهمة بنجاح!\n\n📝 {task_text}",
            reply_markup=self._get_main_menu_keyboard()
        )

    def complete_task(self, update: Update, context: CallbackContext, task_id: int) -> None:
        """Complete a task"""
        self.db_manager.update_task_status(task_id, 'completed')
        self.db_manager.update_user_activity(
            update.effective_user.id, 'task_completed')

        query = update.callback_query
        query.message.reply_text(
            "✅ تم إكمال المهمة بنجاح! 🎉",
            reply_markup=self._get_main_menu_keyboard()
        )

    def delete_task(self, update: Update, context: CallbackContext, task_id: int) -> None:
        """Delete a task"""
        self.db_manager.delete_task(task_id)

        query = update.callback_query
        query.message.reply_text(
            "🗑️ تم حذف المهمة بنجاح!",
            reply_markup=self._get_main_menu_keyboard()
        )

    def show_tasks(self, update: Update, context: CallbackContext, filter_type='pending') -> None:
        """Show user tasks with management options"""
        user_id = update.effective_user.id
        tasks = self.db_manager.get_tasks(user_id, status='all')

        if not tasks:
            update.callback_query.message.reply_text(
                text="📋 ليس لديك مهام حالياً\n\nأنت منظم! 👍",
                reply_markup=self._get_main_menu_keyboard()
            )
            return

        if filter_type == 'completed':
            filtered_tasks = [task for task in tasks if task[4] == 'completed']
            title = "✅ المهام المكتملة"
        elif filter_type == 'pending':
            filtered_tasks = [task for task in tasks if task[4] != 'completed']
            title = "⏳ المهام القادمة"
        else:
            filtered_tasks = tasks
            title = "📋 جميع المهام"

        if not filtered_tasks:
            update.callback_query.message.reply_text(
                text=f"{title}:\n\nلا توجد مهام في هذه الفئة.",
                reply_markup=self._get_main_menu_keyboard()
            )
            return

        task_list = f"{title}:\n\n"

        for i, (task_id, task_name, due_date, priority, status) in enumerate(filtered_tasks, 1):
            status_emoji = "✅" if status == 'completed' else "⏳"
            priority_emoji = "🔴" if priority == 3 else "🟡" if priority == 2 else "🟢"
            task_list += f"{i}. {status_emoji} {priority_emoji} {task_name}\n"
            task_list += f"   📅 {due_date}\n\n"

        keyboard = []
        for task_id, task_name, due_date, priority, status in filtered_tasks:
            if status != 'completed':
                display_name = task_name[:25] + \
                    "..." if len(task_name) > 25 else task_name
                task_button = InlineKeyboardButton(
                    f"✅ {display_name}",
                    callback_data=f'complete_task_{task_id}'
                )
                delete_button = InlineKeyboardButton(
                    f"🗑️ {display_name}",
                    callback_data=f'delete_task_{task_id}'
                )
                keyboard.append([task_button, delete_button])

        keyboard.append([InlineKeyboardButton(
            "🔙 القائمة الرئيسية", callback_data='main_menu')])

        reply_markup = InlineKeyboardMarkup(keyboard)

        update.callback_query.message.reply_text(
            text=task_list,
            reply_markup=reply_markup
        )

    def _clean_text_for_telegram(self, text):
        """🔧 Clean text to remove invalid Markdown characters"""
        # Remove incorrect escape characters
        text = text.replace('\\*', '')
        text = text.replace('\\_', '')
        text = text.replace('\\`', '')
        text = text.replace('\\[', '[')
        text = text.replace('\\]', ']')

        # Remove excessive formatting marks
        import re
        text = re.sub(r'\*+', '', text)
        text = re.sub(r'_+', '', text)

        return text.strip()

    def answer_question(self, update: Update, context: CallbackContext,
                        question: str, subject_filter: str = None) -> None:
        """Answer the user's question - enhanced"""

        waiting_msg = update.message.reply_text("🔍 جاري البحث عن الإجابة...")

        search_results = self.rag_system.search_with_quality_filter(
            question, k=5, min_quality=0.25, subject_filter=subject_filter
        )

        if subject_filter and search_results:
            search_results = [
                r for r in search_results if r["metadata"]["subject"] == subject_filter]

        if not search_results or (search_results and search_results[0]["score"] < 0.4):
            subject_text = ""
            if subject_filter:
                subject_name = "الأحياء" if subject_filter == 'biology' else "اللغة العربية"
                subject_text = f" في مادة {subject_name}"

            response = f"""❌ عذراً، لم أجد إجابة دقيقة{subject_text}

💡 اقتراحات:
• حاول إعادة صياغة السؤال
• تأكد من أن السؤال واضح ومحدد
• تأكد أن السؤال يتعلق بالمادة الصحيحة

📚 مواضيع يمكنني مساعدتك بها:
{"• التكاثر، الخلية، الهرمونات، المناعة" if subject_filter == "biology" else "• مدرسة الديوان، الشعر، النحو، الأدب"}"""

            waiting_msg.delete()

            update.message.reply_text(
                response,
                reply_markup=self._get_main_menu_keyboard()
            )

            self.db_manager.update_user_activity(
                update.effective_user.id, 'question')
            return

        context_text = "\n\n".join([result["text"]
                                       for result in search_results[:3]])
        answer = self.ai_generator.generate_answer(question, context_text)

        sources = []
        for result in search_results[:3]:
            subject = "الأحياء" if result["metadata"]["subject"] == "biology" else "اللغة العربية"
            chapter = result["metadata"]["chapter"]
            page = result["metadata"]["page"]
            score = result["score"]
            sources.append(
                f"• {subject} - {chapter} - صفحة {page} (دقة: {score:.0%})")

        quality_emoji = "✅" if search_results[0]["score"] >= 0.6 else "⚠️"

        # 🔧 Clean text to remove invalid Markdown characters
        cleaned_answer = self._clean_text_for_telegram(answer)

        response = f"""{quality_emoji} الإجابة:

{cleaned_answer}

📚 المصادر:
{chr(10).join(sources)}

💡 هل تريد المزيد من التفاصيل؟ اسألني!"""

        waiting_msg.delete()

        self._send_long_message(
            update, response, self._get_main_menu_keyboard())

        self.db_manager.update_user_activity(
            update.effective_user.id, 'question')

    def get_summary(self, update: Update, context: CallbackContext,
                        subject: str, topic: str) -> None:
        """Get a summary for a specific topic"""

        waiting_msg = update.message.reply_text("📚 جاري تحضير الملخص...")

        search_results = self.rag_system.search_with_quality_filter(
            topic, k=8, min_quality=0.25, subject_filter=subject
        )

        if subject and search_results:
            search_results = [
                r for r in search_results if r["metadata"]["subject"] == subject]

        if search_results and search_results[0]["score"] < 0.4:
            search_results = []

        if not search_results:
            subject_ar = "الأحياء" if subject == "biology" else "اللغة العربية"

            waiting_msg.delete()

            update.message.reply_text(
                f"""❌ عذراً، الموضوع '{topic}' غير موجود في مادة {subject_ar}

💡 هذا الموضوع قد يكون من مادة أخرى

📚 مواضيع متاحة في {subject_ar}:
{"• التكاثر، الخلية، الهرمونات، المناعة، الجهاز العصبي" if subject == "biology" else "• مدرسة الديوان، الشعر العربي، النحو، البلاغة"}""",
                reply_markup=self._get_main_menu_keyboard()
            )
            return

        content = "\n\n".join([result["text"]
                               for result in search_results[:5]])
        summary = self.ai_generator.generate_summary(content)

        if "عذراً، حدث خطأ" in summary or "لم أتمكن من توليد ملخص" in summary:
            waiting_msg.delete()

            update.message.reply_text(
                summary,
                reply_markup=self._get_main_menu_keyboard()
            )
            return

        sources = set()
        for result in search_results[:3]:
            sources.add(
                f"• {result['metadata']['chapter']} - صفحة {result['metadata']['page']}")

        subject_ar = "الأحياء" if subject == "biology" else "اللغة العربية"

        # 🔧 Clean text from Markdown characters
        cleaned_summary = self._clean_text_for_telegram(summary)

        response = f"""📚 ملخص '{topic}'
في مادة {subject_ar}

{cleaned_summary}

📖 المصادر:
{chr(10).join(sources)}"""

        waiting_msg.delete()

        self._send_long_message(
            update, response, self._get_main_menu_keyboard())

        self.db_manager.update_user_activity(
            update.effective_user.id, 'summary')

    def _get_quiz_question_keyboard(self):
        """Keyboard during quiz solving"""
        keyboard = [
            [
                InlineKeyboardButton("أ", callback_data='answer_a'),
                InlineKeyboardButton("ب", callback_data='answer_b'),
                InlineKeyboardButton("ج", callback_data='answer_c'),
                InlineKeyboardButton("د", callback_data='answer_d')
            ],
            [InlineKeyboardButton("⏹️ إنهاء الاختبار",
                                     callback_data='end_quiz')]
        ]
        return InlineKeyboardMarkup(keyboard)

    def show_detailed_statistics(self, update: Update, context: CallbackContext) -> None:
        """Show detailed statistics"""
        user_id = update.effective_user.id
        stats = self.db_manager.get_detailed_user_stats(user_id)

        if not stats:
            stats_text = "📊 إحصائياتك\n\nلا توجد إحصائيات حتى الآن!"
        else:
            stats_text = f"""📊 إحصائياتك الشخصية

❓ الأسئلة: {stats['questions_asked']}
📚 الملخصات: {stats['summaries_generated']}   
🎯 الاختبارات: {stats['quizzes_taken']}
✅ المهام المكتملة: {stats['tasks_completed']}
📋 المهام المعلقة: {stats['pending_tasks']}
📊 إجمالي المهام: {stats['total_tasks']}

⏰ آخر نشاط: {stats['last_active'] or 'غير متاح'}

💪 مستوى نشاطك: {"🟢 ممتاز" if stats['questions_asked'] > 10 else "🟡 جيد" if stats['questions_asked'] > 5 else "🔴 مبتدئ"}"""

        update.callback_query.message.reply_text(
            text=stats_text,
            reply_markup=self._get_main_menu_keyboard()
        )

    def generate_quiz(self, update: Update, context: CallbackContext, subject: str, topic: str) -> None:
        """Generate an enhanced quiz"""

        waiting_msg = update.message.reply_text("🎯 جاري تحضير الاختبار...")

        search_results = self.rag_system.search_with_quality_filter(
            topic, k=5, min_quality=0.3, subject_filter=subject
        )

        if subject and search_results:
            search_results = [
                r for r in search_results if r["metadata"]["subject"] == subject]

        if search_results and search_results[0]["score"] < 0.4:
            search_results = []

        if not search_results:
            subject_ar = "الأحياء" if subject == "biology" else "اللغة العربية"

            waiting_msg.delete()

            update.message.reply_text(
                f"❌ عذراً، لم أجد محتوى كافٍ عن '{topic}' في مادة {subject_ar}\n\n💡 جرب موضوعاً آخر أو تأكد من كتابة الموضوع بشكل صحيح.",
                reply_markup=self._get_main_menu_keyboard()
            )
            return

        content = "\n\n".join([result["text"]
                               for result in search_results[:3]])

        from quiz_generator import QuizGenerator
        quiz_gen = QuizGenerator()
        questions = quiz_gen.generate_structured_quiz(content, num_questions=5)

        if not questions or len(questions) == 0:
            waiting_msg.delete()

            update.message.reply_text(
                "❌ عذراً، حدث خطأ في توليد الأسئلة. حاول مرة أخرى.",
                reply_markup=self._get_main_menu_keyboard()
            )
            return

        import time
        quiz_id = f"{subject}_{int(time.time())}"

        context.user_data['current_quiz'] = {
            'quiz_id': quiz_id,
            'questions': questions,
            'current_question': 0,
            'user_answers': []
        }

        subject_ar = "الأحياء" if subject == "biology" else "اللغة العربية"

        waiting_msg.delete()

        response = f"""🎯 اختبار في '{topic}'
مادة {subject_ar}

عدد الأسئلة: {len(questions)}
لنبدأ الاختبار الآن!"""

        update.message.reply_text(
            response,
            reply_markup=self._get_main_menu_keyboard()
        )

        self.show_next_question(update, context)

        self.db_manager.update_user_activity(update.effective_user.id, 'quiz')

    def start_quiz(self, update: Update, context: CallbackContext) -> None:
        """Start solving the quiz"""
        query = update.callback_query

        if 'current_quiz' not in context.user_data:
            query.message.reply_text(
                text="❌ عذراً، انتهى وقت هذا الاختبار",
                reply_markup=self._get_main_menu_keyboard()
            )
            return

        questions = context.user_data['quiz_questions']

        context.user_data['current_quiz'] = {
            'quiz_id': context.user_data.get('quiz_id', 'quiz'),
            'questions': questions,
            'current_question': 0,
            'user_answers': []
        }

        self.show_next_question(update, context)

    def show_next_question(self, update: Update, context: CallbackContext) -> None:
        """Show the next question"""
        quiz_data = context.user_data['current_quiz']
        current_index = quiz_data['current_question']
        questions = quiz_data['questions']

        if current_index >= len(questions):
            self.finish_quiz(update, context)
            return

        question = questions[current_index]

        # 🔧 Clean the question from Markdown characters
        cleaned_question = self._clean_text_for_telegram(question['question'])

        question_text = f"""🎯 السؤال {current_index + 1} من {len(questions)}:

{cleaned_question}

"""

        for key, value in question['options'].items():
            question_text += f"{key}) {value}\n"

        question_text += "\n👇 اختر الإجابة:"

        if hasattr(update, 'callback_query') and update.callback_query:
            update.callback_query.message.reply_text(
                text=question_text,
                reply_markup=self._get_quiz_question_keyboard()
            )
        else:
            update.message.reply_text(
                text=question_text,
                reply_markup=self._get_quiz_question_keyboard()
            )

    def finish_quiz(self, update: Update, context: CallbackContext) -> None:
        """End the quiz and show results"""
        from quiz_generator import QuizGenerator
        quiz_gen = QuizGenerator()

        quiz_data = context.user_data.get('current_quiz')

        if not quiz_data:
            if hasattr(update, 'callback_query') and update.callback_query:
                update.callback_query.message.reply_text(
                    "❌ لا يوجد اختبار نشط",
                    reply_markup=self._get_main_menu_keyboard()
                )
            else:
                update.message.reply_text(
                    "❌ لا يوجد اختبار نشط",
                    reply_markup=self._get_main_menu_keyboard()
                )
            return

        questions = quiz_data['questions']
        user_answers = quiz_data['user_answers']

        # If not all questions were answered, append empty answers
        while len(user_answers) < len(questions):
            user_answers.append("لا إجابة")

        score_result = quiz_gen.calculate_score(user_answers, questions)

        result_text = f"""🎉 انتهى الاختبار!

{score_result['message']}

📊 النتيجة النهائية:
• الدرجة: {score_result['score']}/{score_result['total']}
• النسبة: {score_result['percentage']:.1f}%
• التقييم: {score_result['grade']}

📝 تفاصيل الإجابات:

"""

        for i, question in enumerate(questions, 1):
            user_answer = user_answers[i-1] if i - \
                1 < len(user_answers) else "لا إجابة"
            correct_answer = question['correct_answer']
            is_correct = user_answer == correct_answer

            # 🔧 Clean the question
            cleaned_question = self._clean_text_for_telegram(
                question['question'])

            result_text += f"السؤال {i}:\n"
            result_text += f"{cleaned_question}\n\n"

            for key, value in question['options'].items():
                if key == correct_answer and key == user_answer:
                    result_text += f"✅ {key}) {value} (إجابتك - صحيحة)\n"
                elif key == correct_answer:
                    result_text += f"✅ {key}) {value} (الإجابة الصحيحة)\n"
                elif key == user_answer:
                    result_text += f"❌ {key}) {value} (إجابتك - خاطئة)\n"
                else:
                    result_text += f"   {key}) {value}\n"

            result_text += f"\n💡 الشرح: {question['explanation']}\n\n"
            result_text += "─" * 30 + "\n\n"

        # Clean up data before sending
        context.user_data.pop('current_quiz', None)
        context.user_data.pop('quiz_questions', None)
        context.user_data.pop('quiz_id', None)

        if hasattr(update, 'callback_query') and update.callback_query:
            self._send_long_message(
                update, result_text, self._get_main_menu_keyboard(), is_callback=True)
        else:
            self._send_long_message(
                update, result_text, self._get_main_menu_keyboard())

    def _send_long_message(self, update: Update, text: str, reply_markup=None, is_callback=False):
        """Send a long message divided into chunks"""
        MAX_MESSAGE_LENGTH = 4000

        if len(text) <= MAX_MESSAGE_LENGTH:
            if is_callback:
                update.callback_query.message.reply_text(
                    text=text,
                    reply_markup=reply_markup
                )
            else:
                update.message.reply_text(
                    text=text,
                    reply_markup=reply_markup
                )
            return

        chunks = []
        current_chunk = ""

        for line in text.split('\n'):
            if len(current_chunk) + len(line) + 1 > MAX_MESSAGE_LENGTH:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line
            else:
                if current_chunk:
                    current_chunk += '\n'
                current_chunk += line

        if current_chunk:
            chunks.append(current_chunk)

        for i, chunk in enumerate(chunks):
            chunk_reply_markup = reply_markup if i == len(chunks) - 1 else None

            if i > 0:
                chunk = f"... (متابعة)\n\n{chunk}"

            if is_callback:
                update.callback_query.message.reply_text(
                    text=chunk,
                    reply_markup=chunk_reply_markup
                )
            else:
                update.message.reply_text(
                    text=chunk,
                    reply_markup=chunk_reply_markup
                )
                
    def run(self):
        dispatcher = self.dispatcher

        dispatcher.add_handler(CallbackQueryHandler(
            self.start_quiz,
            pattern='^start_quiz_'
        ))

        dispatcher.add_handler(CommandHandler("start", self.start))
        dispatcher.add_handler(CallbackQueryHandler(self.button))
        dispatcher.add_handler(MessageHandler(
            Filters.text & ~Filters.command, self.handle_message))

        print("✅ البوت يعمل الآن...")
        self.updater.start_polling()
        self.updater.idle()
