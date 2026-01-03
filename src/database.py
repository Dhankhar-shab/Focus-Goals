import sqlite3
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'app_data.db')

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Habits Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')

        # Habit Logs Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER,
                date TEXT NOT NULL,
                status INTEGER DEFAULT 0,
                FOREIGN KEY (habit_id) REFERENCES habits (id)
            )
        ''')

        # Tasks Table (extended with is_top3 and duration)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                deadline TEXT,
                priority INTEGER,
                points INTEGER,
                is_completed INTEGER DEFAULT 0,
                energy_level TEXT,
                is_top3 INTEGER DEFAULT 0,
                duration_hours REAL DEFAULT 0
            )
        ''')
        
        # Add duration_hours column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE tasks ADD COLUMN duration_hours REAL DEFAULT 0')
        except:
            pass  # Column already exists
        
        # Task Logs (for tracking actions like postpone)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                date TEXT NOT NULL,
                action TEXT NOT NULL,
                reason TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''')

        # Rewards Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                points_cost INTEGER DEFAULT 0
            )
        ''')

        # Reward Logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reward_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reward_id INTEGER,
                date TEXT NOT NULL,
                FOREIGN KEY (reward_id) REFERENCES rewards (id)
            )
        ''')

        # Settings Table (key-value)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Reflections Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                completed TEXT,
                difficult TEXT,
                win TEXT
            )
        ''')

        # Points Balance Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS points_balance (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                balance INTEGER DEFAULT 0
            )
        ''')
        # Initialize balance if not exists
        cursor.execute('INSERT OR IGNORE INTO points_balance (id, balance) VALUES (1, 0)')
        
        # Focus Sessions Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS focus_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_minutes INTEGER,
                completed INTEGER DEFAULT 0,
                linked_task_id INTEGER,
                linked_habit_id INTEGER,
                session_type TEXT DEFAULT 'focus'
            )
        ''')
        
        # Initialize default focus settings
        cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('clock_visible', 'true'))
        cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('sound_enabled', 'false'))
        cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('focus_mode', 'pomodoro'))
        
        conn.commit()
        conn.close()

    # =====================
    # HABIT METHODS
    # =====================
    def add_habit(self, name: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        created_at = datetime.now().strftime("%Y-%m-%d")
        cursor.execute('INSERT INTO habits (name, created_at) VALUES (?, ?)', (name, created_at))
        conn.commit()
        habit_id = cursor.lastrowid
        conn.close()
        return habit_id

    def get_habits(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM habits')
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_habit(self, habit_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM habit_logs WHERE habit_id = ?', (habit_id,))
        cursor.execute('DELETE FROM habits WHERE id = ?', (habit_id,))
        conn.commit()
        conn.close()

    def log_habit(self, habit_id: int, date: str, status: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM habit_logs WHERE habit_id = ? AND date = ?', (habit_id, date))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('UPDATE habit_logs SET status = ? WHERE id = ?', (status, existing[0]))
        else:
            cursor.execute('INSERT INTO habit_logs (habit_id, date, status) VALUES (?, ?, ?)', (habit_id, date, status))
            
        conn.commit()
        conn.close()

    def get_habit_logs(self, habit_id: int, limit: int = 30):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM habit_logs WHERE habit_id = ? ORDER BY date DESC LIMIT ?', (habit_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return rows
        
    def get_todays_habit_status(self, habit_id: int):
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM habit_logs WHERE habit_id = ? AND date = ?', (habit_id, today))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0

    def get_habit_streak(self, habit_id: int) -> int:
        """Calculate consecutive days of 'Done' status (status=2)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date, status FROM habit_logs 
            WHERE habit_id = ? ORDER BY date DESC
        ''', (habit_id,))
        logs = cursor.fetchall()
        conn.close()
        
        streak = 0
        today = datetime.now().date()
        
        for i, (date_str, status) in enumerate(logs):
            log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            expected_date = today - timedelta(days=i)
            
            if log_date != expected_date:
                break
            if status != 2:
                break
            streak += 1
        
        return streak

    def get_week_habit_points(self, habit_id: int) -> List[int]:
        """Get points for last 7 days (Mon-Sun style, most recent first)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date()
        week_start = today - timedelta(days=6)
        
        cursor.execute('''
            SELECT date, status FROM habit_logs 
            WHERE habit_id = ? AND date >= ? AND date <= ?
            ORDER BY date ASC
        ''', (habit_id, week_start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")))
        logs = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        
        points = []
        for i in range(7):
            d = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
            status = logs.get(d, 0)
            points.append(status)  # 0, 1, or 2
        return points

    def get_month_habit_logs(self, habit_id: int, year: int, month: int) -> Dict[str, int]:
        """Get all habit logs for a specific habit in a given month.
        Returns dict mapping date strings to status values."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Build date range for the month
        start_date = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1:04d}-01-01"
        else:
            end_date = f"{year:04d}-{month + 1:02d}-01"
        
        cursor.execute('''
            SELECT date, status FROM habit_logs 
            WHERE habit_id = ? AND date >= ? AND date < ?
        ''', (habit_id, start_date, end_date))
        
        logs = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return logs

    def get_all_habits_month_data(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Get all habits with their monthly logs for efficient matrix rendering.
        Returns list of dicts with habit info and log data."""
        habits = self.get_habits()
        result = []
        
        for habit in habits:
            habit_id, name, created_at = habit
            logs = self.get_month_habit_logs(habit_id, year, month)
            result.append({
                'id': habit_id,
                'name': name,
                'created_at': created_at,
                'logs': logs  # Dict mapping date -> status
            })
        
        return result

    def get_month_summary(self, year: int, month: int) -> Dict[str, Any]:
        """Get summary statistics for a month.
        Returns habit count, completion data, and daily progress."""
        import calendar
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get total habits
        cursor.execute('SELECT COUNT(*) FROM habits')
        total_habits = cursor.fetchone()[0]
        
        # Date range
        start_date = f"{year:04d}-{month:02d}-01"
        days_in_month = calendar.monthrange(year, month)[1]
        
        # Get all logs for the month
        if month == 12:
            end_date = f"{year + 1:04d}-01-01"
        else:
            end_date = f"{year:04d}-{month + 1:02d}-01"
        
        cursor.execute('''
            SELECT date, COUNT(*) as count, SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) as done
            FROM habit_logs 
            WHERE date >= ? AND date < ?
            GROUP BY date
        ''', (start_date, end_date))
        
        daily_data = {}
        total_done = 0
        total_possible = 0
        
        for row in cursor.fetchall():
            date_str, count, done = row
            daily_data[date_str] = {
                'logged': count,
                'done': done,
                'percentage': (done / total_habits * 100) if total_habits > 0 else 0
            }
            total_done += done
        
        total_possible = total_habits * days_in_month
        
        conn.close()
        
        return {
            'total_habits': total_habits,
            'days_in_month': days_in_month,
            'total_done': total_done,
            'total_possible': total_possible,
            'completion_rate': (total_done / total_possible * 100) if total_possible > 0 else 0,
            'daily_data': daily_data
        }

    # =====================
    # TASK METHODS
    # =====================
    def add_task(self, name: str, deadline: Optional[str], priority: int, points: int, energy_level: str, duration_hours: float = 0):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (name, deadline, priority, points, energy_level, is_completed, is_top3, duration_hours)
            VALUES (?, ?, ?, ?, ?, 0, 0, ?)
        ''', (name, deadline, priority, points, energy_level, duration_hours))
        conn.commit()
        task_id = cursor.lastrowid
        conn.close()
        return task_id

    def get_tasks(self, include_completed=False, top3_only=False, energy_level: Optional[str] = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM tasks WHERE 1=1'
        params = []
        
        if not include_completed:
            query += ' AND is_completed = 0'
        if top3_only:
            query += ' AND is_top3 = 1'
        if energy_level:
            query += ' AND energy_level = ?'
            params.append(energy_level)
            
        query += ' ORDER BY priority DESC, deadline ASC'
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def set_task_top3(self, task_id: int, is_top3: bool):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET is_top3 = ? WHERE id = ?', (1 if is_top3 else 0, task_id))
        conn.commit()
        conn.close()

    def get_top3_count(self) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM tasks WHERE is_top3 = 1 AND is_completed = 0')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def complete_task(self, task_id: int) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET is_completed = 1 WHERE id = ?', (task_id,))
        cursor.execute('SELECT points FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        points = row[0] if row else 0
        
        # Log action
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute('INSERT INTO task_logs (task_id, date, action) VALUES (?, ?, ?)', (task_id, today, 'completed'))
        
        conn.commit()
        conn.close()
        return points

    def postpone_task(self, task_id: int, reason: str, new_deadline: Optional[str] = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        
        cursor.execute('INSERT INTO task_logs (task_id, date, action, reason) VALUES (?, ?, ?, ?)', 
                       (task_id, today, 'postponed', reason))
        
        if new_deadline:
            cursor.execute('UPDATE tasks SET deadline = ? WHERE id = ?', (new_deadline, task_id))
        
        conn.commit()
        conn.close()

    def delete_task(self, task_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM task_logs WHERE task_id = ?', (task_id,))
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        conn.close()

    # =====================
    # REWARDS METHODS
    # =====================
    def add_reward(self, name: str, points_cost: int = 0):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO rewards (name, points_cost) VALUES (?, ?)', (name, points_cost))
        conn.commit()
        reward_id = cursor.lastrowid
        conn.close()
        return reward_id

    def get_rewards(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM rewards')
        rows = cursor.fetchall()
        conn.close()
        return rows

    def claim_reward(self, reward_id: int) -> bool:
        """Claim a reward if balance is sufficient. Returns True if successful."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT points_cost FROM rewards WHERE id = ?', (reward_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
        
        cost = row[0]
        cursor.execute('SELECT balance FROM points_balance WHERE id = 1')
        balance = cursor.fetchone()[0]
        
        if balance >= cost:
            cursor.execute('UPDATE points_balance SET balance = balance - ? WHERE id = 1', (cost,))
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute('INSERT INTO reward_logs (reward_id, date) VALUES (?, ?)', (reward_id, today))
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False

    def delete_reward(self, reward_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM rewards WHERE id = ?', (reward_id,))
        conn.commit()
        conn.close()

    # =====================
    # POINTS METHODS
    # =====================
    def get_points_balance(self) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM points_balance WHERE id = 1')
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0

    def add_points(self, amount: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE points_balance SET balance = balance + ? WHERE id = 1', (amount,))
        conn.commit()
        conn.close()

    def deduct_points(self, amount: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE points_balance SET balance = MAX(0, balance - ?) WHERE id = 1', (amount,))
        conn.commit()
        conn.close()

    # =====================
    # SETTINGS METHODS
    # =====================
    def get_setting(self, key: str, default: str = '') -> str:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default

    def set_setting(self, key: str, value: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
        conn.commit()
        conn.close()

    def get_todays_energy(self) -> str:
        return self.get_setting('energy_level', 'Medium')

    def set_todays_energy(self, level: str):
        self.set_setting('energy_level', level)

    # =====================
    # REFLECTION METHODS
    # =====================
    def save_reflection(self, completed: str, difficult: str, win: str):
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO reflections (date, completed, difficult, win)
            VALUES (?, ?, ?, ?)
        ''', (today, completed, difficult, win))
        conn.commit()
        conn.close()

    def get_todays_reflection(self) -> Optional[Dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT completed, difficult, win FROM reflections WHERE date = ?', (today,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {'completed': row[0], 'difficult': row[1], 'win': row[2]}
        return None

    # =====================
    # DASHBOARD HELPERS
    # =====================
    def get_todays_stats(self) -> Dict[str, Any]:
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Habits done today
        cursor.execute('''
            SELECT COUNT(*) FROM habit_logs 
            WHERE date = ? AND status = 2
        ''', (today,))
        habits_done = cursor.fetchone()[0]
        
        # Total habits
        cursor.execute('SELECT COUNT(*) FROM habits')
        total_habits = cursor.fetchone()[0]
        
        # Pending tasks
        cursor.execute('SELECT COUNT(*) FROM tasks WHERE is_completed = 0')
        pending_tasks = cursor.fetchone()[0]
        
        # Top 3 pending
        cursor.execute('SELECT COUNT(*) FROM tasks WHERE is_top3 = 1 AND is_completed = 0')
        top3_pending = cursor.fetchone()[0]
        
        # High priority completed today
        cursor.execute('''
            SELECT COUNT(*) FROM task_logs tl
            JOIN tasks t ON tl.task_id = t.id
            WHERE tl.date = ? AND tl.action = 'completed' AND t.priority = 3
        ''', (today,))
        high_priority_done = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'habits_done': habits_done,
            'total_habits': total_habits,
            'pending_tasks': pending_tasks,
            'top3_pending': top3_pending,
            'high_priority_done': high_priority_done,
            'points_balance': self.get_points_balance(),
            'energy_level': self.get_todays_energy()
        }
