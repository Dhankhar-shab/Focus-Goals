from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                               QComboBox, QGridLayout, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from database import DatabaseManager

class Dashboard(QWidget):
    energy_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.setStyleSheet("background-color: #121212;")
        
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(28)
        self.layout.setContentsMargins(48, 48, 48, 48)

        # Header
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 20)
        
        title = QLabel("Dashboard")
        title.setStyleSheet("""
            font-size: 24px; 
            font-weight: 600; 
            color: #EAEAEA;
            letter-spacing: -0.2px;
        """)
        header.addWidget(title)
        header.addStretch()
        
        # Energy Selector
        energy_container = QFrame()
        energy_container.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border-radius: 10px;
            }
        """)
        energy_layout = QHBoxLayout(energy_container)
        energy_layout.setContentsMargins(16, 10, 16, 10)
        energy_layout.setSpacing(10)
        
        energy_icon = QLabel("")
        energy_icon.setStyleSheet("font-size: 14px;")
        energy_layout.addWidget(energy_icon)
        
        energy_label = QLabel("Energy")
        energy_label.setStyleSheet("color: #6A6A6A; font-size: 12px;")
        energy_layout.addWidget(energy_label)
        
        self.energy_combo = QComboBox()
        self.energy_combo.addItems(["High", "Medium", "Low"])
        self.energy_combo.setStyleSheet("""
            QComboBox { 
                border: none;
                background: transparent;
                font-size: 12px;
                font-weight: 600;
                color: #9A9A9A;
                padding-right: 16px;
            }
            QComboBox:hover { color: #EAEAEA; }
            QComboBox::drop-down { border: none; width: 12px; }
        """)
        self.energy_combo.currentTextChanged.connect(self.on_energy_changed)
        energy_layout.addWidget(self.energy_combo)
        
        header.addWidget(energy_container)
        self.layout.addLayout(header)

        # Stat Cards
        cards_layout = QGridLayout()
        cards_layout.setSpacing(16)
        
        self.points_card = self.create_stat_card("", "Points", "0", "#4A88B5")
        self.habits_card = self.create_stat_card("", "Habits Today", "0/0", "#4A7C59")
        self.tasks_card = self.create_stat_card("", "Pending", "0", "#A67C52")
        self.top3_card = self.create_stat_card("", "Top 3", "0", "#6A6A6A")
        
        cards_layout.addWidget(self.points_card, 0, 0)
        cards_layout.addWidget(self.habits_card, 0, 1)
        cards_layout.addWidget(self.tasks_card, 0, 2)
        cards_layout.addWidget(self.top3_card, 0, 3)
        
        self.layout.addLayout(cards_layout)

        # Weekly Overview
        graph_header = QLabel("Weekly Overview")
        graph_header.setStyleSheet("font-size: 18px; font-weight: 500; color: #EAEAEA; margin-top: 24px; margin-bottom: 12px;")
        self.layout.addWidget(graph_header)
        
        self.graph_frame = QFrame()
        self.graph_frame.setStyleSheet("""
            QFrame { 
                background-color: #1A1A1A; 
                border-radius: 14px;
            }
        """)
        # self.add_shadow(self.graph_frame) # Reduce shadow dominance
        
        self.graph_layout = QVBoxLayout(self.graph_frame)
        self.graph_layout.setContentsMargins(24, 24, 24, 24)
        
        self.figure = Figure(figsize=(8, 3), dpi=100, facecolor='#161616')
        self.canvas = FigureCanvas(self.figure)
        self.graph_layout.addWidget(self.canvas)
        
        self.layout.addWidget(self.graph_frame)
        self.layout.addStretch()

        self.refresh_stats()
        self.load_energy_level()

    def add_shadow(self, widget, blur=24, opacity=0.3):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setColor(QColor(0, 0, 0, int(255 * opacity)))
        shadow.setOffset(0, 8)
        widget.setGraphicsEffect(shadow)

    def create_stat_card(self, icon: str, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{ 
                background-color: #1A1A1A; 
                border-radius: 14px;
            }}
        """)
        # self.add_shadow(card, blur=20, opacity=0.15)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 18px; color: {color}; background: transparent; border: none;")
        layout.addWidget(icon_label)
        
        # Value
        v_label = QLabel(value)
        v_label.setObjectName("value_label")
        v_label.setStyleSheet("font-size: 28px; font-weight: 600; color: #EAEAEA; background: transparent; border: none;")
        layout.addWidget(v_label)
        
        # Title
        t_label = QLabel(title)
        t_label.setStyleSheet("color: #6A6A6A; font-size: 11px; font-weight: 600; background: transparent; border: none;")
        layout.addWidget(t_label)
        
        return card

    def update_card_value(self, card: QFrame, value: str):
        label = card.findChild(QLabel, "value_label")
        if label:
            label.setText(value)

    def on_energy_changed(self, text: str):
        self.db.set_todays_energy(text)
        self.energy_changed.emit(text)

    def load_energy_level(self):
        level = self.db.get_todays_energy()
        index = {"High": 0, "Medium": 1, "Low": 2}.get(level, 1)
        self.energy_combo.setCurrentIndex(index)

    def refresh_stats(self):
        stats = self.db.get_todays_stats()
        
        self.update_card_value(self.points_card, str(stats['points_balance']))
        self.update_card_value(self.habits_card, f"{stats['habits_done']}/{stats['total_habits']}")
        self.update_card_value(self.tasks_card, str(stats['pending_tasks']))
        self.update_card_value(self.top3_card, str(stats['top3_pending']))
        
        self.draw_graph()

    def draw_graph(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor='#161616')
        
        habits = self.db.get_habits()
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        if not habits:
            ax.text(0.5, 0.5, "No habits yet", ha='center', va='center', 
                   fontsize=14, color='#6A6A6A')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            self.canvas.draw()
            return
        
        total_points = [0] * 7
        for habit in habits:
            week_points = self.db.get_week_habit_points(habit[0])
            for i, p in enumerate(week_points):
                total_points[i] += p
        
        # Muted bar colors
        colors = ['#4A7C59' if p > 0 else '#2D2D2D' for p in total_points]
        bars = ax.bar(days, total_points, color=colors, width=0.5, edgecolor='none')
        
        ax.set_ylabel("Points", fontsize=11, color='#6A6A6A')
        ax.set_ylim(0, max(total_points) + 2 if max(total_points) > 0 else 5)
        
        # Dark theme styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#2D2D2D')
        ax.spines['bottom'].set_color('#2D2D2D')
        ax.tick_params(colors='#6A6A6A', labelsize=10)
        ax.yaxis.grid(True, linestyle='-', alpha=0.15, color='#3D3D3D')
        ax.set_axisbelow(True)
        
        self.figure.tight_layout()
        self.canvas.draw()

    def showEvent(self, event):
        self.refresh_stats()
        super().showEvent(event)
