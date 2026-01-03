"""
Focus Manager - Business logic for Pomodoro and Time Block focus sessions.
Provides a calm, minimal focus tracking experience.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any
from database import DatabaseManager


class FocusMode(Enum):
    POMODORO = "pomodoro"
    TIMEBLOCK = "timeblock"


class PomodoroPhase(Enum):
    IDLE = "idle"
    FOCUS = "focus"
    BREAK = "break"
    LONG_BREAK = "long_break"


class FocusManager:
    """Manages focus sessions with Pomodoro and Time Block modes."""
    
    # Default Pomodoro durations (in minutes)
    FOCUS_DURATION = 25
    BREAK_DURATION = 5
    LONG_BREAK_DURATION = 15
    SESSIONS_BEFORE_LONG_BREAK = 4
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()
        
        # Current state
        self.mode = FocusMode.POMODORO
        self.phase = PomodoroPhase.IDLE
        self.session_count = 0
        
        # Timer state
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.remaining_seconds: int = self.FOCUS_DURATION * 60
        self.is_running: bool = False
        self.paused_remaining: Optional[int] = None  # For pause functionality
        
        # Time Block state
        self.timeblock_start: Optional[datetime] = None
        self.timeblock_end: Optional[datetime] = None
        self.timeblock_task_name: str = ""
        
        # Current session ID (for database)
        self.current_session_id: Optional[int] = None
        
        # Load settings
        self._load_settings()
    
    def _load_settings(self):
        """Load focus settings from database."""
        mode_str = self.db.get_setting('focus_mode', 'pomodoro')
        self.mode = FocusMode.POMODORO if mode_str == 'pomodoro' else FocusMode.TIMEBLOCK
    
    def set_mode(self, mode: FocusMode):
        """Switch between Pomodoro and Time Block modes."""
        if self.is_running:
            return False  # Can't switch while running
        self.mode = mode
        self.db.set_setting('focus_mode', mode.value)
        return True
    
    # =====================
    # POMODORO METHODS
    # =====================
    
    def start_pomodoro(self) -> bool:
        """Start a Pomodoro focus session."""
        if self.is_running:
            return False
        
        self.phase = PomodoroPhase.FOCUS
        self.remaining_seconds = self.FOCUS_DURATION * 60
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(seconds=self.remaining_seconds)
        self.is_running = True
        
        # Log session start
        self.current_session_id = self._log_session_start('pomodoro', 'focus')
        
        return True
    
    def start_break(self) -> bool:
        """Start a break after completing a focus session."""
        if self.is_running:
            return False
        
        # Determine break type
        if self.session_count > 0 and self.session_count % self.SESSIONS_BEFORE_LONG_BREAK == 0:
            self.phase = PomodoroPhase.LONG_BREAK
            duration = self.LONG_BREAK_DURATION
        else:
            self.phase = PomodoroPhase.BREAK
            duration = self.BREAK_DURATION
        
        self.remaining_seconds = duration * 60
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(seconds=self.remaining_seconds)
        self.is_running = True
        
        # Log break start
        self.current_session_id = self._log_session_start('pomodoro', self.phase.value)
        
        return True
    
    def stop(self) -> Dict[str, Any]:
        """Stop the current session early (no penalty, no reward)."""
        result = {
            'was_running': self.is_running,
            'phase': self.phase.value,
            'completed': False,
            'elapsed_seconds': 0
        }
        
        if self.is_running and self.start_time:
            elapsed = datetime.now() - self.start_time
            result['elapsed_seconds'] = int(elapsed.total_seconds())
            
            # Log incomplete session
            if self.current_session_id:
                self._log_session_end(self.current_session_id, completed=False)
        
        self._reset_state()
        return result
    
    def tick(self) -> Dict[str, Any]:
        """Called every second to update timer. Returns current state."""
        if not self.is_running:
            return self._get_state()
        
        # Calculate actual remaining time based on end_time for accuracy
        if self.end_time:
            now = datetime.now()
            self.remaining_seconds = max(0, int((self.end_time - now).total_seconds()))
        else:
            self.remaining_seconds = max(0, self.remaining_seconds - 1)
        
        if self.remaining_seconds <= 0:
            # Session completed
            return self._complete_session()
        
        return self._get_state()
    
    def _complete_session(self) -> Dict[str, Any]:
        """Handle session completion."""
        completed_phase = self.phase
        
        # Log completion
        if self.current_session_id:
            self._log_session_end(self.current_session_id, completed=True)
        
        if completed_phase == PomodoroPhase.FOCUS:
            self.session_count += 1
        
        self._reset_state()
        
        return {
            'completed': True,
            'phase': completed_phase.value,
            'session_count': self.session_count,
            'remaining_seconds': 0,
            'is_running': False
        }
    
    def _reset_state(self):
        """Reset timer state to idle."""
        self.is_running = False
        self.phase = PomodoroPhase.IDLE
        self.remaining_seconds = self.FOCUS_DURATION * 60
        self.start_time = None
        self.end_time = None
        self.current_session_id = None
        self.paused_remaining = None
    
    def _get_state(self) -> Dict[str, Any]:
        """Get current timer state."""
        return {
            'mode': self.mode.value,
            'phase': self.phase.value,
            'is_running': self.is_running,
            'remaining_seconds': self.remaining_seconds,
            'session_count': self.session_count,
            'completed': False
        }
    
    # =====================
    # TIME BLOCK METHODS
    # =====================
    
    def schedule_timeblock(self, start: datetime, end: datetime, task_name: str = "") -> Dict[str, Any]:
        """Schedule a time block for future focus."""
        now = datetime.now()
        
        # Validation
        if start <= now:
            return {'success': False, 'error': 'Start time must be in the future'}
        
        if end <= start:
            return {'success': False, 'error': 'End time must be after start time'}
        
        # Check for overlapping sessions
        if self._has_overlapping_session(start, end):
            return {'success': False, 'error': 'Time block overlaps with existing session'}
        
        self.timeblock_start = start
        self.timeblock_end = end
        self.timeblock_task_name = task_name
        
        # Log to database
        duration = int((end - start).total_seconds() / 60)
        session_id = self._log_timeblock(start, end, duration, task_name)
        
        return {
            'success': True,
            'session_id': session_id,
            'start': start.isoformat(),
            'end': end.isoformat(),
            'duration_minutes': duration
        }
    
    def clear_timeblock(self):
        """Clear the scheduled time block."""
        self.timeblock_start = None
        self.timeblock_end = None
        self.timeblock_task_name = ""
    
    def get_timeblock_status(self) -> Dict[str, Any]:
        """Get current time block status."""
        if not self.timeblock_start:
            return {'active': False}
        
        now = datetime.now()
        
        if now < self.timeblock_start:
            status = 'scheduled'
            remaining = (self.timeblock_start - now).total_seconds()
        elif now < self.timeblock_end:
            status = 'in_progress'
            remaining = (self.timeblock_end - now).total_seconds()
        else:
            status = 'completed'
            remaining = 0
        
        return {
            'active': True,
            'status': status,
            'start': self.timeblock_start.isoformat(),
            'end': self.timeblock_end.isoformat(),
            'task_name': self.timeblock_task_name,
            'remaining_seconds': int(remaining)
        }
    
    def _has_overlapping_session(self, start: datetime, end: datetime) -> bool:
        """Check if there's an overlapping time block."""
        # For now, just check against current timeblock
        if self.timeblock_start and self.timeblock_end:
            # Check overlap: sessions overlap if one starts before the other ends
            if start < self.timeblock_end and end > self.timeblock_start:
                return True
        return False
    
    # =====================
    # DATABASE METHODS
    # =====================
    
    def _log_session_start(self, mode: str, session_type: str) -> int:
        """Log session start to database."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO focus_sessions (mode, start_time, session_type)
                VALUES (?, ?, ?)
            ''', (mode, datetime.now().isoformat(), session_type))
            
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return session_id
        except Exception as e:
            print(f"Error logging session start: {e}")
            return 0
    
    def _log_session_end(self, session_id: int, completed: bool):
        """Log session end to database."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            end_time = datetime.now()
            
            # Get start time to calculate duration
            cursor.execute('SELECT start_time FROM focus_sessions WHERE id = ?', (session_id,))
            row = cursor.fetchone()
            
            if row:
                start_time = datetime.fromisoformat(row[0])
                duration = int((end_time - start_time).total_seconds() / 60)
                
                cursor.execute('''
                    UPDATE focus_sessions 
                    SET end_time = ?, duration_minutes = ?, completed = ?
                    WHERE id = ?
                ''', (end_time.isoformat(), duration, 1 if completed else 0, session_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error logging session end: {e}")
    
    def _log_timeblock(self, start: datetime, end: datetime, duration: int, task_name: str) -> int:
        """Log time block to database."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO focus_sessions (mode, start_time, end_time, duration_minutes, session_type)
                VALUES (?, ?, ?, ?, ?)
            ''', ('timeblock', start.isoformat(), end.isoformat(), duration, 'focus'))
            
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return session_id
        except Exception as e:
            print(f"Error logging timeblock: {e}")
            return 0
    
    # =====================
    # UTILITY METHODS
    # =====================
    
    @staticmethod
    def format_time(seconds: int) -> str:
        """Format seconds as MM:SS."""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
    
    def get_display_time(self) -> str:
        """Get formatted remaining time for display."""
        return self.format_time(self.remaining_seconds)
