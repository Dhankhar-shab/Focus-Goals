from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Habit:
    id: Optional[int]
    name: str
    created_at: str  # ISO format YYYY-MM-DD

@dataclass
class HabitLog:
    id: Optional[int]
    habit_id: int
    date: str  # YYYY-MM-DD
    status: int  # 0=Not Done, 1=Partial, 2=Done

@dataclass
class Task:
    id: Optional[int]
    name: str
    deadline: Optional[str] # YYYY-MM-DD HH:MM
    priority: int # 3=High (Red), 2=Medium (Yellow), 1=Low (Green)
    points: int
    is_completed: bool
    energy_level: str # "High", "Medium", "Low"
