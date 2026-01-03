
import os

def load_stylesheet():
    path = os.path.join(os.path.dirname(__file__), "styles.qss")
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return ""
