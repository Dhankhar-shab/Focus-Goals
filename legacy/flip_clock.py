import tkinter as tk
from datetime import datetime

class FlipClock:
    def __init__(self, root):
        self.root = root
        self.root.title("Flip Clock")
        self.root.configure(bg='black')
        
        # Main container
        self.main_frame = tk.Frame(root, bg='black')
        self.main_frame.pack(expand=True, fill='both', padx=50, pady=50)
        
        # Create time containers
        self.hour_frame = self.create_time_unit(self.main_frame, 0)
        self.minute_frame = self.create_time_unit(self.main_frame, 1)
        self.second_frame = self.create_time_unit(self.main_frame, 2)
        
        # Colon separators
        self.create_separator(self.main_frame, 0.5)
        self.create_separator(self.main_frame, 1.5)
        
        # Labels for storing current values
        self.hour_labels = []
        self.minute_labels = []
        self.second_labels = []
        
        # Initialize display
        self.update_clock()
        
    def create_time_unit(self, parent, position):
        """Create a frame for a time unit (hour, minute, or second)"""
        frame = tk.Frame(parent, bg='black')
        frame.grid(row=0, column=position*2, padx=10)
        
        # Create two digit containers side by side
        digit1_frame = self.create_digit_container(frame)
        digit1_frame.pack(side='left', padx=5)
        
        digit2_frame = self.create_digit_container(frame)
        digit2_frame.pack(side='left', padx=5)
        
        return frame
        
    def create_digit_container(self, parent):
        """Create a single digit flip card container"""
        container = tk.Frame(parent, bg='#2a2a2a', 
                           highlightbackground='#1a1a1a',
                           highlightthickness=2)
        container.pack(side='left')
        
        # Digit label
        label = tk.Label(container, text='0', 
                        font=('Arial', 120, 'bold'),
                        fg='white', bg='#2a2a2a',
                        width=2, height=1)
        label.pack(padx=20, pady=30)
        
        return container
        
    def create_separator(self, parent, position):
        """Create colon separator between time units"""
        separator = tk.Label(parent, text=':', 
                           font=('Arial', 80, 'bold'),
                           fg='#555', bg='black')
        separator.grid(row=0, column=int(position*2))
        
    def update_clock(self):
        """Update the clock display"""
        now = datetime.now()
        
        # Get time components
        hour = now.strftime('%I')  # 12-hour format
        minute = now.strftime('%M')
        second = now.strftime('%S')
        am_pm = now.strftime('%p')
        
        # Update hour digits
        hour_widgets = self.hour_frame.winfo_children()
        hour_widgets[0].winfo_children()[0].config(text=hour[0])
        hour_widgets[1].winfo_children()[0].config(text=hour[1])
        
        # Update minute digits
        minute_widgets = self.minute_frame.winfo_children()
        minute_widgets[0].winfo_children()[0].config(text=minute[0])
        minute_widgets[1].winfo_children()[0].config(text=minute[1])
        
        # Update second digits
        second_widgets = self.second_frame.winfo_children()
        second_widgets[0].winfo_children()[0].config(text=second[0])
        second_widgets[1].winfo_children()[0].config(text=second[1])
        
        # Update AM/PM indicator if not exists, create it
        if not hasattr(self, 'am_pm_label'):
            self.am_pm_label = tk.Label(self.main_frame, text=am_pm,
                                       font=('Arial', 24, 'bold'),
                                       fg='#666', bg='black')
            self.am_pm_label.grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        else:
            self.am_pm_label.config(text=am_pm)
        
        # Schedule next update
        self.root.after(1000, self.update_clock)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("900x400")
    clock = FlipClock(root)
    root.mainloop()