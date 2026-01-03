from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QPushButton, QComboBox, QTimeEdit, QLineEdit, 
                                QFrame, QStackedWidget, QSizePolicy, QCheckBox)
from PySide6.QtCore import Qt, QTimer, Signal, QTime, QDate
from PySide6.QtGui import QFont
from datetime import datetime, time
from focus_manager import FocusManager, FocusMode, PomodoroPhase

class FocusWidget(QWidget):
    """
    Minimal, calm focus widget for Pomodoro and Time Block modes.
    """
    session_completed = Signal(str)  # Emits phase name on completion
    
    def __init__(self, db_manager):
        super().__init__()
        self.mgr = FocusManager(db_manager)
        self.init_ui()
        
        # Internal timer for focus logic (ticking every second)
        self.tick_timer = QTimer(self)
        self.tick_timer.timeout.connect(self.on_tick)
        self.tick_timer.setInterval(1000)
        
        # Timer for checking time block status
        self.block_check_timer = QTimer(self)
        self.block_check_timer.timeout.connect(self.check_timeblock_status)
        self.block_check_timer.setInterval(30000)  # Check every 30 seconds

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(30)
        
        # 1. Header & Mode Selector
        header_layout = QHBoxLayout()
        title = QLabel("Focus Mode")
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #EAEAEA;")
        
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Pomodoro", "Time Block"])
        self.mode_selector.setFixedWidth(140)
        self.mode_selector.setStyleSheet("""
            QComboBox {
                background-color: #1A1A1A;
                border: 1px solid #2D2D2D;
                border-radius: 8px;
                padding: 6px 12px;
                font-weight: 600;
            }
        """)
        self.mode_selector.currentIndexChanged.connect(self.on_mode_changed)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.mode_selector)
        self.main_layout.addLayout(header_layout)
        
        # 2. Content Stack (Pomodoro vs Time Block UI)
        self.stack = QStackedWidget()
        
        # --- Pomodoro Page ---
        self.pomo_page = QWidget()
        pomo_layout = QVBoxLayout(self.pomo_page)
        pomo_layout.setAlignment(Qt.AlignCenter)
        pomo_layout.setSpacing(24)
        
        self.timer_label = QLabel("25:00")
        self.timer_label.setStyleSheet("font-size: 72px; font-weight: 600; color: #EAEAEA;")
        self.timer_label.setAlignment(Qt.AlignCenter)
        
        self.status_label = QLabel("Ready to focus?")
        self.status_label.setStyleSheet("font-size: 14px; color: #6A6A6A; font-weight: 400;")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        self.pomo_btn = QPushButton("Start Focus")
        self.pomo_btn.setFixedSize(200, 48)
        self.pomo_btn.setCursor(Qt.PointingHandCursor)
        self.pomo_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A5C44;
                color: #EAEAEA;
                border-radius: 12px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #446C50; }
        """)
        self.pomo_btn.clicked.connect(self.toggle_pomodoro)
        
        pomo_layout.addStretch()
        pomo_layout.addWidget(self.timer_label)
        pomo_layout.addWidget(self.status_label)
        pomo_layout.addSpacing(10)
        pomo_layout.addWidget(self.pomo_btn, 0, Qt.AlignCenter)
        pomo_layout.addStretch()
        
        # --- Time Block Page ---
        self.block_page = QWidget()
        block_layout = QVBoxLayout(self.block_page)
        block_layout.setContentsMargins(0, 20, 0, 0)
        block_layout.setSpacing(20)
        
        instruction = QLabel("Reserve a window for deep work")
        instruction.setStyleSheet("color: #6A6A6A; font-size: 13px;")
        block_layout.addWidget(instruction)
        
        # Current block status display
        self.block_status_frame = QFrame()
        self.block_status_frame.setStyleSheet("""
            background-color: #1A1A1A; 
            border-radius: 12px;
            border: 1px solid #2D2D2D;
        """)
        self.block_status_frame.setVisible(False)
        block_status_layout = QVBoxLayout(self.block_status_frame)
        block_status_layout.setContentsMargins(20, 16, 20, 16)
        
        self.block_status_label = QLabel("No active time block")
        self.block_status_label.setStyleSheet("color: #EAEAEA; font-weight: 500;")
        self.block_time_label = QLabel("")
        self.block_time_label.setStyleSheet("color: #6A6A6A; font-size: 12px;")
        self.block_task_label = QLabel("")
        self.block_task_label.setStyleSheet("color: #9A9A9A; font-size: 11px; margin-top: 4px;")
        
        block_status_layout.addWidget(self.block_status_label)
        block_status_layout.addWidget(self.block_time_label)
        block_status_layout.addWidget(self.block_task_label)
        
        self.clear_block_btn = QPushButton("Clear Block")
        self.clear_block_btn.setFixedHeight(28)
        self.clear_block_btn.setCursor(Qt.PointingHandCursor)
        self.clear_block_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #AA4A4A;
                border: none;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover { color: #CC5555; }
        """)
        self.clear_block_btn.clicked.connect(self.clear_timeblock)
        block_status_layout.addWidget(self.clear_block_btn, 0, Qt.AlignRight)
        
        block_layout.addWidget(self.block_status_frame)
        
        # New block form
        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: #1A1A1A; border-radius: 16px;")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(24, 24, 24, 24)
        form_layout.setSpacing(16)
        
        # Start Time
        start_row = QHBoxLayout()
        start_label = QLabel("Start Time:")
        start_label.setStyleSheet("color: #EAEAEA;")
        start_row.addWidget(start_label)
        self.start_edit = QTimeEdit()
        self.start_edit.setTime(QTime.currentTime().addSecs(300)) # Default 5 mins ahead
        self.start_edit.setStyleSheet("""
            QTimeEdit {
                background: #242424; 
                border: 1px solid #333333; 
                padding: 6px; 
                border-radius: 6px;
                color: #EAEAEA;
            }
        """)
        start_row.addStretch()
        start_row.addWidget(self.start_edit)
        form_layout.addLayout(start_row)
        
        # End Time
        end_row = QHBoxLayout()
        end_label = QLabel("End Time:")
        end_label.setStyleSheet("color: #EAEAEA;")
        end_row.addWidget(end_label)
        self.end_edit = QTimeEdit()
        self.end_edit.setTime(QTime.currentTime().addSecs(3600 + 300)) # Default 1 hour block
        self.end_edit.setStyleSheet("""
            QTimeEdit {
                background: #242424; 
                border: 1px solid #333333; 
                padding: 6px; 
                border-radius: 6px;
                color: #EAEAEA;
            }
        """)
        end_row.addStretch()
        end_row.addWidget(self.end_edit)
        form_layout.addLayout(end_row)
        
        # Task Name
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("What will you work on? (Optional)")
        self.task_input.setStyleSheet("""
            QLineEdit {
                background-color: #242424;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 10px;
                color: #EAEAEA;
            }
        """)
        form_layout.addWidget(self.task_input)
        
        block_layout.addWidget(form_frame)
        
        self.block_btn = QPushButton("Schedule Block")
        self.block_btn.setFixedSize(160, 40)
        self.block_btn.setCursor(Qt.PointingHandCursor)
        self.block_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A5C44;
                color: #EAEAEA;
                border-radius: 10px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #446C50; }
        """)
        self.block_btn.clicked.connect(self.schedule_block)
        block_layout.addWidget(self.block_btn, 0, Qt.AlignRight)
        
        block_layout.addStretch()
        
        # Add both pages to stack
        self.stack.addWidget(self.pomo_page)
        self.stack.addWidget(self.block_page)
        
        # Add stack to main layout
        self.main_layout.addWidget(self.stack)
        
        # 3. Settings (Bottom)
        settings_frame = QFrame()
        settings_frame.setStyleSheet("background-color: transparent; border-top: 1px solid #1A1A1A; padding-top: 10px;")
        settings_layout = QHBoxLayout(settings_frame)
        settings_layout.setContentsMargins(0, 10, 0, 0)
        
        self.show_clock_cb = QCheckBox("Show Clock")
        self.show_clock_cb.setChecked(self.mgr.db.get_setting('clock_visible', 'true') == 'true')
        self.show_clock_cb.setStyleSheet("color: #6A6A6A; font-size: 11px;")
        self.show_clock_cb.toggled.connect(self.toggle_clock_visibility)
        
        self.enable_sound_cb = QCheckBox("Sound Alerts")
        self.enable_sound_cb.setChecked(self.mgr.db.get_setting('sound_enabled', 'false') == 'true')
        self.enable_sound_cb.setStyleSheet("color: #6A6A6A; font-size: 11px;")
        self.enable_sound_cb.toggled.connect(self.toggle_sound)
        
        settings_layout.addWidget(self.show_clock_cb)
        settings_layout.addSpacing(20)
        settings_layout.addWidget(self.enable_sound_cb)
        settings_layout.addStretch()
        
        self.main_layout.addWidget(settings_frame)
        
        # Initialize UI state
        self.check_timeblock_status()

    def toggle_clock_visibility(self, checked):
        state = 'true' if checked else 'false'
        self.mgr.db.set_setting('clock_visible', state)
        # Notify MainWindow to update sidebar
        mw = self.window()
        if hasattr(mw, 'clock_container'):
            mw.clock_container.setVisible(checked)

    def toggle_sound(self, checked):
        state = 'true' if checked else 'false'
        self.mgr.db.set_setting('sound_enabled', state)

    def on_mode_changed(self, index):
        mode = FocusMode.POMODORO if index == 0 else FocusMode.TIMEBLOCK
        if self.mgr.set_mode(mode):
            self.stack.setCurrentIndex(index)
            # Start/stop block checker based on mode
            if mode == FocusMode.TIMEBLOCK:
                self.block_check_timer.start()
                self.check_timeblock_status()
            else:
                self.block_check_timer.stop()
        else:
            # Revert if switch failed (running)
            self.mode_selector.setCurrentIndex(0 if self.mgr.mode == FocusMode.POMODORO else 1)

    def toggle_pomodoro(self):
        if not self.mgr.is_running:
            if self.mgr.phase == PomodoroPhase.IDLE:
                self.mgr.start_pomodoro()
            else:
                self.mgr.start_break()
            
            self.tick_timer.start()
            self.update_pomo_ui()
        else:
            self.mgr.stop()
            self.tick_timer.stop()
            self.update_pomo_ui()

    def update_pomo_ui(self):
        state = self.mgr._get_state()
        self.timer_label.setText(self.mgr.get_display_time())
        
        if not state['is_running']:
            self.pomo_btn.setText("Start Focus")
            self.pomo_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3A5C44; 
                    color: #EAEAEA; 
                    border-radius: 12px; 
                    font-size: 15px;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #446C50; }
            """)
            self.status_label.setText("Ready to focus?")
            # Reset background to normal
            win = self.window()
            if hasattr(win, 'centralWidget'):
                win.centralWidget().setStyleSheet("background-color: #121212;")
        else:
            self.pomo_btn.setText("Stop")
            self.pomo_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2D2D2D; 
                    color: #AA4A4A; 
                    border-radius: 12px; 
                    font-size: 15px;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #333333; }
            """)
            
            p = state['phase']
            if p == 'focus':
                self.status_label.setText("Focusing... Deep work in progress.")
                self.window().centralWidget().setStyleSheet("background-color: #121212;")
            elif p == 'break':
                self.status_label.setText("Short Break. Refresh your mind.")
                # Lighter background for break as requested
                self.window().centralWidget().setStyleSheet("background-color: #181818;")
            elif p == 'long_break':
                self.status_label.setText("Long Break. You've earned it.")
                self.window().centralWidget().setStyleSheet("background-color: #1C1C1C;")

    def on_tick(self):
        result = self.mgr.tick()
        if result['completed']:
            self.tick_timer.stop()
            self.update_pomo_ui()
            self.session_completed.emit(result['phase'])
            # Play sound if enabled
            if self.enable_sound_cb.isChecked():
                self.play_completion_sound()
        else:
            self.timer_label.setText(self.mgr.get_display_time())

    def play_completion_sound(self):
        """Play a soft completion sound (implement if needed)"""
        # You can use QSound or other audio library here
        # For now, just a placeholder
        pass

    def schedule_block(self):
        st = self.start_edit.time()
        et = self.end_edit.time()
        
        # Convert QTime to datetime today
        now = datetime.now()
        start_dt = datetime.combine(now.date(), time(st.hour(), st.minute()))
        end_dt = datetime.combine(now.date(), time(et.hour(), et.minute()))
        
        res = self.mgr.schedule_timeblock(start_dt, end_dt, self.task_input.text())
        if res['success']:
            self.task_input.clear()
            self.check_timeblock_status()
            # Reset times for next block
            self.start_edit.setTime(QTime.currentTime().addSecs(300))
            self.end_edit.setTime(QTime.currentTime().addSecs(3900))
        else:
            # Show error in status
            self.block_status_frame.setVisible(True)
            self.block_status_label.setText(f"Error: {res['error']}")
            self.block_status_label.setStyleSheet("color: #AA4A4A; font-weight: 500;")
            self.block_time_label.setText("")
            self.block_task_label.setText("")

    def check_timeblock_status(self):
        """Update time block status display"""
        status = self.mgr.get_timeblock_status()
        
        if not status['active']:
            self.block_status_frame.setVisible(False)
            return
        
        self.block_status_frame.setVisible(True)
        
        if status['status'] == 'scheduled':
            self.block_status_label.setText("Scheduled Time Block")
            self.block_status_label.setStyleSheet("color: #9A9A9A; font-weight: 500;")
        elif status['status'] == 'in_progress':
            self.block_status_label.setText("Focus Block Active")
            self.block_status_label.setStyleSheet("color: #3A5C44; font-weight: 500;")
        else:
            self.block_status_label.setText("Block Completed")
            self.block_status_label.setStyleSheet("color: #6A6A6A; font-weight: 500;")
        
        # Format time display
        start = datetime.fromisoformat(status['start'])
        end = datetime.fromisoformat(status['end'])
        self.block_time_label.setText(
            f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"
        )
        
        # Show task name if exists
        if status['task_name']:
            self.block_task_label.setText(f"Task: {status['task_name']}")
            self.block_task_label.setVisible(True)
        else:
            self.block_task_label.setVisible(False)

    def clear_timeblock(self):
        """Clear the current time block"""
        self.mgr.clear_timeblock()
        self.block_status_frame.setVisible(False)
