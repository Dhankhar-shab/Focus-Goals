import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QStackedWidget, QLabel, 
                               QFrame, QGraphicsDropShadowEffect, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from .styles_loader import load_stylesheet
from .dashboard import Dashboard
from .monthly_habit_widget import MonthlyHabitWidget
from .task_widget import TaskWidget
from .rewards_widget import RewardsWidget
from .reflection_dialog import ReflectionDialog
from .focus_widget import FocusWidget
from .clock_widget import ClockWidget
from .flip_clock_widget import FlipClockWidget
from .calendar_widget import CalendarWidget

from database import DatabaseManager
from PySide6.QtCore import Qt, QTimer, QDateTime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Study Focus")
        self.resize(1280, 820)
        self.setMinimumSize(1100, 700)
        
        # Frameless Window setup
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.db = DatabaseManager()
        self.drag_pos = None
        
        # Central Widget
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #121212;")
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === SIDEBAR ===
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet("background-color: #0D0D0D;")
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 32)
        sidebar_layout.setSpacing(0)

        # Traffic Light Window Controls
        controls_frame = QWidget()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(20, 20, 20, 20)
        controls_layout.setSpacing(8)
        
        self.btn_close = self.create_control_button("#FF5F56", self.close)
        self.btn_min = self.create_control_button("#FFBD2E", self.showMinimized)
        self.btn_max = self.create_control_button("#27C93F", self.toggle_maximize)
        
        controls_layout.addWidget(self.btn_close)
        controls_layout.addWidget(self.btn_min)
        controls_layout.addWidget(self.btn_max)
        controls_layout.addStretch()
        
        sidebar_layout.addWidget(controls_frame)
        
        # Header Container (to keep existing margins for title)
        title_container = QWidget()
        title_container_layout = QVBoxLayout(title_container)
        title_container_layout.setContentsMargins(20, 0, 20, 0)
        title_container_layout.setSpacing(0)
        
        # App Title
        title_frame = QWidget()
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 40)
        title_layout.setSpacing(4)
        
        app_title = QLabel("Study")
        app_title.setStyleSheet("""
            color: #EAEAEA; 
            font-size: 24px; 
            font-weight: 600;
            letter-spacing: -0.2px;
        """)
        title_layout.addWidget(app_title)
        
        app_subtitle = QLabel("Focus")
        app_subtitle.setStyleSheet("""
            color: #4A7C59; 
            font-size: 24px; 
            font-weight: 600;
            letter-spacing: -0.2px;
        """)
        title_layout.addWidget(app_subtitle)
        
        title_container_layout.addWidget(title_frame)
        sidebar_layout.addWidget(title_container)

        # Navigation section
        nav_section = QWidget()
        nav_layout = QVBoxLayout(nav_section)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(8) # Increased spacing

        self.btn_dashboard = self.create_nav_button("⌂  Dashboard", "dashboard", True)
        self.btn_habits = self.create_nav_button("✓  Habits", "habits")
        self.btn_tasks = self.create_nav_button("📋  Tasks", "tasks")
        self.btn_focus = self.create_nav_button("⏱  Focus", "focus")
        self.btn_rewards = self.create_nav_button("🏆  Rewards", "rewards")
        self.btn_calendar = self.create_nav_button("📅  Calendar", "calendar")
        self.btn_clock_section = self.create_nav_button("🕒  Clock", "clock_section")
        
        nav_layout.addWidget(self.btn_dashboard)
        nav_layout.addWidget(self.btn_habits)
        nav_layout.addWidget(self.btn_tasks)
        nav_layout.addWidget(self.btn_focus)
        nav_layout.addWidget(self.btn_rewards)
        nav_layout.addWidget(self.btn_calendar)
        nav_layout.addWidget(self.btn_clock_section)
        
        sidebar_layout.addWidget(nav_section)
        sidebar_layout.addStretch()
        
        # Sidebar Clock (Bottom)
        self.clock_container = ClockWidget()
        
        # Only show if not disabled in settings
        is_clock_visible = self.db.get_setting('clock_visible', 'true') == 'true'
        self.clock_container.setVisible(is_clock_visible)
        
        sidebar_layout.addWidget(self.clock_container)
        
        # Daily Reflection Button (bottom)
        self.btn_reflect = QPushButton("✨  Daily Reflection")
        self.btn_reflect.setCursor(Qt.PointingHandCursor)
        self.btn_reflect.setStyleSheet("""
            QPushButton {
                background-color: #161616;
                color: #9A9A9A;
                border: 1px solid #242424;
                border-radius: 10px;
                padding: 12px 14px;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #1A1A1A;
                color: #EAEAEA;
            }
        """)
        self.btn_reflect.clicked.connect(self.open_reflection)
        sidebar_layout.addWidget(self.btn_reflect)

        # === CONTENT AREA ===
        content_container = QWidget()
        content_container.setStyleSheet("background-color: #121212;")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet("background-color: #121212;")
        
        self.page_dashboard = Dashboard()
        self.page_habits = MonthlyHabitWidget()
        self.page_tasks = TaskWidget()
        self.page_focus = FocusWidget(self.db)
        self.page_rewards = RewardsWidget()
        self.page_calendar = CalendarWidget()
        self.page_clock_section = FlipClockWidget(mode="auto")

        self.content_area.addWidget(self.page_dashboard)
        self.content_area.addWidget(self.page_habits)
        self.content_area.addWidget(self.page_tasks)
        self.content_area.addWidget(self.page_focus)
        self.content_area.addWidget(self.page_rewards)
        self.content_area.addWidget(self.page_calendar)
        self.content_area.addWidget(self.page_clock_section)
        
        content_layout.addWidget(self.content_area)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content_container)

        # Default
        self.btn_dashboard.setChecked(True)
        self.content_area.setCurrentWidget(self.page_dashboard)

        # Signals
        self.page_habits.points_updated.connect(self.refresh_all)
        self.page_tasks.points_updated.connect(self.refresh_all)
        self.page_rewards.points_updated.connect(self.refresh_all)

        self.setStyleSheet(load_stylesheet())

    def create_nav_button(self, text, page_name, checked=False):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setChecked(checked)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6A6A6A;
                text-align: left;
                padding: 10px 14px;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #161616;
                color: #9A9A9A;
            }
            QPushButton:checked {
                background-color: #1A1A1A;
                color: #EAEAEA;
                font-weight: 600;
            }
        """)
        btn.clicked.connect(lambda: self.switch_page(page_name))
        return btn

    def create_control_button(self, color, callback):
        btn = QPushButton()
        btn.setFixedSize(12, 12)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {color}CC;
            }}
        """)
        btn.clicked.connect(callback)
        return btn

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    def switch_page(self, page_name):
        pages = {
            "dashboard": self.page_dashboard,
            "habits": self.page_habits,
            "tasks": self.page_tasks,
            "focus": self.page_focus,
            "rewards": self.page_rewards,
            "calendar": self.page_calendar,
            "clock_section": self.page_clock_section,
        }
        if page_name in pages:
            self.content_area.setCurrentWidget(pages[page_name])
            if page_name == "dashboard":
                self.page_dashboard.refresh_stats()

    def open_reflection(self):
        dialog = ReflectionDialog(self)
        dialog.exec()

    def refresh_all(self):
        self.page_dashboard.refresh_stats()
        self.page_rewards.refresh_rewards()



