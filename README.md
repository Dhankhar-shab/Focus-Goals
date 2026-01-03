# ⏱ Study Focus

**Study Focus** is a minimal, calm, and distraction-free productivity application built for Linux. It combines habit tracking, task management, and focus sessions with a premium, dark-mode aesthetic.

![Study Focus Screenshot](https://via.placeholder.com/1280x820.png?text=Study+Focus+Premium+UI) *Note: Replace with actual screenshot before publishing.*

## ✨ Features

- **🎯 Focus System**: Toggle between Pomodoro sessions and scheduled Time Blocks.
- **✓ Habit Matrix**: Track your daily discipline with a monthly grid view and performance graphs.
- **📋 Task Board**: Manage your to-do list with "Top 3" highlighting and priority-based sorting.
- **📅 Calendar Integration**: A full-featured calendar with event management and chronological sidebar.
- **🏆 Rewards Shop**: Earn points for completing tasks and habits, then redeem them for custom rewards.
- **🌙 Premium Dark Theme**: A sleek, Mac-inspired "traffic light" interface with SF Pro typography.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- PySide6

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/study-focus.git
   cd study-focus
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python3 main.py
   ```

## 🛠 Project Structure

- `main.py`: Entry point for the application.
- `src/ui/`: Contains all PySide6 UI components and stylesheets.
- `src/database.py`: Manages SQLite persistence and data logic.
- `src/focus_manager.py`: Core logic for time-tracking and focus sessions.
- `data/`: Directory for local storage (auto-generated).

## 🎨 Theme & Customization

The application uses a custom CSS system defined in `src/ui/styles.qss`. You can modify colors, fonts, and spacing there to match your personal preference.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by premium productivity tools and minimalist design philosophies.
- Icons powered by native Unicode symbols for high-performance rendering.
