import os
import json
import calendar
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QGridLayout, QScrollArea,
                               QDialog, QLineEdit, QTextEdit, QTimeEdit, 
                               QMessageBox, QSizePolicy)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QColor, QFont

class EventDialog(QDialog):
    # Signal to delete event: (date_str, index)
    delete_requested = Signal(str, int)

    def __init__(self, parent=None, date=None, event_data=None, event_index=None):
        super().__init__(parent)
        self.edit_mode = event_data is not None
        self.setWindowTitle("Edit Event" if self.edit_mode else "Create Event")
        self.setFixedWidth(400)
        self.date = date or QDate.currentDate()
        self.event_data = event_data
        self.event_index = event_index
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        # Title
        layout.addWidget(QLabel("Event Title"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter event title...")
        if self.edit_mode:
            self.title_input.setText(self.event_data.get('title', ''))
        layout.addWidget(self.title_input)

        # Date Display
        layout.addWidget(QLabel(f"Date: {self.date.toString('MMMM d, yyyy')}"))

        # Time
        layout.addWidget(QLabel("Time"))
        self.time_input = QTimeEdit()
        if self.edit_mode and 'time' in self.event_data:
            try:
                time = datetime.strptime(self.event_data['time'], "%I:%M %p").time()
                self.time_input.setTime(time)
            except:
                self.time_input.setTime(datetime.now().time())
        else:
            self.time_input.setTime(datetime.now().time())
        layout.addWidget(self.time_input)

        # Description
        layout.addWidget(QLabel("Description"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(100)
        if self.edit_mode:
            self.desc_input.setPlainText(self.event_data.get('description', ''))
        layout.addWidget(self.desc_input)

        # Buttons
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        if self.edit_mode:
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("background-color: #dc3545; color: white; border-radius: 8px; padding: 8px 16px;")
            delete_btn.clicked.connect(self.handle_delete)
            btn_layout.addWidget(delete_btn)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def handle_delete(self):
        if QMessageBox.question(self, "Confirm Delete", 
                               "Are you sure you want to delete this event?",
                               QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.delete_requested.emit(self.date.toString("yyyy-MM-dd"), self.event_index)
            self.done(2) # Custom return code for delete

    def get_data(self):
        """Extract and clean data from inputs for storage"""
        time_str = self.time_input.time().toString("hh:mm AP")
        return {
            "title": self.title_input.text().strip(),
            "time": time_str,
            "description": self.desc_input.toPlainText().strip()
        }

class EventLabel(QLabel):
    clicked = Signal(int) # index of event

    def __init__(self, text, index, parent=None):
        super().__init__(text, parent)
        self.index = index
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QLabel {
                font-size: 10px; 
                color: #9A9A9A; 
                background-color: #242424; 
                border-radius: 2px; 
                padding: 1px 3px;
            }
            QLabel:hover {
                background-color: #2D2D2D;
                color: #EAEAEA;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index)

class EventCard(QFrame):
    edit_requested = Signal(str, int) # date_str, index

    def __init__(self, date_str, index, event_data, parent=None):
        super().__init__(parent)
        self.date_str = date_str
        self.index = index
        self.event_data = event_data
        self.expanded = False
        self.init_ui()

    def init_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            EventCard {
                border: 1px solid #2D2D2D;
                border-radius: 8px;
                background-color: #161616;
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Header section
        self.header_frame = QFrame()
        self.header_frame.setCursor(Qt.PointingHandCursor)
        self.header_frame.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
        """)
        header_layout = QVBoxLayout(self.header_frame)
        header_layout.setContentsMargins(12, 12, 12, 12)
        header_layout.setSpacing(4)

        date_lbl = QLabel(f"📅 {self.date_str}")
        date_lbl.setStyleSheet("font-size: 11px; color: #4A7C59; font-weight: bold;")
        header_layout.addWidget(date_lbl)

        title_lbl = QLabel(self.event_data['title'])
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #EAEAEA;")
        title_lbl.setWordWrap(True)
        header_layout.addWidget(title_lbl)

        time_lbl = QLabel(f"🕐 {self.event_data.get('time', 'No time set')}")
        time_lbl.setStyleSheet("font-size: 11px; color: #9A9A9A;")
        header_layout.addWidget(time_lbl)

        self.main_layout.addWidget(self.header_frame)

        # Detail section
        self.detail_frame = QFrame()
        self.detail_frame.setVisible(False)
        self.detail_frame.setStyleSheet("background-color: #161616;")
        detail_layout = QVBoxLayout(self.detail_frame)
        detail_layout.setContentsMargins(12, 0, 12, 12)
        detail_layout.setSpacing(8)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #2D2D2D;")
        detail_layout.addWidget(line)

        desc_title = QLabel("Description:")
        desc_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #4A4A4A;")
        detail_layout.addWidget(desc_title)

        desc_lbl = QLabel(self.event_data.get('description', 'No description'))
        desc_lbl.setStyleSheet("font-size: 12px; color: #9A9A9A;")
        desc_lbl.setWordWrap(True)
        detail_layout.addWidget(desc_lbl)

        edit_btn = QPushButton("✏️ Edit Event")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                color: #EAEAEA;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
            }
        """)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.date_str, self.index))
        detail_layout.addWidget(edit_btn)

        self.main_layout.addWidget(self.detail_frame)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_expand()

    def toggle_expand(self):
        self.expanded = not self.expanded
        self.detail_frame.setVisible(self.expanded)
        # Handle rounded corners for the very bottom when expanded
        if self.expanded:
            self.header_frame.setStyleSheet("""
                QFrame {
                    background-color: #1A1A1A;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                }
            """)
        else:
            self.header_frame.setStyleSheet("""
                QFrame {
                    background-color: #1A1A1A;
                    border-radius: 8px;
                }
            """)

class DayCell(QFrame):
    clicked = Signal(QDate)
    event_clicked = Signal(QDate, int) # date, index

    def __init__(self, date, is_current_month=True, parent=None):
        super().__init__(parent)
        self.date = date
        self.is_current_month = is_current_month
        self.init_ui()

    def init_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(2)

        # Day Number
        self.day_label = QLabel(str(self.date.day()))
        self.day_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        
        if not self.is_current_month:
            self.day_label.setStyleSheet("color: #4A4A4A;")
            self.setStyleSheet("border: 1px solid #1A1A1A;")
        elif self.date == QDate.currentDate():
            self.day_label.setStyleSheet("color: #4A7C59; font-weight: bold;")
            self.setStyleSheet("background-color: #1A1A1A; border: 1px solid #4A7C59;")
        else:
            self.day_label.setStyleSheet("color: #EAEAEA;")
            self.setStyleSheet("border: 1px solid #2D2D2D;")
        
        self.layout.addWidget(self.day_label)

        # Events Container
        self.events_widget = QWidget()
        self.events_layout = QVBoxLayout(self.events_widget)
        self.events_layout.setContentsMargins(0, 0, 0, 0)
        self.events_layout.setSpacing(2)
        self.layout.addWidget(self.events_widget)
        self.layout.addStretch()

    def mousePressEvent(self, event):
        # Prevent triggering date click if clicking on child widgets
        if not self.childAt(event.pos()):
            self.clicked.emit(self.date)

    def add_event_labels(self, events):
        # Clear existing
        for i in reversed(range(self.events_layout.count())):
            self.events_layout.itemAt(i).widget().setParent(None)
        
        for i, event in enumerate(events[:3]):
            lbl = EventLabel(f"• {event['title']}", i)
            lbl.clicked.connect(lambda idx: self.event_clicked.emit(self.date, idx))
            self.events_layout.addWidget(lbl)
        
        if len(events) > 3:
            more_lbl = QLabel(f"+{len(events)-3} more")
            more_lbl.setStyleSheet("font-size: 9px; color: #4A7C59;")
            self.events_layout.addWidget(more_lbl)

class CalendarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_date = QDate.currentDate()
        self.events_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "events.json")
        self.events = self.load_events()
        self.init_ui()

    def load_events(self):
        if os.path.exists(self.events_file):
            try:
                with open(self.events_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_events(self):
        os.makedirs(os.path.dirname(self.events_file), exist_ok=True)
        with open(self.events_file, 'w') as f:
            json.dump(self.events, f, indent=2)

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # --- Sidebar ---
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)

        # Mini Calendar Grid
        mini_cal_label = QLabel("Mini Calendar")
        mini_cal_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #EAEAEA;")
        sidebar_layout.addWidget(mini_cal_label)
        
        self.mini_grid_container = QWidget()
        self.mini_grid_layout = QGridLayout(self.mini_grid_container)
        self.mini_grid_layout.setSpacing(2)
        self.mini_grid_layout.setContentsMargins(0, 5, 0, 15)
        sidebar_layout.addWidget(self.mini_grid_container)

        # Upcoming Events Label
        upcoming_label = QLabel("Upcoming Events")
        upcoming_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #EAEAEA;")
        sidebar_layout.addWidget(upcoming_label)

        # Scroll Area for Event Cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                width: 4px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #2D2D2D;
                border-radius: 2px;
            }
        """)
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: transparent;")
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(0, 10, 8, 10)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch()
        
        self.scroll_area.setWidget(self.scroll_content)
        sidebar_layout.addWidget(self.scroll_area)

        main_layout.addWidget(sidebar)

        # --- Main Calendar ---
        calendar_container = QWidget()
        calendar_layout = QVBoxLayout(calendar_container)
        calendar_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header_layout = QHBoxLayout()
        
        self.month_year_label = QLabel()
        self.month_year_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #EAEAEA;")
        header_layout.addWidget(self.month_year_label)
        
        header_layout.addStretch()

        prev_btn = QPushButton("◀")
        prev_btn.setFixedSize(40, 40)
        prev_btn.clicked.connect(self.prev_month)
        header_layout.addWidget(prev_btn)

        today_btn = QPushButton("Today")
        today_btn.setStyleSheet("padding: 5px 15px;")
        today_btn.clicked.connect(self.go_today)
        header_layout.addWidget(today_btn)

        next_btn = QPushButton("▶")
        next_btn.setFixedSize(40, 40)
        next_btn.clicked.connect(self.next_month)
        header_layout.addWidget(next_btn)

        create_btn = QPushButton("+ Create Event")
        create_btn.setObjectName("primary")
        create_btn.clicked.connect(lambda: self.open_event_dialog(QDate.currentDate()))
        header_layout.addWidget(create_btn)

        calendar_layout.addLayout(header_layout)
        calendar_layout.addSpacing(20)

        # Grid Header (Days of week)
        days_header = QGridLayout()
        days_header.setSpacing(1)
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for i, day in enumerate(days):
            lbl = QLabel(day)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #9A9A9A; font-weight: bold; padding: 10px; background-color: #161616;")
            days_header.addWidget(lbl, 0, i)
        calendar_layout.addLayout(days_header)

        # Main Grid
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(1)
        calendar_layout.addLayout(self.grid_layout)
        calendar_layout.addStretch()

        main_layout.addWidget(calendar_container)

        self.update_calendar()

    def update_calendar(self):
        # Update labels
        self.month_year_label.setText(self.current_date.toString("MMMM yyyy"))
        
        # Update mini calendar
        self.update_mini_calendar()

        # Clear grid
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        # Fill grid
        year = self.current_date.year()
        month = self.current_date.month()
        first_day = QDate(year, month, 1)
        start_padding = first_day.dayOfWeek() % 7

        # Days from previous month
        prev_month_last_day = first_day.addDays(-1)
        for i in range(start_padding):
            date = prev_month_last_day.addDays(- (start_padding - i - 1))
            cell = DayCell(date, is_current_month=False)
            cell.clicked.connect(self.handle_date_click)
            cell.event_clicked.connect(self.handle_event_click)
            self.grid_layout.addWidget(cell, 0, i)

        # Days of current month
        days_in_month = first_day.daysInMonth()
        for day in range(1, days_in_month + 1):
            date = QDate(year, month, day)
            cell = DayCell(date, is_current_month=True)
            cell.clicked.connect(self.handle_date_click)
            cell.event_clicked.connect(self.handle_event_click)
            
            date_str = date.toString("yyyy-MM-dd")
            if date_str in self.events:
                cell.add_event_labels(self.events[date_str])
            
            pos = start_padding + day - 1
            self.grid_layout.addWidget(cell, pos // 7, pos % 7)

        # Days from next month (fill up to 6 rows)
        current_pos = start_padding + days_in_month
        next_month_day = 1
        while current_pos < 42:
            date = QDate(year, month, days_in_month).addDays(next_month_day)
            cell = DayCell(date, is_current_month=False)
            cell.clicked.connect(self.handle_date_click)
            cell.event_clicked.connect(self.handle_event_click)
            self.grid_layout.addWidget(cell, current_pos // 7, current_pos % 7)
            current_pos += 1
            next_month_day += 1

        self.update_events_list()

    def update_mini_calendar(self):
        # Clear mini grid
        for i in reversed(range(self.mini_grid_layout.count())):
            item = self.mini_grid_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        year = self.current_date.year()
        month = self.current_date.month()
        today = QDate.currentDate()
        
        # Day headers
        days = ["S", "M", "T", "W", "T", "F", "S"]
        for i, d in enumerate(days):
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 9px; color: #4A4A4A; font-weight: bold;")
            self.mini_grid_layout.addWidget(lbl, 0, i)

        first_day = QDate(year, month, 1)
        start_padding = first_day.dayOfWeek() % 7
        
        # Mini cells
        pos = 7
        # Padding
        for i in range(start_padding):
            lbl = QLabel("")
            self.mini_grid_layout.addWidget(lbl, pos // 7, pos % 7)
            pos += 1
            
        for day in range(1, first_day.daysInMonth() + 1):
            date = QDate(year, month, day)
            lbl = QLabel(str(day))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedSize(20, 20)
            
            if date == today:
                lbl.setStyleSheet("background-color: #4A7C59; color: white; border-radius: 10px; font-size: 10px;")
            else:
                lbl.setStyleSheet("font-size: 10px; color: #9A9A9A;")
                
            self.mini_grid_layout.addWidget(lbl, pos // 7, pos % 7)
            pos += 1

    def update_events_list(self):
        # Clears all widgets and stretches from the layout safely
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.spacerItem():
                pass # Stretches are removed by takeAt

        today = QDate.currentDate()
        
        all_events = []
        for date_str, events in self.events.items():
            try:
                # V5 Robustness: Explicitly validate the date string
                date = QDate.fromString(date_str, "yyyy-MM-dd")
                if not date.isValid() or date < today:
                    continue
                
                for idx, event in enumerate(events):
                    # Ensure event is a dictionary and has a title
                    if isinstance(event, dict) and event.get('title'):
                        all_events.append((date, idx, event))
            except (ValueError, TypeError):
                # Skip corrupted or invalid meeting entries
                continue

        # V5 Sorting: Finalized chronological helper
        def get_sortable_time(event_dict):
            time_str = event_dict.get('time', '')
            if not time_str:
                return "00:00"
            try:
                # Handle AM/PM logic more strictly
                dt = datetime.strptime(time_str.upper(), "%I:%M %p")
                return dt.strftime("%H:%M")
            except ValueError:
                # Handle cases like "10:00AM" (missing space) or invalid strings
                try:
                    dt = datetime.strptime(time_str.upper().replace(" ", ""), "%I:%M%p")
                    return dt.strftime("%H:%M")
                except:
                    return "00:00"

        # Sort by actual QDate first, then by the 24h helper string
        all_events.sort(key=lambda x: (x[0], get_sortable_time(x[2])))
        
        for date, idx, event_data in all_events:
            card = EventCard(date.toString("yyyy-MM-dd"), idx, event_data)
            card.edit_requested.connect(self.handle_edit_request)
            self.cards_layout.addWidget(card)
        
        # Add a stretch at the end to keep cards at the top
        self.cards_layout.addStretch()

    def handle_date_click(self, date):
        if date < QDate.currentDate():
            QMessageBox.warning(self, "Invalid Date", "Cannot create events in the past.")
            return
        self.open_event_dialog(date)

    def handle_event_click(self, date, index):
        date_str = date.toString("yyyy-MM-dd")
        if date_str in self.events and index < len(self.events[date_str]):
            self.open_event_dialog(date, self.events[date_str][index], index)

    def handle_edit_request(self, date_str, index):
        date = QDate.fromString(date_str, "yyyy-MM-dd")
        if date_str in self.events and index < len(self.events[date_str]):
            self.open_event_dialog(date, self.events[date_str][index], index)

    def open_event_dialog(self, date, event_data=None, event_index=None):
        dialog = EventDialog(self, date, event_data, event_index)
        dialog.delete_requested.connect(self.delete_event)
        
        result = dialog.exec()
        if result == QDialog.Accepted:
            data = dialog.get_data()
            if not data['title']:
                return
            
            date_str = date.toString("yyyy-MM-dd")
            if date_str not in self.events:
                self.events[date_str] = []
                
            if event_data is not None:
                # Update existing
                self.events[date_str][event_index] = data
            else:
                # Add new
                self.events[date_str].append(data)
            
            self.save_events()
            self.update_calendar()
        elif result == 2: # Delete return code
            # Handled by signal
            pass

    def delete_event(self, date_str, index):
        if date_str in self.events and index < len(self.events[date_str]):
            del self.events[date_str][index]
            if not self.events[date_str]:
                del self.events[date_str]
            self.save_events()
            self.update_calendar()

    def prev_month(self):
        self.current_date = self.current_date.addMonths(-1)
        self.update_calendar()

    def next_month(self):
        self.current_date = self.current_date.addMonths(1)
        self.update_calendar()

    def go_today(self):
        self.current_date = QDate.currentDate()
        self.update_calendar()
