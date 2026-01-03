"""
Flip Clock Widget - A retro-style digital clock for the Study Focus app.
Translated from the tkinter addon to PySide6.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QTimer, QDateTime
from datetime import datetime

class DigitContainer(QFrame):
    """A single digit container for the flip clock."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 120)
        self.setStyleSheet("""
            DigitContainer {
                background-color: #2A2A2A;
                border: 2px solid #1A1A1A;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel("0")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                font-family: 'Arial';
                font-size: 80px;
                font-weight: bold;
                color: white;
                background-color: transparent;
            }
        """)
        layout.addWidget(self.label)

    def set_digit(self, digit):
        self.label.setText(str(digit))


class FlipClockWidget(QWidget):
    """
    Main Flip Clock widget containing hour, minute, and second units.
    Matches the aesthetic of the original tkinter addon.
    """
    def __init__(self, parent=None, show_seconds=True, mode="auto"):
        super().__init__(parent)
        self.show_seconds = show_seconds
        self.mode = mode # "auto" for system clock, "manual" for timer
        self.init_ui()
        
        # Timer for updates (only in auto mode)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        if self.mode == "auto":
            self.timer.start(1000)
            self.update_clock()

    def init_ui(self):
        self.setStyleSheet("background-color: transparent;")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Time Units
        self.hour_unit = self.create_time_unit(main_layout)
        self.add_separator(main_layout)
        self.minute_unit = self.create_time_unit(main_layout)
        
        if self.show_seconds:
            self.add_separator(main_layout)
            self.second_unit = self.create_time_unit(main_layout)
        
        # AM/PM Label
        self.am_pm_label = QLabel("")
        self.am_pm_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        main_layout.addWidget(self.am_pm_label, 0, Qt.AlignTop)

    def create_time_unit(self, layout):
        unit_layout = QHBoxLayout()
        unit_layout.setSpacing(5)
        
        d1 = DigitContainer()
        d2 = DigitContainer()
        
        unit_layout.addWidget(d1)
        unit_layout.addWidget(d2)
        
        layout.addLayout(unit_layout)
        return (d1, d2)

    def add_separator(self, layout):
        sep = QLabel(":")
        sep.setStyleSheet("""
            QLabel {
                color: #555555;
                font-size: 60px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(sep)

    def set_time(self, time_str):
        """
        Set time manually. Expected format: "MM:SS" or "HH:MM:SS" or "HH:MM AM/PM"
        """
        parts = time_str.split(' ')
        digits_part = parts[0]
        am_pm = parts[1] if len(parts) > 1 else ""
        
        time_components = digits_part.split(':')
        
        # Check if we have hours and minutes
        if len(time_components) >= 2:
            self.hour_unit[0].set_digit(time_components[0][0])
            self.hour_unit[1].set_digit(time_components[0][1])
            self.minute_unit[0].set_digit(time_components[1][0])
            self.minute_unit[1].set_digit(time_components[1][1])
            
        # Handle seconds if applicable
        if self.show_seconds:
            if len(time_components) >= 3:
                self.second_unit[0].set_digit(time_components[2][0])
                self.second_unit[1].set_digit(time_components[2][1])
            else:
                self.second_unit[0].set_digit('0')
                self.second_unit[1].set_digit('0')

        self.am_pm_label.setText(am_pm)

    def update_clock(self):
        if self.mode != "auto":
            return
            
        now = datetime.now()
        hour = now.strftime('%I')
        minute = now.strftime('%M')
        second = now.strftime('%S')
        am_pm = now.strftime('%p')
        
        self.set_time(f"{hour}:{minute}:{second} {am_pm}")
