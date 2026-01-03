
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QComboBox, QDateEdit, 
                               QSpinBox, QFormLayout, QDoubleSpinBox)
from PySide6.QtCore import Qt, QDate

class AddHabitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Habit")
        self.resize(360, 200)
        self.setStyleSheet("background-color: #161616;")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)

        lbl = QLabel("Habit Name:")
        lbl.setStyleSheet("color: #9A9A9A; font-size: 12px; border: none;")
        self.layout.addWidget(lbl)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Drink Water")
        self.name_input.setFixedHeight(35)
        self.layout.addWidget(self.name_input)

        self.layout.addSpacing(10)
        
        buttons = QHBoxLayout()
        self.save_btn = QPushButton("Save Habit")
        self.save_btn.setFixedHeight(35)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A7C59; color: #EAEAEA;
                border: none; border-radius: 8px; font-weight: 600;
            }
            QPushButton:hover { background-color: #5D8C6C; }
        """)
        self.save_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(35)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #242424; color: #9A9A9A;
                border: none; border-radius: 8px;
            }
            QPushButton:hover { background-color: #2D2D2D; color: #EAEAEA; }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)
        self.layout.addLayout(buttons)

    def get_data(self):
        return self.name_input.text()

class AddTaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Task")
        self.resize(420, 400)
        self.setStyleSheet("background-color: #161616;")
        
        main_v = QVBoxLayout(self)
        main_v.setContentsMargins(30, 30, 30, 30)
        main_v.setSpacing(20)

        self.layout = QFormLayout()
        self.layout.setSpacing(15)
        self.layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.name_input = QLineEdit()
        self.name_input.setFixedHeight(35)
        self.layout.addRow(self.create_lbl("Task Name:"), self.name_input)

        self.deadline_input = QDateEdit()
        self.deadline_input.setFixedHeight(35)
        self.deadline_input.setDate(QDate.currentDate())
        self.deadline_input.setMinimumDate(QDate.currentDate())  # Prevent past dates
        self.deadline_input.setDisplayFormat("yyyy-MM-dd")  # Unambiguous format
        self.deadline_input.setCalendarPopup(True)
        self.layout.addRow(self.create_lbl("Deadline:"), self.deadline_input)

        self.priority_input = QComboBox()
        self.priority_input.setFixedHeight(35)
        self.priority_input.addItems(["Low", "Medium", "High"])
        self.layout.addRow(self.create_lbl("Priority:"), self.priority_input)

        self.points_input = QSpinBox()
        self.points_input.setFixedHeight(35)
        self.points_input.setRange(0, 100)
        self.points_input.setValue(10)
        self.layout.addRow(self.create_lbl("Points:"), self.points_input)

        self.energy_input = QComboBox()
        self.energy_input.setFixedHeight(35)
        self.energy_input.addItems(["High", "Medium", "Low"])
        self.layout.addRow(self.create_lbl("Energy:"), self.energy_input)

        # Duration input (hours to complete)
        self.duration_input = QDoubleSpinBox()
        self.duration_input.setFixedHeight(35)
        self.duration_input.setRange(0, 24)
        self.duration_input.setSingleStep(0.5)
        self.duration_input.setValue(1.0)
        self.duration_input.setSuffix(" hrs")
        self.duration_input.setDecimals(1)
        self.layout.addRow(self.create_lbl("Time to Complete:"), self.duration_input)

        main_v.addLayout(self.layout)
        main_v.addSpacing(10)

        # Buttons
        buttons = QHBoxLayout()
        self.save_btn = QPushButton("Save Task")
        self.save_btn.setFixedHeight(35)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A5C44; color: #EAEAEA;
                border: none; border-radius: 8px; font-weight: 600;
            }
            QPushButton:hover { background-color: #446B4F; }
        """)
        self.save_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(35)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #242424; color: #9A9A9A;
                border: none; border-radius: 8px;
            }
            QPushButton:hover { background-color: #2D2D2D; color: #EAEAEA; }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)
        main_v.addLayout(buttons)

    def create_lbl(self, text):
        l = QLabel(text)
        l.setStyleSheet("color: #9A9A9A; font-size: 11px; border: none;")
        return l

    def get_data(self):
        priority_map = {0: 1, 1: 2, 2: 3} # Low->1, Med->2, High->3
        return {
            "name": self.name_input.text(),
            "deadline": self.deadline_input.date().toString("yyyy-MM-dd"),
            "priority": priority_map[self.priority_input.currentIndex()],
            "points": self.points_input.value(),
            "energy_level": self.energy_input.currentText(),
            "duration_hours": self.duration_input.value()
        }
