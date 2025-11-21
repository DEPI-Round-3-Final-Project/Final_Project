import sqlite3
from datetime import datetime
import hashlib


class DatabaseManager:
    def __init__(self, db_path="study_assistant.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Create database tables - enhanced"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registration_date TEXT
        )
        ''')

        # Tasks table - enhanced
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_name TEXT,
            due_date TEXT,
            priority INTEGER DEFAULT 1,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')

        # Notes table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject TEXT,
            content TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')

        # Extracted textbook content table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS textbook_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            grade_level TEXT,
            chapter TEXT,
            content TEXT,
            page_number INTEGER,
            content_type TEXT
        )
        ''')

        # 🆕 Stats table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY,
            questions_asked INTEGER DEFAULT 0,
            summaries_generated INTEGER DEFAULT 0,
            quizzes_taken INTEGER DEFAULT 0,
            tasks_completed INTEGER DEFAULT 0,
            last_active TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')

        conn.commit()
        conn.close()

    def add_user(self, user_id, username, first_name, last_name):
        """Add a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, registration_date)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, registration_date))

        # Create stats record
        cursor.execute('''
        INSERT OR IGNORE INTO user_stats (user_id, last_active)
        VALUES (?, ?)
        ''', (user_id, registration_date))

        conn.commit()
        conn.close()

    def add_task(self, user_id, task_name, due_date, priority=1):
        """Add a new task - enhanced"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute('''
        INSERT INTO tasks (user_id, task_name, due_date, priority, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, task_name, due_date, priority, "pending", created_at))

        conn.commit()
        conn.close()

    def get_tasks(self, user_id, status='pending'):
        """Get user tasks - enhanced"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if status == 'all':
            cursor.execute('''
            SELECT id, task_name, due_date, priority, status FROM tasks
            WHERE user_id = ?
            ORDER BY due_date, priority DESC
            ''', (user_id,))
        else:
            cursor.execute('''
            SELECT id, task_name, due_date, priority, status FROM tasks
            WHERE user_id = ? AND status = ?
            ORDER BY due_date, priority DESC
            ''', (user_id, status))

        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def get_tasks_by_date(self, user_id, date):
        """🆕 Get tasks for a specific date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        SELECT id, task_name, due_date, priority, status FROM tasks
        WHERE user_id = ? AND due_date = ? AND status = 'pending'
        ORDER BY priority DESC
        ''', (user_id, date))

        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def update_task_status(self, task_id, new_status):
        """🆕 Update task status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        completed_at = None
        if new_status == 'completed':
            completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute('''
        UPDATE tasks
        SET status = ?, completed_at = ?
        WHERE id = ?
        ''', (new_status, completed_at, task_id))

        conn.commit()
        conn.close()

    def update_task_priority(self, task_id, new_priority):
        """🆕 Update task priority"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        UPDATE tasks
        SET priority = ?
        WHERE id = ?
        ''', (new_priority, task_id))

        conn.commit()
        conn.close()

    def delete_task(self, task_id):
        """🆕 Delete a task - without updating stats"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))

        conn.commit()
        conn.close()

    def get_all_users(self):
        """🆕 Get all users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT user_id, username, first_name, last_name FROM users')
        users = cursor.fetchall()

        conn.close()
        return users

    def update_user_stats(self, user_id, stat_type):
        """🔧 Update user statistics - enhanced"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        last_active = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Ensure user record exists
        cursor.execute('''
        INSERT OR IGNORE INTO user_stats (user_id, last_active) 
        VALUES (?, ?)
        ''', (user_id, last_active))

        if stat_type == 'question':
            cursor.execute('''
            UPDATE user_stats
            SET questions_asked = questions_asked + 1, last_active = ?
            WHERE user_id = ?
            ''', (last_active, user_id))
        elif stat_type == 'summary':
            cursor.execute('''
            UPDATE user_stats
            SET summaries_generated = summaries_generated + 1, last_active = ?
            WHERE user_id = ?
            ''', (last_active, user_id))
        elif stat_type == 'quiz':
            cursor.execute('''
            UPDATE user_stats
            SET quizzes_taken = quizzes_taken + 1, last_active = ?
            WHERE user_id = ?
            ''', (last_active, user_id))
        elif stat_type == 'task_completed':
            cursor.execute('''
            UPDATE user_stats
            SET tasks_completed = tasks_completed + 1, last_active = ?
            WHERE user_id = ?
            ''', (last_active, user_id))

        conn.commit()
        conn.close()

    def get_user_stats(self, user_id):
        """Get user statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        SELECT questions_asked, summaries_generated, quizzes_taken, 
               tasks_completed, last_active
        FROM user_stats
        WHERE user_id = ?
        ''', (user_id,))

        stats = cursor.fetchone()
        conn.close()

        if stats:
            return {
                'questions_asked': stats[0],
                'summaries_generated': stats[1],
                'quizzes_taken': stats[2],
                'tasks_completed': stats[3],
                'last_active': stats[4]
            }
        return None

    def add_textbook_content(self, subject, grade_level, chapter, content, page_number, content_type):
        """Add textbook content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        INSERT INTO textbook_content (subject, grade_level, chapter, content, page_number, content_type)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (subject, grade_level, chapter, content, page_number, content_type))

        conn.commit()
        conn.close()

    def get_textbook_content(self, subject, keywords=None):
        """Get textbook content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if keywords:
            query = f'''
            SELECT chapter, content, page_number FROM textbook_content
            WHERE subject = ? AND ({" OR ".join(["content LIKE ?" for _ in keywords])})
            '''
            params = [subject] + [f"%{keyword}%" for keyword in keywords]
            cursor.execute(query, params)
        else:
            cursor.execute('''
            SELECT chapter, content, page_number FROM textbook_content
            WHERE subject = ?
            ''', (subject,))

        content = cursor.fetchall()
        conn.close()
        return content

    def update_user_activity(self, user_id, activity_type):
        """🆕 Update personal activity statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        last_active = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Ensure user record exists
        cursor.execute('''
        INSERT OR IGNORE INTO user_stats (user_id, last_active) 
        VALUES (?, ?)
        ''', (user_id, last_active))

        if activity_type == 'question':
            cursor.execute('''
            UPDATE user_stats 
            SET questions_asked = questions_asked + 1, last_active = ?
            WHERE user_id = ?
            ''', (last_active, user_id))
        elif activity_type == 'summary':
            cursor.execute('''
            UPDATE user_stats 
            SET summaries_generated = summaries_generated + 1, last_active = ?
            WHERE user_id = ?
            ''', (last_active, user_id))
        elif activity_type == 'quiz':
            cursor.execute('''
            UPDATE user_stats 
            SET quizzes_taken = quizzes_taken + 1, last_active = ?
            WHERE user_id = ?
            ''', (last_active, user_id))
        elif activity_type == 'task_completed':
            cursor.execute('''
            UPDATE user_stats 
            SET tasks_completed = tasks_completed + 1, last_active = ?
            WHERE user_id = ?
            ''', (last_active, user_id))

        conn.commit()
        conn.close()

    def get_detailed_user_stats(self, user_id):
        """🔧 Get detailed user statistics - enhanced"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # User statistics
        cursor.execute('''
        SELECT questions_asked, summaries_generated, quizzes_taken, 
               tasks_completed, last_active
        FROM user_stats 
        WHERE user_id = ?
        ''', (user_id,))

        stats = cursor.fetchone()

        # Count current tasks (only pending)
        cursor.execute('''
        SELECT COUNT(*) FROM tasks 
        WHERE user_id = ? AND status = 'pending'
        ''', (user_id,))
        pending_tasks = cursor.fetchone()[0]

        # 🔧 Actual completed tasks count from the tasks table
        cursor.execute('''
        SELECT COUNT(*) FROM tasks 
        WHERE user_id = ? AND status = 'completed'
        ''', (user_id,))
        completed_tasks_actual = cursor.fetchone()[0]

        # 🔧 Total tasks (all tasks regardless of status)
        cursor.execute('''
        SELECT COUNT(*) FROM tasks 
        WHERE user_id = ?
        ''', (user_id,))
        total_tasks = cursor.fetchone()[0]

        conn.close()

        if stats:
            return {
                'questions_asked': stats[0],
                'summaries_generated': stats[1],
                'quizzes_taken': stats[2],
                'tasks_completed': completed_tasks_actual,  # 🔧 Use the actual count
                'last_active': stats[4],
                'pending_tasks': pending_tasks,
                'total_tasks': total_tasks  # 🆕 Add total tasks
            }

        # If no stats, return empty data
        return {
            'questions_asked': 0,
            'summaries_generated': 0,
            'quizzes_taken': 0,
            'tasks_completed': completed_tasks_actual if 'completed_tasks_actual' in locals() else 0,
            'last_active': None,
            'pending_tasks': pending_tasks if 'pending_tasks' in locals() else 0,
            'total_tasks': total_tasks if 'total_tasks' in locals() else 0
        }
    