import calendar
from datetime import datetime, date
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QPushButton, QScrollArea, QFrame, QGridLayout, 
                                QSizePolicy, QSpacerItem, QProgressBar, QMessageBox)
from PySide6.QtCore import Qt, Signal, QSize, QPointF
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QFont, QPainterPath
from database import DatabaseManager
from points_manager import PointsManager
from .dialogs import AddHabitDialog

# Global reference for today's date (updated at runtime)
TODAY_DATE = date.today()

class MonthlyHabitWidget(QWidget):
    points_updated = Signal()
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.points_mgr = PointsManager(self.db)
        
        # Current view state
        now = datetime.now()
        self.current_year = now.year
        self.current_month = now.month
        
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0) # Controlled via explicit spacers
        self.layout.setContentsMargins(60, 40, 60, 40) # Airy horizontal padding
        self.setStyleSheet("background-color: #121212;")

        # 1. Header Section
        self.setup_header()
        self.layout.addSpacing(32) # Header -> Summary
        
        # 2. Summary Metrics
        self.setup_summary_row()
        self.layout.addSpacing(48) # Summary -> Table
        
        # 3. Habit Matrix Table
        self.setup_matrix_area()
        self.layout.addSpacing(48) # Table -> Graph
        
        # 5. Graph Area
        self.setup_graph_area()

    def setup_header(self):
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 20, 0, 0) # More top padding
        
        # Left: Prev Month
        self.prev_btn = QPushButton("‹")
        self.prev_btn.setFixedSize(28, 28)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4A4A4A;
                border: 1px solid #2D2D2D;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover { color: #9A9A9A; border-color: #3D3D3D; }
        """)
        self.prev_btn.clicked.connect(self.prev_month)
        
        # Center: Month Year
        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignCenter)
        self.month_label.setFixedWidth(200) # Centering anchor
        self.month_label.setStyleSheet("""
            color: #EAEAEA;
            font-size: 20px;
            font-weight: 600;
            margin: 0 10px;
        """)
        
        # Right: Next Month
        self.next_btn = QPushButton("›")
        self.next_btn.setFixedSize(28, 28)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4A4A4A;
                border: 1px solid #2D2D2D;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover { color: #9A9A9A; border-color: #3D3D3D; }
        """)
        self.next_btn.clicked.connect(self.next_month)
        
        header_layout.addStretch()
        header_layout.addWidget(self.prev_btn)
        header_layout.addWidget(self.month_label)
        header_layout.addWidget(self.next_btn)
        header_layout.addStretch()
        
        # Add Habit Button
        self.add_btn = QPushButton("+  Add Habit")
        self.add_btn.setFixedSize(110, 32)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setStyleSheet("""
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
        self.add_btn.clicked.connect(self.open_add_dialog)
        
        header_container = QWidget()
        header_container_layout = QHBoxLayout(header_container)
        header_container_layout.setContentsMargins(0, 0, 0, 0)
        header_container_layout.addLayout(header_layout)
        header_container_layout.addWidget(self.add_btn)
        
        self.layout.addWidget(header_container)

    def setup_summary_row(self):
        self.summary_container = QWidget()
        layout = QHBoxLayout(self.summary_container)
        layout.setContentsMargins(0, 8, 0, 16)
        layout.setSpacing(16)
        
        # Card 1: Habits
        card_habits = QFrame()
        card_habits.setStyleSheet("QFrame { background-color: #1A1A1A; border-radius: 12px; }")
        v1 = QVBoxLayout(card_habits)
        v1.setContentsMargins(24, 16, 24, 16)
        self.habit_count_val = QLabel("0")
        self.habit_count_val.setStyleSheet("font-size: 18px; font-weight: 600; color: #EAEAEA;")
        habit_count_lbl = QLabel("Habits")
        habit_count_lbl.setStyleSheet("font-size: 11px; color: #6A6A6A; font-weight: 600;")
        v1.addWidget(self.habit_count_val)
        v1.addWidget(habit_count_lbl)
        layout.addWidget(card_habits)

        # Card 2: Completed
        card_done = QFrame()
        card_done.setStyleSheet("QFrame { background-color: #1A1A1A; border-radius: 12px; }")
        v2 = QVBoxLayout(card_done)
        v2.setContentsMargins(24, 16, 24, 16)
        self.completed_val = QLabel("0")
        self.completed_val.setStyleSheet("font-size: 18px; font-weight: 600; color: #EAEAEA;")
        completed_lbl = QLabel("Completed")
        completed_lbl.setStyleSheet("font-size: 11px; color: #6A6A6A; font-weight: 600;")
        v2.addWidget(self.completed_val)
        v2.addWidget(completed_lbl)
        layout.addWidget(card_done)

        # Card 3: Progress
        card_progress = QFrame()
        card_progress.setStyleSheet("QFrame { background-color: #1A1A1A; border-radius: 12px; }")
        v3 = QVBoxLayout(card_progress)
        v3.setContentsMargins(24, 16, 24, 16)
        v3.setSpacing(10)
        
        progress_lbl_row = QHBoxLayout()
        progress_name = QLabel("Monthly Progress")
        progress_name.setStyleSheet("font-size: 11px; color: #6A6A6A;")
        self.progress_pct = QLabel("0%")
        self.progress_pct.setStyleSheet("font-size: 11px; color: #EAEAEA; font-weight: 600;")
        progress_lbl_row.addWidget(progress_name)
        progress_lbl_row.addStretch()
        progress_lbl_row.addWidget(self.progress_pct)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #242424;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #4A7C59;
                border-radius: 3px;
            }
        """)
        
        v3.addLayout(progress_lbl_row)
        v3.addWidget(self.progress_bar)
        layout.addWidget(card_progress, 1) # Give more space to progress card
        
        self.layout.addWidget(self.summary_container)

    def setup_matrix_area(self):
        # We need a scroll area for the table part
        self.matrix_container = QWidget()
        self.matrix_layout = QHBoxLayout(self.matrix_container)
        self.matrix_layout.setContentsMargins(0, 16, 0, 16) # Add vertical breathing room
        self.matrix_layout.setSpacing(0)
        
        # Sticky Column (Habit Names)
        self.sticky_column = QWidget()
        self.sticky_column.setFixedWidth(220) # Wider for more padding
        self.sticky_column.setStyleSheet("background-color: #121212;")
        self.sticky_layout = QVBoxLayout(self.sticky_column)
        self.sticky_layout.setContentsMargins(0, 0, 0, 0)
        self.sticky_layout.setSpacing(0)
        
        # Matrix Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.matrix_content = QWidget()
        self.matrix_grid = QGridLayout(self.matrix_content)
        self.matrix_grid.setContentsMargins(0, 0, 0, 0)
        self.matrix_grid.setSpacing(2) # Increased spacing
        
        self.scroll_area.setWidget(self.matrix_content)
        
        self.matrix_layout.addWidget(self.sticky_column)
        self.matrix_layout.addWidget(self.scroll_area)
        
        self.layout.addWidget(self.matrix_container, 1)

    def setup_bottom_summary(self):
        # Rows are added directly to matrix grid in build_matrix_footer
        pass

    def setup_graph_area(self):
        self.graph_container = QWidget()
        self.graph_container.setFixedHeight(220) # Increased height
        layout = QVBoxLayout(self.graph_container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel("Monthly Performance Trend")
        lbl.setStyleSheet("color: #4A4A4A; font-size: 11px; font-weight: 400; margin-bottom: 10px;")
        layout.addWidget(lbl)
        
        self.graph_widget = PerformanceGraph()
        layout.addWidget(self.graph_widget)
        
        self.layout.addWidget(self.graph_container)

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.refresh_data()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.refresh_data()

    def open_add_dialog(self):
        dialog = AddHabitDialog(self)
        if dialog.exec():
            name = dialog.get_data()
            if name:
                self.db.add_habit(name)
                self.refresh_data()

    def refresh_data(self):
        # Update month label
        month_name = calendar.month_name[self.current_month]
        self.month_label.setText(f"{month_name} {self.current_year}")
        
        # Get data from database
        habits_data = self.db.get_all_habits_month_data(self.current_year, self.current_month)
        summary = self.db.get_month_summary(self.current_year, self.current_month)
        
        # Update summary metrics
        self.habit_count_val.setText(str(summary['total_habits']))
        self.completed_val.setText(str(summary['total_done']))
        self.progress_bar.setValue(int(summary['completion_rate']))
        self.progress_pct.setText(f"{int(summary['completion_rate'])}%")
        
        # Clear Matrix
        self.clear_layout(self.sticky_layout)
        self.clear_grid(self.matrix_grid)
        
        # Rebuild Matrix
        self.build_matrix(habits_data, summary)
        
        # Update Graph
        self.graph_widget.set_data(summary['daily_data'], summary['days_in_month'], self.current_year, self.current_month)

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def clear_grid(self, grid):
        while grid.count():
            item = grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def build_matrix(self, habits_data, summary):
        num_days = summary['days_in_month']
        
        # 1. Header Rows (Weeks and Days)
        self.build_matrix_header(num_days, summary)
        
        # 2. Habit Rows
        for row_idx, habit in enumerate(habits_data):
            # Habit Name (Sticky Column)
            self.add_habit_name_row(habit['name'], habit['id'])
            
            # Habit Cells
            for day in range(1, num_days + 1):
                date_str = f"{self.current_year:04d}-{self.current_month:02d}-{day:02d}"
                status = habit['logs'].get(date_str, 0) # 0: Missed, 1: Partial, 2: Done
                
                # Check date relative to today
                cell_date = date(self.current_year, self.current_month, day)
                is_past = cell_date < TODAY_DATE
                is_future = cell_date > TODAY_DATE
                is_today = cell_date == TODAY_DATE
                
                cell = HabitCell(habit['id'], date_str, status, is_today=is_today, is_past=is_past, is_future=is_future)
                cell.status_changed.connect(self.on_cell_changed)
                cell.setFixedHeight(38) # Consistent cell height
                self.matrix_grid.addWidget(cell, row_idx + 2, day - 1)
        
        # 3. Add Summary Rows to Grid
        self.build_matrix_footer(num_days, summary['daily_data'])

    def build_matrix_header(self, num_days, summary):
        # Column width for each day cell
        cell_width = 38 # Slightly wider
        
        # Week Row
        week_num = 1
        current_week_start = 1
        
        # Day Names and Dates Row
        for day in range(1, num_days + 1):
            date_obj = datetime(self.current_year, self.current_month, day)
            day_name = date_obj.strftime('%a')[:2] # Sa, Su, Mo...
            
            header_cell = QFrame()
            header_cell.setFixedSize(cell_width, 45)
            header_cell.setStyleSheet("background-color: transparent; border: none;")
            v = QVBoxLayout(header_cell)
            v.setContentsMargins(0, 5, 0, 5)
            v.setSpacing(2)
            
            lbl_day = QLabel(day_name)
            lbl_day.setAlignment(Qt.AlignCenter)
            lbl_day.setStyleSheet("color: #4A4A4A; font-size: 9px; font-weight: 400;") # Muted
            
            lbl_date = QLabel(str(day))
            lbl_date.setAlignment(Qt.AlignCenter)
            lbl_date.setStyleSheet("color: #8A8A8A; font-size: 11px; font-weight: 500;") # Secondary
            
            v.addWidget(lbl_day)
            v.addWidget(lbl_date)
            
            self.matrix_grid.addWidget(header_cell, 1, day - 1)
            
            # Week grouping logic (simplified: check if it's Sunday or end of month)
            if date_obj.weekday() == 6 or day == num_days:
                span = day - current_week_start + 1
                week_lbl = QLabel(f"Week {week_num}")
                week_lbl.setAlignment(Qt.AlignCenter)
                week_lbl.setFixedHeight(30) # Fixed height for alignment
                week_lbl.setStyleSheet("""
                    color: #555555; 
                    font-size: 10px; 
                    padding: 8px 4px 4px 4px;
                    background: transparent;
                """)
                self.matrix_grid.addWidget(week_lbl, 0, current_week_start - 1, 1, span)
                
                week_num += 1
                current_week_start = day + 1

        # Spacer in sticky layout for headers
        header_spacer = QFrame()
        header_spacer.setFixedHeight(30 + 45) # Week Row (30) + Day Row (45)
        header_spacer.setStyleSheet("background: transparent;")
        self.sticky_layout.addWidget(header_spacer)

    def build_matrix_footer(self, num_days, daily_data):
        # Row for "Habits Done"
        row_idx = self.matrix_grid.rowCount() 
        
        # Add more vertical spacing above summary rows
        spacer_row = QFrame()
        spacer_row.setFixedHeight(12)
        spacer_row.setStyleSheet("background: transparent; border: none;")
        self.sticky_layout.addWidget(spacer_row)
        self.matrix_grid.addWidget(spacer_row, row_idx, 0, 1, num_days)
        row_idx += 1

        # Sticky label for Done Count
        done_lbl_row = QFrame()
        done_lbl_row.setFixedHeight(30)
        done_lbl_layout = QHBoxLayout(done_lbl_row)
        done_lbl_layout.setContentsMargins(24, 0, 0, 0) # Align with habit names
        lbl_count = QLabel("Daily Done")
        lbl_count.setStyleSheet("color: #4A4A4A; font-size: 11px; font-weight: 400;")
        done_lbl_layout.addWidget(lbl_count)
        self.sticky_layout.addWidget(done_lbl_row)
        
        # Sticky label for Progress %
        pct_lbl_row = QFrame()
        pct_lbl_row.setFixedHeight(30)
        pct_lbl_layout = QHBoxLayout(pct_lbl_row)
        pct_lbl_layout.setContentsMargins(24, 0, 0, 0)
        lbl_pct = QLabel("Daily Progress")
        lbl_pct.setStyleSheet("color: #4A4A4A; font-size: 11px; font-weight: 400;")
        pct_lbl_layout.addWidget(lbl_pct)
        self.sticky_layout.addWidget(pct_lbl_row)

        for day in range(1, num_days + 1):
            date_str = f"{self.current_year:04d}-{self.current_month:02d}-{day:02d}"
            day_stats = daily_data.get(date_str, {'done': 0, 'percentage': 0})
            
            # Done count cell
            count_cell = QLabel(str(day_stats['done']))
            count_cell.setAlignment(Qt.AlignCenter)
            count_cell.setFixedHeight(30)
            count_cell.setStyleSheet("color: #555555; font-size: 10px; padding: 5px;") # Reduced opacity via color
            self.matrix_grid.addWidget(count_cell, row_idx, day - 1)
            
            # Percentage cell
            pct_cell = QLabel(f"{int(day_stats['percentage'])}%")
            pct_cell.setAlignment(Qt.AlignCenter)
            pct_cell.setFixedHeight(30)
            pct_cell.setStyleSheet("color: #555555; font-size: 10px; padding: 5px;")
            self.matrix_grid.addWidget(pct_cell, row_idx + 1, day - 1)

    def add_habit_name_row(self, name, habit_id):
        row = QFrame()
        row.setFixedHeight(38) # Match cell height
        row.setStyleSheet("""
            QFrame {
                background-color: transparent;
            }
        """)
        h = QHBoxLayout(row)
        h.setContentsMargins(24, 0, 10, 0) # More left padding
        
        lbl = QLabel(name)
        lbl.setStyleSheet("color: #EAEAEA; font-size: 13px; font-weight: 600;")
        h.addWidget(lbl)
        
        h.addStretch()
        
        # Delete Button
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(24, 24)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4A4A4A;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover { color: #AA4A4A; }
        """)
        del_btn.clicked.connect(lambda: self.confirm_delete_habit(habit_id, name))
        h.addWidget(del_btn)
        
        self.sticky_layout.addWidget(row)

    def confirm_delete_habit(self, habit_id, habit_name):
        msg = QMessageBox(self)
        msg.setWindowTitle("Delete Habit")
        msg.setText(f"Are you sure you want to delete '{habit_name}'?")
        msg.setInformativeText("This will permanently remove the habit and all its logs.")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        
        # Style the messagebox
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1A1A1A;
            }
            QLabel {
                color: #EAEAEA;
            }
            QPushButton {
                background-color: #242424;
                color: #EAEAEA;
                border-radius: 6px;
                padding: 6px 15px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #2D2D2D;
            }
        """)
        
        if msg.exec() == QMessageBox.Yes:
            self.db.delete_habit(habit_id)
            self.refresh_data()
            self.points_updated.emit()

    def on_cell_changed(self, habit_id, date_str, new_status):
        self.db.log_habit(habit_id, date_str, new_status)
        self.points_updated.emit()
        self.refresh_data()

class HabitCell(QFrame):
    status_changed = Signal(int, str, int)
    
    def __init__(self, habit_id, date_str, status, is_today=False, is_past=False, is_future=False):
        super().__init__()
        self.habit_id = habit_id
        self.date_str = date_str
        self.status = status
        self.is_today = is_today
        self.is_past = is_past
        self.is_future = is_future
        
        self.setFixedSize(36, 36)  # Uniform cell size
        self.update_style()
        
        if self.is_today:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ForbiddenCursor)

    def update_style(self):
        if self.is_future:
            # Future dates - very muted and locked appearance
            bg = "#121212"
            border = "#1A1A1A"
        elif self.is_past:
            # Past dates - muted and disabled appearance
            if self.status == 2:  # Done in past
                bg = "#2A4230"  # Muted green (faded)
                border = "#3A5040"
            elif self.status == 1:  # Partial in past
                bg = "#6A5A1C"  # Muted amber (faded)
                border = "#7A6A24"
            else:  # Missed in past
                bg = "#161616"  # Very muted
                border = "#1E1E1E"
        elif self.status == 2:  # Done (today)
            bg = "#3A5C44"  # Soft green
            border = "#4A6C54"
        elif self.status == 1:  # Partial (today)
            bg = "#9A7B1C"  # Warm amber
            border = "#AA8B2C"
        else:  # Not done (today)
            bg = "#1E1E1E"  # Neutral dark
            border = "#282828"
            
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 6px;
                margin: 1px;
            }}
        """)
        
        # Add Checkmark if Done
        if self.layout():
            # Clear existing
            for i in reversed(range(self.layout().count())): 
                self.layout().itemAt(i).widget().deleteLater()
        else:
            self.setLayout(QVBoxLayout())
            self.layout().setContentsMargins(0, 0, 0, 0)
            self.layout().setAlignment(Qt.AlignCenter)
            
        if self.status == 2:
            check_lbl = QLabel("✓")
            check_lbl.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
            self.layout().addWidget(check_lbl)
        elif self.status == 1:
            check_lbl = QLabel("◐")
            check_lbl.setStyleSheet("color: #E2A04A; font-size: 14px;")
            self.layout().addWidget(check_lbl)

    def mousePressEvent(self, event):
        # Only allow interaction for today
        if not self.is_today:
            return
            
        if event.button() == Qt.LeftButton:
            # Cycle: 0 -> 2 -> 1 -> 0
            if self.status == 0:
                self.status = 2
            elif self.status == 2:
                self.status = 1
            else:
                self.status = 0
                
            self.update_style()
            self.status_changed.emit(self.habit_id, self.date_str, self.status)

class PerformanceGraph(QWidget):
    def __init__(self):
        super().__init__()
        self.data = {}
        self.days = 30
        self.year = 2024
        self.month = 1
        self.setMinimumHeight(120)
        
    def set_data(self, data, days, year, month):
        self.data = data
        self.days = days
        self.year = year
        self.month = month
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Draw background frame - lower contrast
        painter.setPen(QPen(QColor("#1A1A1A"), 1))
        painter.setBrush(QBrush(QColor("#161616")))
        painter.drawRoundedRect(0, 0, w, h, 14, 14)
        
        if not self.data:
            return
            
        # Graph coordinates - increase padding
        margin_x = 60
        margin_y = 50
        graph_w = w - (margin_x * 2)
        graph_h = h - (margin_y * 1.5)
        
        points = []
        for day in range(1, self.days + 1):
            date_str = f"{self.year:04d}-{self.month:02d}-{day:02d}"
            val = self.data.get(date_str, {}).get('percentage', 0)
            
            x = margin_x + (day - 1) * (graph_w / (self.days - 1))
            y = h - margin_y - (val / 100 * graph_h)
            points.append(QPointF(x, y))
            
        if not points:
            return

        # Prepare path for smooth curve
        path = QPainterPath()
        path.moveTo(points[0])
        
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i+1]
            c1 = QPointF(p1.x() + (p2.x() - p1.x()) / 2, p1.y())
            c2 = QPointF(p1.x() + (p2.x() - p1.x()) / 2, p2.y())
            path.cubicTo(c1, c2, p2)

        # Draw area fill
        fill_path = QPainterPath(path)
        fill_path.lineTo(points[-1].x(), h - margin_y)
        fill_path.lineTo(points[0].x(), h - margin_y)
        fill_path.closeSubpath()
        
        accent_color = QColor("#4A7C59")
        fill_color = QColor(accent_color)
        fill_color.setAlpha(20) # Even more subtle
        painter.setBrush(QBrush(fill_color))
        painter.setPen(Qt.NoPen)
        painter.drawPath(fill_path)
        
        # Draw line
        painter.setPen(QPen(accent_color, 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(path)
            
        # Draw dots - reduced visibility
        painter.setBrush(QBrush(accent_color))
        painter.setPen(Qt.NoPen)
        for i, p in enumerate(points):
            if i % 3 == 0 or i == len(points)-1: # Only every 3rd point or last
                alpha = 80
                c = QColor(accent_color)
                c.setAlpha(alpha)
                painter.setBrush(QBrush(c))
                painter.drawEllipse(p, 2, 2)
            
        # Draw X-axis labels (whisper thin)
        painter.setPen(QPen(QColor("#444444")))
        painter.setFont(QFont("Inter", 8))
        for i in [1, 10, 20, self.days]:
            x = margin_x + (i - 1) * (graph_w / (self.days - 1))
            painter.drawText(int(x - 15), h - 25, 30, 20, Qt.AlignCenter, str(i))
