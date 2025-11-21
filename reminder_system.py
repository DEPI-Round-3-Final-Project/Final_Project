from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import logging
import pytz

logger = logging.getLogger(__name__)


class ReminderSystem:
    """
    🆕 Smart reminder system for tasks

    Features:
    - Remind about tasks one day before the due date
    - Daily notification for pending tasks
    - Periodic review reminder
    """

    def __init__(self, bot, db_manager):
        self.bot = bot
        self.db_manager = db_manager
        self.scheduler = BackgroundScheduler()
        self._setup_jobs()

    def _setup_jobs(self):
        """Setup scheduled jobs"""
        cairo_tz = pytz.timezone("Africa/Cairo")

        # Daily reminder at 8 AM
        self.scheduler.add_job(
            self.send_daily_reminder,
            'cron',
            hour=8,
            minute=0,
            id='daily_reminder',
            timezone=cairo_tz
        )

        # Evening reminder at 6 PM
        self.scheduler.add_job(
            self.send_evening_reminder,
            'cron',
            hour=18,
            minute=0,
            id='evening_reminder',
            timezone=cairo_tz
        )

        # Check tasks every hour
        self.scheduler.add_job(
            self.check_upcoming_tasks,
            'interval',
            hours=1,
            id='check_tasks',
            timezone=cairo_tz
        )

    def start(self):
        """Start the reminder system"""
        self.scheduler.start()
        logger.info("✅ نظام التذكيرات يعمل الآن")

    def stop(self):
        """Stop the reminder system"""
        self.scheduler.shutdown()
        logger.info("⏹️ تم إيقاف نظام التذكيرات")

    def send_daily_reminder(self):
        """Send a daily morning reminder"""
        logger.info("📨 إرسال التذكير اليومي الصباحي...")

        users = self.db_manager.get_all_users()

        for user_id, username, first_name, _ in users:
            try:
                tasks = self.db_manager.get_tasks(user_id)

                if tasks:
                    message = f"""☀️ صباح الخير {first_name}!

📋 لديك {len(tasks)} مهمة اليوم:

"""
                    for i, (_, task_name, due_date, priority, _) in enumerate(tasks[:5], 1):
                        priority_emoji = "🔴" if priority == 3 else "🟡" if priority == 2 else "🟢"
                        message += f"{i}. {priority_emoji} {task_name}\n"

                    message += "\n💪 لنبدأ يوماً منتجاً!"

                    self.bot.send_message(
                        chat_id=user_id,
                        text=message
                    )

            except Exception as e:
                logger.error(f"خطأ في إرسال التذكير لـ {user_id}: {e}")

    def send_evening_reminder(self):
        """Send an evening reminder"""
        logger.info("📨 إرسال التذكير المسائي...")

        users = self.db_manager.get_all_users()

        for user_id, username, first_name, _ in users:
            try:
                tasks = self.db_manager.get_tasks(user_id)

                if tasks:
                    message = f"""🌙 مساء الخير {first_name}!

📝 مراجعة المهام:
• لديك {len(tasks)} مهمة معلقة

💡 وقت المراجعة:
هل راجعت دروسك اليوم؟ 

🎯 نصيحة اليوم:
المراجعة المنتظمة أفضل من المذاكرة المكثفة!"""

                    self.bot.send_message(
                        chat_id=user_id,
                        text=message
                    )

            except Exception as e:
                logger.error(f"خطأ في إرسال التذكير المسائي لـ {user_id}: {e}")

    def check_upcoming_tasks(self):
        """Check for upcoming tasks and send a reminder"""
        logger.info("🔍 فحص المهام القريبة...")

        users = self.db_manager.get_all_users()
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        for user_id, username, first_name, _ in users:
            try:
                tasks = self.db_manager.get_tasks_by_date(user_id, tomorrow)

                if tasks:
                    message = f"""⏰ تذكير مهم!

{first_name}، لديك مهام غداً:

"""
                    for i, (_, task_name, due_date, priority, _) in enumerate(tasks, 1):
                        priority_emoji = "🔴" if priority == 3 else "🟡" if priority == 2 else "🟢"
                        message += f"{i}. {priority_emoji} {task_name}\n"

                    message += "\n📚 ابدأ التحضير الآن!"

                    self.bot.send_message(
                        chat_id=user_id,
                        text=message
                    )

            except Exception as e:
                logger.error(f"خطأ في فحص المهام لـ {user_id}: {e}")

    def send_custom_reminder(self, user_id, message):
        """Send a custom reminder"""
        try:
            self.bot.send_message(
                chat_id=user_id,
                text=message
            )
            logger.info(f"✅ تم إرسال تذكير مخصص لـ {user_id}")
        except Exception as e:
            logger.error(f"خطأ في إرسال التذكير المخصص: {e}")

    def schedule_task_reminder(self, user_id, task_name, due_datetime):
        """Schedule a reminder for a specific task"""
        reminder_time = due_datetime - timedelta(days=1)

        if reminder_time > datetime.now():
            self.scheduler.add_job(
                self.send_custom_reminder,
                'date',
                run_date=reminder_time,
                args=[user_id, f"⏰ تذكير: {task_name}\nالموعد: غداً"],
                id=f'task_reminder_{user_id}_{task_name}',
                timezone=pytz.timezone("Africa/Cairo")
            )
            logger.info(f"✅ تم جدولة تذكير للمهمة: {task_name}")

    def get_scheduler_status(self):
        """Get scheduler status"""
        return {
            "running": self.scheduler.running,
            "jobs_count": len(self.scheduler.get_jobs())
        }
    
