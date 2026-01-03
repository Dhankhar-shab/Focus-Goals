"""
Global Clock Widget - A quiet time companion for the Study Focus app
Displays current time in a calm, minimal format
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from datetime import datetime
import platform


class ClockWidget(QWidget):
    """
    Minimal clock display for sidebar.
    Updates once per minute to avoid distraction.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
        # Update timer - once per minute
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_time)
        self.update_timer.start(60000)  # 60 seconds
        
        # Initial update
        self.update_time()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)
        
        # Time display (12-hour format)
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 500;
                color: #EAEAEA;
                letter-spacing: 1px;
            }
        """)
        
        # Date display (subtle)
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #6A6A6A;
                font-weight: 400;
            }
        """)
        
        layout.addWidget(self.time_label)
        layout.addWidget(self.date_label)
        
        # Container styling
        self.setStyleSheet("""
            ClockWidget {
                background-color: #1A1A1A;
                border-radius: 12px;
                border: 1px solid #2D2D2D;
            }
        """)
    
    def update_time(self):
        """Update the displayed time and date"""
        now = datetime.now()
        
        # 12-hour format with conditional padding based on OS
        if platform.system() == 'Windows':
            time_str = now.strftime("%#I:%M %p")
            date_str = now.strftime("%a, %b %#d")
        else:
            time_str = now.strftime("%-I:%M %p")
            date_str = now.strftime("%a, %b %-d")
        
        self.time_label.setText(time_str)
        self.date_label.setText(date_str)
    
    def showEvent(self, event):
        """When widget becomes visible, update immediately"""
        super().showEvent(event)
        self.update_time()


# Alternative: Compact Clock for Top Bar
class CompactClockWidget(QWidget):
    """
    Minimal clock for top bar placement.
    Even more compact than sidebar version.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_time)
        self.update_timer.start(60000)
        
        self.update_time()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(0)
        
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignRight)
        self.time_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #9A9A9A;
                letter-spacing: 0.5px;
            }
        """)
        
        layout.addWidget(self.time_label)
        
        self.setStyleSheet("background-color: transparent;")
    
    def update_time(self):
        """Update the displayed time"""
        now = datetime.now()
        
        # Use 12-hour format with proper padding
        if platform.system() == 'Windows':
            time_str = now.strftime("%#I:%M %p")
        else:
            time_str = now.strftime("%-I:%M %p")
            
        self.time_label.setText(time_str)
    
    def showEvent(self, event):
        """When widget becomes visible, update immediately"""
        super().showEvent(event)
        self.update_time()
