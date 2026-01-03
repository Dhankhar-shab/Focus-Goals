from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea, QFrame, QMessageBox,
                               QGraphicsDropShadowEffect, QGridLayout, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from database import DatabaseManager
from points_manager import PointsManager
from .dialogs import AddHabitDialog
from datetime import datetime

class HabitWidget(QWidget):
    points_updated = Signal()
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.points_mgr = PointsManager(self.db)
        self.setStyleSheet("background-color: #121212;")
        
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(24)
        self.layout.setContentsMargins(48, 48, 48, 48)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Habits")
        title.setStyleSheet("""
            font-size: 32px; 
            font-weight: 600; 
            color: #E5E5E5;
            letter-spacing: -0.5px;
        """)
        header.addWidget(title)
        header.addStretch()
        
        add_btn = QPushButton("+  New Habit")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: #FFFFFF;
                border: none;
                padding: 12px 24px;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #5A9DE8; }
            QPushButton:pressed { background-color: #3A80D2; }
        """)
        add_btn.clicked.connect(self.open_add_dialog)
        header.addWidget(add_btn)
        
        self.layout.addLayout(header)

        # Subtitle
        subtitle = QLabel("Track your daily progress · Done (+2) · Partial (+1) · Missed (0)")
        subtitle.setStyleSheet("color: #6A6A6A; font-size: 13px;")
        self.layout.addWidget(subtitle)

        # Scroll Area with Grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)

        self.refresh_habits()

    def add_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 8)
        widget.setGraphicsEffect(shadow)

    def open_add_dialog(self):
        dialog = AddHabitDialog(self)
        if dialog.exec():
            name = dialog.get_data()
            if name:
                self.db.add_habit(name)
                self.refresh_habits()

    def refresh_habits(self):
        # Clear grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        habits = self.db.get_habits()
        
        if not habits:
            empty = QLabel("No habits yet.\nClick 'New Habit' to create your first one.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #6A6A6A; font-size: 15px; padding: 80px;")
            self.grid_layout.addWidget(empty, 0, 0, 1, 3)
            return
        
        # Grid: 3 columns
        for idx, habit in enumerate(habits):
            h_id, h_name, _ = habit
            row = idx // 3
            col = idx % 3
            card = self.create_habit_card(h_id, h_name)
            self.grid_layout.addWidget(card, row, col)

    def create_habit_card(self, habit_id: int, name: str) -> QFrame:
        card = QFrame()
        card.setFixedSize(320, 200)
        card.setStyleSheet("""
            QFrame { 
                background-color: #1C1C1C; 
                border-radius: 16px;
            }
        """)
        self.add_shadow(card)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)
        
        # Top Row: Name + Streak + Delete
        top_row = QHBoxLayout()
        
        name_label = QLabel(name)
        name_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #E5E5E5;")
        name_label.setWordWrap(True)
        top_row.addWidget(name_label, 1)
        
        # Streak badge
        streak = self.db.get_habit_streak(habit_id)
        if streak > 0:
            streak_label = QLabel(f"🔥 {streak}")
            streak_label.setStyleSheet("""
                background-color: #3D2E1E; 
                color: #E2A04A; 
                padding: 4px 10px; 
                border-radius: 8px;
                font-size: 11px;
                font-weight: 600;
            """)
            top_row.addWidget(streak_label)
        
        # Delete button
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(28, 28)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton {
                background: #2D2D2D; color: #E25C5C; border: none; 
                border-radius: 8px; font-size: 12px;
            }
            QPushButton:hover { background: #E25C5C; color: #1E1E1E; }
        """)
        del_btn.clicked.connect(lambda: self.delete_habit(habit_id))
        top_row.addWidget(del_btn)
        
        layout.addLayout(top_row)
        
        # Weekly Progress Dots (M T W T F S S)
        week_points = self.db.get_week_habit_points(habit_id)
        week_row = QHBoxLayout()
        week_row.setSpacing(8)
        days = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
        
        for day, pts in zip(days, week_points):
            day_container = QVBoxLayout()
            day_container.setSpacing(4)
            
            day_lbl = QLabel(day)
            day_lbl.setAlignment(Qt.AlignCenter)
            day_lbl.setStyleSheet("font-size: 10px; color: #6A6A6A; font-weight: 600;")
            
            dot = QFrame()
            dot.setFixedSize(12, 12)
            if pts == 2:
                dot.setStyleSheet("background-color: #4CAF7C; border-radius: 6px;")
            elif pts == 1:
                dot.setStyleSheet("background-color: #E2A04A; border-radius: 6px;")
            else:
                dot.setStyleSheet("background-color: #2D2D2D; border-radius: 6px;")
            
            day_container.addWidget(day_lbl, alignment=Qt.AlignCenter)
            day_container.addWidget(dot, alignment=Qt.AlignCenter)
            week_row.addLayout(day_container)
        
        week_row.addStretch()
        layout.addLayout(week_row)
        
        layout.addStretch()
        
        # Status Buttons - Large, Pressable
        current_status = self.db.get_todays_habit_status(habit_id)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        
        btn_missed = self.create_status_btn("✕ Missed", current_status == 0, "#4A4A4A", "#8A8A8A")
        btn_partial = self.create_status_btn("◐ Partial", current_status == 1, "#3D2E1E", "#E2A04A")
        btn_done = self.create_status_btn("✓ Done", current_status == 2, "#1E3D2E", "#4CAF7C")
        
        btn_missed.clicked.connect(lambda: self.update_status(habit_id, 0))
        btn_partial.clicked.connect(lambda: self.update_status(habit_id, 1))
        btn_done.clicked.connect(lambda: self.update_status(habit_id, 2))
        
        btn_row.addWidget(btn_missed)
        btn_row.addWidget(btn_partial)
        btn_row.addWidget(btn_done)
        
        layout.addLayout(btn_row)
        
        return card

    def create_status_btn(self, text: str, is_active: bool, bg_color: str, fg_color: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        if is_active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: {fg_color};
                    border: 2px solid {fg_color};
                    padding: 10px 8px;
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: 600;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #1E1E1E;
                    color: #6A6A6A;
                    border: 1px solid #2D2D2D;
                    padding: 10px 8px;
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: 400;
                }}
                QPushButton:hover {{
                    background-color: #2D2D2D;
                    color: #E5E5E5;
                }}
            """)
        return btn

    def update_status(self, habit_id: int, status: int):
        today = datetime.now().strftime("%Y-%m-%d")
        old_status = self.db.get_todays_habit_status(habit_id)
        self.db.log_habit(habit_id, today, status)
        
        if status > old_status:
            self.db.add_points(status - old_status)
        elif status < old_status:
            self.db.deduct_points(old_status - status)
        
        self.points_updated.emit()
        self.refresh_habits()

    def delete_habit(self, habit_id: int):
        reply = QMessageBox.question(
            self, "Delete Habit", 
            "Delete this habit and all logs?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_habit(habit_id)
            self.refresh_habits()
