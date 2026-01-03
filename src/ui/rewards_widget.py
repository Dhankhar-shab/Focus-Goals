from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea, QFrame, QDialog,
                               QLineEdit, QSpinBox, QFormLayout, QMessageBox,
                               QDialogButtonBox, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from database import DatabaseManager
from points_manager import PointsManager

class AddRewardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Reward")
        self.resize(360, 200)
        self.setStyleSheet("background: #1E1E1E;")
        
        layout = QFormLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., 30 min break")
        layout.addRow(QLabel("Name:"), self.name_input)
        
        self.cost_input = QSpinBox()
        self.cost_input.setRange(0, 1000)
        self.cost_input.setValue(20)
        layout.addRow(QLabel("Cost:"), self.cost_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def get_data(self):
        return {'name': self.name_input.text(), 'cost': self.cost_input.value()}

class RewardsWidget(QWidget):
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
        title = QLabel("Rewards")
        title.setStyleSheet("""
            font-size: 24px; 
            font-weight: 600; 
            color: #EAEAEA;
            letter-spacing: -0.2px;
        """)
        header.addWidget(title)
        header.addStretch()
        
        # Balance
        self.balance_label = QLabel(" 0")
        self.balance_label.setStyleSheet("""
            background-color: #1A1A1A;
            color: #7A8BA2;
            padding: 8px 16px;
            border-radius: 10px;
            border: 1px solid #242424;
            font-size: 14px;
            font-weight: 600;
        """)
        header.addWidget(self.balance_label)
        
        add_btn = QPushButton("  New Reward")
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

        # Unlock status
        self.unlock_frame = QFrame()
        self.unlock_layout = QHBoxLayout(self.unlock_frame)
        self.unlock_layout.setContentsMargins(18, 14, 18, 14)
        self.unlock_label = QLabel()
        self.unlock_layout.addWidget(self.unlock_label)
        self.layout.addWidget(self.unlock_frame)

        # Scroll
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; }")
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignTop)
        self.container_layout.setSpacing(14)
        
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)

        self.refresh_rewards()

    def add_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 6)
        widget.setGraphicsEffect(shadow)

    def open_add_dialog(self):
        dialog = AddRewardDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data["name"]:
                self.db.add_reward(data["name"], data["cost"])
                self.refresh_rewards()

    def refresh_rewards(self):
        balance = self.db.get_points_balance()
        self.balance_label.setText(f" {balance}")
        
        can_unlock = self.points_mgr.can_unlock_rewards()
        if can_unlock:
            self.unlock_frame.setStyleSheet("""
                QFrame { 
                    background-color: #1A241A; 
                    border-radius: 10px;
                    border: 1px solid #243424;
                }
            """)
            self.unlock_label.setText("  All Top 3 done! Rewards unlocked.")
            self.unlock_label.setStyleSheet("color: #4A7C59; font-weight: 600; font-size: 12px;")
        else:
            self.unlock_frame.setStyleSheet("""
                QFrame { 
                    background-color: #241A1A; 
                    border-radius: 10px;
                    border: 1px solid #342424;
                }
            """)
            self.unlock_label.setText("  Complete Top 3 to unlock rewards")
            self.unlock_label.setStyleSheet("color: #8C4646; font-weight: 600; font-size: 12px;")
        
        for i in reversed(range(self.container_layout.count())): 
            widget = self.container_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        rewards = self.db.get_rewards()
        
        if not rewards:
            empty = QLabel("No rewards yet.\nAdd some to motivate yourself!")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #6A6A6A; font-size: 15px; padding: 60px;")
            self.container_layout.addWidget(empty)
            return
        
        for reward in rewards:
            self.add_reward_card(reward, balance, can_unlock)

    def add_reward_card(self, reward, balance: int, can_unlock: bool):
        r_id, name, cost = reward
        can_afford = balance >= cost
        is_claimable = can_unlock and can_afford
        
        card = QFrame()
        if is_claimable:
            card.setStyleSheet("""
                QFrame { 
                    background-color: #1A181C; 
                    border-radius: 12px;
                    border: 1px solid #3E3445;
                    border-right: 4px solid #5D5470;
                }
            """)
        else:
            card.setStyleSheet("""
                QFrame { 
                    background-color: #161616; 
                    border-radius: 12px;
                    border: 1px solid #242424;
                }
            """)
        self.add_shadow(card)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 16, 16, 16)
        
        # Icon
        icon = QLabel("")
        icon.setStyleSheet("font-size: 28px;")
        layout.addWidget(icon)
        
        # Info
        info = QVBoxLayout()
        info.setSpacing(2)
        
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #EAEAEA;")
        info.addWidget(name_lbl)
        
        cost_lbl = QLabel(f"{cost} points")
        cost_lbl.setStyleSheet("color: #6A6A6A; font-size: 12px; font-weight: 600;")
        info.addWidget(cost_lbl)
        
        layout.addLayout(info, 1)
        
        # Claim
        claim_btn = QPushButton("Claim")
        if is_claimable:
            claim_btn.setStyleSheet("""
                QPushButton {
                    background: #5D5470; color: #EAEAEA;
                    border: none; padding: 8px 20px; border-radius: 8px;
                    font-weight: 600; font-size: 12px;
                }
                QPushButton:hover { background: #6D6480; }
            """)
            claim_btn.setCursor(Qt.PointingHandCursor)
            claim_btn.clicked.connect(lambda: self.claim_reward(r_id, name))
        else:
            claim_btn.setEnabled(False)
            claim_btn.setStyleSheet("""
                QPushButton {
                    background: #242424; color: #4A4A4A;
                    border: none; padding: 8px 20px; border-radius: 8px;
                    font-size: 12px;
                }
            """)
        layout.addWidget(claim_btn)
        
        # Delete
        del_btn = QPushButton("")
        del_btn.setFixedSize(34, 34)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton {
                background: #2D1E1E; color: #E25C5C; border: none; 
                border-radius: 10px; font-size: 14px;
            }
            QPushButton:hover { background: #E25C5C; color: #1E1E1E; }
        """)
        del_btn.clicked.connect(lambda: self.delete_reward(r_id))
        layout.addWidget(del_btn)
        
        self.container_layout.addWidget(card)

    def claim_reward(self, reward_id: int, name: str):
        if self.db.claim_reward(reward_id):
            QMessageBox.information(self, "Claimed!", f"Enjoy: {name}")
            self.points_updated.emit()
            self.refresh_rewards()

    def delete_reward(self, reward_id: int):
        self.db.delete_reward(reward_id)
        self.refresh_rewards()

    def showEvent(self, event):
        self.refresh_rewards()
        super().showEvent(event)
