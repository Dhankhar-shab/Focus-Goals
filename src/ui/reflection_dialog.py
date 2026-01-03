from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame)
from PySide6.QtCore import Qt
from database import DatabaseManager

class ReflectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.setWindowTitle("Daily Reflection")
        self.resize(500, 520)
        self.setStyleSheet("background-color: #121212;")
        
        self.completed_answer = None
        self.difficult_answer = None
        self.win_answer = None
        
        layout = QVBoxLayout(self)
        layout.setSpacing(28)
        layout.setContentsMargins(36, 36, 36, 36)
        
        # Header
        header = QLabel("  Daily Reflection")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            color: #EAEAEA; 
            font-size: 24px; 
            font-weight: 600;
        """)
        layout.addWidget(header)
        
        subtitle = QLabel("Take 30 seconds to reflect on your day")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #6A6A6A; font-size: 14px;")
        layout.addWidget(subtitle)
        
        # Questions
        q1 = self.create_question("What did you complete?",
            ["Most tasks", "Some tasks", "Few", "Nothing"], self.set_completed)
        layout.addWidget(q1)
        
        q2 = self.create_question("What felt difficult?",
            ["Focus", "Time", "Energy", "Motivation"], self.set_difficult)
        layout.addWidget(q2)
        
        q3 = self.create_question("One small win?",
            ["Habit done", "Task done", "Stayed focused", "Good break"], self.set_win)
        layout.addWidget(q3)
        
        # Save
        save_btn = QPushButton("Save Reflection")
        save_btn.setFixedHeight(45)
        save_btn.setFixedWidth(200)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A5C44;
                color: #EAEAEA;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #446B4F; }
        """)
        save_btn.clicked.connect(self.save_and_close)
        layout.addWidget(save_btn, alignment=Qt.AlignCenter)
        
        layout.addStretch()

    def create_question(self, question: str, options: list, callback) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { 
                background-color: #161616; 
                border-radius: 12px;
                border: 1px solid #242424;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)
        
        q_label = QLabel(question)
        q_label.setStyleSheet("color: #9A9A9A; font-size: 13px; font-weight: 600; border: none;")
        layout.addWidget(q_label)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        for option in options:
            btn = QPushButton(option)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1A1A1A;
                    color: #6A6A6A;
                    border: 1px solid #242424;
                    padding: 8px 12px;
                    border-radius: 8px;
                    font-size: 12px;
                }
                QPushButton:checked {
                    background-color: #3A5C44;
                    color: #EAEAEA;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #242424;
                    color: #9A9A9A;
                }
            """)
            btn.clicked.connect(lambda checked, o=option: callback(o))
            btn_layout.addWidget(btn)
        
        layout.addLayout(btn_layout)
        return frame

    def set_completed(self, answer: str):
        self.completed_answer = answer

    def set_difficult(self, answer: str):
        self.difficult_answer = answer

    def set_win(self, answer: str):
        self.win_answer = answer

    def save_and_close(self):
        self.db.save_reflection(
            self.completed_answer or "",
            self.difficult_answer or "",
            self.win_answer or ""
        )
        self.accept()
