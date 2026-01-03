"""
Points Manager - Handles all point calculations and awards
"""
from database import DatabaseManager

class PointsManager:
    """Manages points calculation and awarding for habits and tasks."""
    
    # Point values
    HABIT_DONE_POINTS = 2
    HABIT_PARTIAL_POINTS = 1
    HABIT_MISSED_POINTS = 0
    
    MISSED_HIGH_PRIORITY_PENALTY = -2
    WEEKLY_CONSISTENCY_BONUS = 10
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def award_habit_points(self, habit_id: int, status: int) -> int:
        """Award points based on habit status (0=missed, 1=partial, 2=done)"""
        if status == 2:
            points = self.HABIT_DONE_POINTS
        elif status == 1:
            points = self.HABIT_PARTIAL_POINTS
        else:
            points = self.HABIT_MISSED_POINTS
        
        if points > 0:
            self.db.add_points(points)
        return points
    
    def award_task_points(self, task_id: int) -> int:
        """Award points for completing a task. Returns points awarded."""
        points = self.db.complete_task(task_id)
        if points > 0:
            self.db.add_points(points)
        return points
    
    def penalize_missed_high_priority(self, task_id: int) -> int:
        """Apply penalty for missing a high-priority task. Returns penalty applied."""
        # This should be called when a high-priority task deadline passes
        penalty = abs(self.MISSED_HIGH_PRIORITY_PENALTY)
        self.db.deduct_points(penalty)
        return penalty
    
    def check_weekly_bonus(self) -> int:
        """
        Check if user gets weekly consistency bonus.
        Criteria: Complete at least 80% of habits for 7 days.
        Returns bonus awarded (0 if not eligible).
        """
        # Simplified: check if all habits have at least 5 "Done" entries in last 7 days
        habits = self.db.get_habits()
        if not habits:
            return 0
        
        total_possible = len(habits) * 7
        total_done = 0
        
        for habit in habits:
            week_points = self.db.get_week_habit_points(habit[0])
            total_done += sum(1 for p in week_points if p == 2)
        
        if total_possible > 0 and (total_done / total_possible) >= 0.8:
            self.db.add_points(self.WEEKLY_CONSISTENCY_BONUS)
            return self.WEEKLY_CONSISTENCY_BONUS
        
        return 0
    
    def can_unlock_rewards(self) -> bool:
        """Check if user can unlock rewards (all high-priority tasks completed today)."""
        stats = self.db.get_todays_stats()
        # Simple check: no pending top3 tasks
        return stats['top3_pending'] == 0
    
    def get_balance(self) -> int:
        """Get current points balance."""
        return self.db.get_points_balance()
