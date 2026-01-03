from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea, QFrame, QCheckBox,
                               QMessageBox, QDialog, QComboBox, QDateEdit,
                               QFormLayout, QDialogButtonBox, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QColor
from database import DatabaseManager
from points_manager import PointsManager
from .dialogs import AddTaskDialog

class PostponeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Postpone Task")
        self.resize(380, 200)
        self.setStyleSheet("background: #1E1E1E; border-radius: 16px;")
        
        layout = QFormLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)
        
        self.reason_combo = QComboBox()
        self.reason_combo.addItems(["Too hard", "No time", "Low energy", "Other priorities"])
        layout.addRow(QLabel("Reason:"), self.reason_combo)
        
        self.new_date = QDateEdit()
        self.new_date.setDate(QDate.currentDate().addDays(1))
        self.new_date.setMinimumDate(QDate.currentDate().addDays(1))  # Must be future date
        self.new_date.setDisplayFormat("yyyy-MM-dd")  # Unambiguous format
        self.new_date.setCalendarPopup(True)
        layout.addRow(QLabel("New Date:"), self.new_date)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def get_data(self):
        return {
            'reason': self.reason_combo.currentText(),
            'new_deadline': self.new_date.date().toString("yyyy-MM-dd")
        }

class TaskWidget(QWidget):
    points_updated = Signal()
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.points_mgr = PointsManager(self.db)
        self.filter_energy = None
        self.setStyleSheet("background-color: #121212;")
        
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(24)
        self.layout.setContentsMargins(48, 48, 48, 48)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Tasks")
        title.setStyleSheet("""
            font-size: 24px; 
            font-weight: 600; 
            color: #EAEAEA;
            letter-spacing: -0.2px;
        """)
        header.addWidget(title)
        header.addStretch()
        
        # Filter
        self.energy_filter = QComboBox()
        self.energy_filter.addItems(["All", "High", "Medium", "Low"])
        self.energy_filter.currentTextChanged.connect(self.on_filter_changed)
        header.addWidget(self.energy_filter)
        
        add_btn = QPushButton("+  New Task")
        add_btn.setFixedSize(110, 32)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E1E1E;
                color: #9A9A9A;
                border: 1px solid #2D2D2D;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #242424; color: #EAEAEA; }
        """)
        add_btn.clicked.connect(self.open_add_dialog)
        header.addWidget(add_btn)
        
        self.layout.addLayout(header)

        # Top 3 Banner
        self.top3_frame = QFrame()
        self.top3_frame.setStyleSheet("""
            QFrame { 
                background-color: #1A1A1A;
                border-radius: 10px;
            }
        """)
        top3_layout = QHBoxLayout(self.top3_frame)
        top3_layout.setContentsMargins(18, 14, 18, 14)
        
        self.top3_label = QLabel("★  Top 3: Select your 3 most important tasks")
        self.top3_label.setStyleSheet("color: #9A9A9A; font-weight: 600; font-size: 12px;")
        top3_layout.addWidget(self.top3_label)
        
        self.layout.addWidget(self.top3_frame)

        # Scroll
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignTop)
        self.container_layout.setSpacing(14)
        
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)

        self.refresh_tasks()

    def add_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 6)
        widget.setGraphicsEffect(shadow)

    def on_filter_changed(self, text: str):
        self.filter_energy = None if text == "All" else text
        self.refresh_tasks()

    def open_add_dialog(self):
        dialog = AddTaskDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data["name"]:
                self.db.add_task(data["name"], data["deadline"], data["priority"], 
                                data["points"], data["energy_level"], data["duration_hours"])
                self.refresh_tasks()

    def refresh_tasks(self):
        for i in reversed(range(self.container_layout.count())): 
            widget = self.container_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        tasks = self.db.get_tasks(include_completed=False, energy_level=self.filter_energy)
        top3_count = self.db.get_top3_count()
        
        self.top3_label.setText(f"★  Top 3: {top3_count}/3 selected")
        
        if not tasks:
            empty = QLabel("No tasks yet.\nClick 'New Task' to get started.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #6A6A6A; font-size: 15px; padding: 60px;")
            self.container_layout.addWidget(empty)
            return
        
        for task in tasks:
            self.add_task_card(task)

    def add_task_card(self, task):
        # Handle both old (8 columns) and new (9 columns with duration) task tuples
        if len(task) >= 9:
            t_id, name, deadline, priority, points, is_completed, energy, is_top3, duration_hours = task[:9]
        else:
            t_id, name, deadline, priority, points, is_completed, energy, is_top3 = task[:8]
            duration_hours = 0
        
        card = QFrame()
        priority_colors = {3: "#8C4646", 2: "#9A7B1C", 1: "#3A5C44"}
        border_color = priority_colors.get(priority, "#242424")
        
        # Highlight Top 3 with subtle glow
        if is_top3:
            card.setStyleSheet(f"""
                QFrame {{ 
                    background-color: #1C1C1C; 
                    border-radius: 12px;
                    border-left: 3px solid #9A7B1C;
                }}
            """)
        else:
            card.setStyleSheet(f"""
                QFrame {{ 
                    background-color: #181818; 
                    border-radius: 12px;
                    border-left: 3px solid {border_color};
                }}
            """)
        self.add_shadow(card)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 16, 16, 16)

        # Checkbox
        chk = QCheckBox()
        chk.setStyleSheet("""
            QCheckBox::indicator { 
                width: 20px; height: 20px; 
                border: 1px solid #3D3D3D;
                border-radius: 10px;
                background: #1A1A1A;
            }
            QCheckBox::indicator:hover { border-color: #4A7C59; }
            QCheckBox::indicator:checked {
                background: #3A5C44;
                border-color: #446B4F;
            }
        """)
        chk.setCursor(Qt.PointingHandCursor)
        chk.clicked.connect(lambda: self.complete_task(t_id))
        layout.addWidget(chk)

        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        name_row = QHBoxLayout()
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #EAEAEA;")
        name_row.addWidget(name_lbl)
        
        if is_top3:
            star = QLabel("★")
            star.setStyleSheet("color: #E2A04A; font-size: 14px;")
            name_row.addWidget(star)
        name_row.addStretch()
        info_layout.addLayout(name_row)
        
        priority_names = {3: "High", 2: "Medium", 1: "Low"}
        
        # Format duration display
        if duration_hours and duration_hours > 0:
            if duration_hours >= 1:
                duration_str = f"{duration_hours:.1f}h".rstrip('0').rstrip('.')
            else:
                duration_str = f"{int(duration_hours * 60)}m"
            details = f"{deadline or 'No deadline'} · {duration_str} · {priority_names.get(priority, '')} · {points} pts"
        else:
            details = f"{deadline or 'No deadline'} · {priority_names.get(priority, '')} · {points} pts · {energy}"
        
        details_lbl = QLabel(details)
        details_lbl.setStyleSheet("color: #6A6A6A; font-size: 12px;")
        info_layout.addWidget(details_lbl)
        
        layout.addLayout(info_layout, 1)

        # Actions
        actions = QHBoxLayout()
        actions.setSpacing(8)
        
        if not is_top3 and self.db.get_top3_count() < 3:
            star_btn = self.create_icon_btn("☆", "#2D2A1E", "#E2A04A")
            star_btn.setToolTip("Add to Top 3")
            star_btn.clicked.connect(lambda: self.toggle_top3(t_id, True))
            actions.addWidget(star_btn)
        elif is_top3:
            unstar_btn = self.create_icon_btn("★", "#E2A04A", "#1E1E1E")
            unstar_btn.setToolTip("Remove from Top 3")
            unstar_btn.clicked.connect(lambda: self.toggle_top3(t_id, False))
            actions.addWidget(unstar_btn)
        
        postpone_btn = self.create_icon_btn("🕒", "#2D2D2D", "#8A8A8A")
        postpone_btn.setToolTip("Postpone")
        postpone_btn.clicked.connect(lambda: self.postpone_task(t_id))
        actions.addWidget(postpone_btn)
        
        del_btn = self.create_icon_btn("✕", "#2D1E1E", "#E25C5C")
        del_btn.setToolTip("Delete")
        del_btn.clicked.connect(lambda: self.delete_task(t_id))
        actions.addWidget(del_btn)
        
        layout.addLayout(actions)
        self.container_layout.addWidget(card)

    def create_icon_btn(self, icon: str, bg: str, fg: str) -> QPushButton:
        btn = QPushButton(icon)
        btn.setFixedSize(34, 34)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg}; color: {fg}; border: none; 
                border-radius: 10px; font-size: 14px;
            }}
            QPushButton:hover {{ background: {fg}; color: {bg}; }}
        """)
        return btn

    def toggle_top3(self, task_id: int, add: bool):
        self.db.set_task_top3(task_id, add)
        self.refresh_tasks()

    def complete_task(self, task_id: int):
        points = self.points_mgr.award_task_points(task_id)
        QMessageBox.information(self, "Done!", f"Earned {points} points!")
        self.points_updated.emit()
        self.refresh_tasks()

    def postpone_task(self, task_id: int):
        dialog = PostponeDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.db.postpone_task(task_id, data['reason'], data['new_deadline'])
            self.refresh_tasks()

    def delete_task(self, task_id: int):
        reply = QMessageBox.question(self, "Delete", "Delete this task?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_task(task_id)
            self.refresh_tasks()
