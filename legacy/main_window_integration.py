"""
Example integration of ClockWidget into your MainWindow
Add this to your main window class
"""

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from clock_widget import ClockWidget  # or CompactClockWidget
from focus_widget import FocusWidget
from database import DatabaseManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()
    
    def init_ui(self):
        # Create central widget
        central = QWidget()
        central.setStyleSheet("background-color: #121212;")
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Main content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Add your focus widget here
        self.focus_widget = FocusWidget(self.db)
        content_layout.addWidget(self.focus_widget)
        
        main_layout.addWidget(content, stretch=1)
        
        self.setWindowTitle("Study Focus")
        self.resize(1200, 800)
    
    def create_sidebar(self):
        """Create sidebar with clock at the bottom"""
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("background-color: #0A0A0A;")
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(16)
        
        # App title
        from PySide6.QtWidgets import QLabel
        title = QLabel("Study Focus")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #EAEAEA;")
        layout.addWidget(title)
        
        # Add your navigation items here
        # ...
        
        layout.addStretch()
        
        # Clock at bottom (above Daily Reflection)
        self.clock_container = ClockWidget()
        
        # Check if clock should be visible
        clock_visible = self.db.get_setting('clock_visible', 'true') == 'true'
        self.clock_container.setVisible(clock_visible)
        
        layout.addWidget(self.clock_container)
        
        # Daily Reflection button (if you have one)
        # ...
        
        return sidebar


# Alternative: Clock in Top Bar
class MainWindowWithTopClock(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()
    
    def init_ui(self):
        # Create central widget
        central = QWidget()
        central.setStyleSheet("background-color: #121212;")
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top bar with clock
        top_bar = self.create_top_bar()
        main_layout.addWidget(top_bar)
        
        # Main content
        content = QWidget()
        content_layout = QHBoxLayout(content)
        
        # Sidebar
        sidebar = self.create_sidebar_minimal()
        content_layout.addWidget(sidebar)
        
        # Focus widget
        self.focus_widget = FocusWidget(self.db)
        content_layout.addWidget(self.focus_widget, stretch=1)
        
        main_layout.addWidget(content)
        
        self.setWindowTitle("Study Focus")
        self.resize(1200, 800)
    
    def create_top_bar(self):
        """Create top bar with clock on the right"""
        from clock_widget import CompactClockWidget
        from PySide6.QtWidgets import QLabel
        
        bar = QWidget()
        bar.setFixedHeight(48)
        bar.setStyleSheet("background-color: #0A0A0A; border-bottom: 1px solid #1A1A1A;")
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # App title
        title = QLabel("Study Focus")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #EAEAEA;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Clock on the right
        self.clock_container = CompactClockWidget()
        clock_visible = self.db.get_setting('clock_visible', 'true') == 'true'
        self.clock_container.setVisible(clock_visible)
        layout.addWidget(self.clock_container)
        
        return bar
    
    def create_sidebar_minimal(self):
        """Sidebar without clock (clock is in top bar)"""
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("background-color: #0A0A0A;")
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 20)
        
        # Add navigation items
        # ...
        
        return sidebar
