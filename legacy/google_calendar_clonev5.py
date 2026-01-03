import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import calendar
import json
import os

class CalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calendar Scheduler")
        self.root.geometry("1200x700")
        self.root.configure(bg='white')
        
        # Load or initialize events
        self.events = self.load_events()
        
        # Current date tracking
        self.current_date = datetime.now()
        self.selected_date = None
        
        # Create UI
        self.create_header()
        self.create_sidebar()
        self.create_calendar_view()
        
    def load_events(self):
        """Load events from file"""
        if os.path.exists('events.json'):
            try:
                with open('events.json', 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_events(self):
        """Save events to file"""
        with open('events.json', 'w') as f:
            json.dump(self.events, f, indent=2)
    
    def create_header(self):
        """Create header with navigation and current month"""
        header = tk.Frame(self.root, bg='white', height=80)
        header.pack(fill='x', padx=20, pady=10)
        header.pack_propagate(False)
        
        # Navigation buttons
        nav_frame = tk.Frame(header, bg='white')
        nav_frame.pack(side='left')
        
        prev_btn = tk.Button(nav_frame, text='◀', font=('Arial', 16),
                            command=self.prev_month, bg='white',
                            relief='flat', cursor='hand2')
        prev_btn.pack(side='left', padx=5)
        
        next_btn = tk.Button(nav_frame, text='▶', font=('Arial', 16),
                            command=self.next_month, bg='white',
                            relief='flat', cursor='hand2')
        next_btn.pack(side='left', padx=5)
        
        today_btn = tk.Button(nav_frame, text='Today', font=('Arial', 11),
                             command=self.goto_today, bg='white',
                             relief='solid', bd=1, cursor='hand2',
                             padx=15, pady=5)
        today_btn.pack(side='left', padx=10)
        
        # Month and year display
        self.month_label = tk.Label(header, text='', font=('Arial', 24, 'bold'),
                                   bg='white', fg='#333')
        self.month_label.pack(side='left', padx=20)
        
        # Create event button
        create_btn = tk.Button(header, text='+ Create Event',
                              font=('Arial', 11, 'bold'),
                              bg='#1a73e8', fg='white',
                              command=self.open_event_dialog,
                              relief='flat', cursor='hand2',
                              padx=20, pady=8)
        create_btn.pack(side='right')
    
    def create_sidebar(self):
        """Create sidebar with mini calendar and event list"""
        sidebar = tk.Frame(self.root, bg='#f8f9fa', width=250)
        sidebar.pack(side='left', fill='y', padx=(20, 0))
        sidebar.pack_propagate(False)
        
        # Mini calendar
        mini_title = tk.Label(sidebar, text='Mini Calendar',
                            font=('Arial', 12, 'bold'),
                            bg='#f8f9fa', fg='#333')
        mini_title.pack(pady=(20, 10))
        
        # Mini calendar frame
        self.mini_cal_frame = tk.Frame(sidebar, bg='#f8f9fa')
        self.mini_cal_frame.pack(padx=10, pady=10)
        
        # Upcoming events
        events_title = tk.Label(sidebar, text='Upcoming Events',
                               font=('Arial', 12, 'bold'),
                               bg='#f8f9fa', fg='#333')
        events_title.pack(pady=(30, 10))
        
        # Events list with scrollbar
        events_frame = tk.Frame(sidebar, bg='#f8f9fa')
        events_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(events_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Use frame with canvas for better control
        self.events_canvas = tk.Canvas(events_frame, bg='white', 
                                       yscrollcommand=scrollbar.set,
                                       highlightthickness=0)
        self.events_canvas.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.events_canvas.yview)
        
        # Frame inside canvas for events
        self.events_inner_frame = tk.Frame(self.events_canvas, bg='white')
        self.events_canvas_window = self.events_canvas.create_window(
            (0, 0), window=self.events_inner_frame, anchor='nw')
        
        # Bind configure event
        self.events_inner_frame.bind('<Configure>', 
                                    lambda e: self.events_canvas.configure(
                                        scrollregion=self.events_canvas.bbox('all')))
        self.events_canvas.bind('<Configure>', self.on_canvas_configure)
    
    def create_calendar_view(self):
        """Create main calendar grid"""
        cal_frame = tk.Frame(self.root, bg='white')
        cal_frame.pack(side='left', fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Days of week header
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        for i, day in enumerate(days):
            label = tk.Label(cal_frame, text=day, font=('Arial', 10, 'bold'),
                           bg='#f8f9fa', fg='#666', pady=10)
            label.grid(row=0, column=i, sticky='ew', padx=1, pady=1)
            cal_frame.columnconfigure(i, weight=1)
        
        # Calendar grid
        self.day_frames = {}
        for row in range(1, 7):
            cal_frame.rowconfigure(row, weight=1)
            for col in range(7):
                frame = tk.Frame(cal_frame, bg='white', relief='solid', bd=1)
                frame.grid(row=row, column=col, sticky='nsew', padx=1, pady=1)
                
                # Day number label
                day_label = tk.Label(frame, text='', font=('Arial', 11),
                                   bg='white', fg='#333', anchor='ne')
                day_label.pack(side='top', anchor='ne', padx=5, pady=5)
                
                # Events container
                events_container = tk.Frame(frame, bg='white')
                events_container.pack(fill='both', expand=True, padx=3, pady=3)
                
                self.day_frames[(row-1, col)] = {
                    'frame': frame,
                    'label': day_label,
                    'events': events_container
                }
                
                # Bind click event
                frame.bind('<Button-1>', lambda e, r=row-1, c=col: self.select_date(r, c))
                day_label.bind('<Button-1>', lambda e, r=row-1, c=col: self.select_date(r, c))
        
        self.update_calendar()
    
    def update_calendar(self):
        """Update calendar display"""
        year = self.current_date.year
        month = self.current_date.month
        
        # Update month label
        self.month_label.config(text=self.current_date.strftime('%B %Y'))
        
        # Get calendar data
        cal = calendar.monthcalendar(year, month)
        today = datetime.now().date()
        
        # Clear and update calendar
        for (row, col), components in self.day_frames.items():
            if row < len(cal) and col < len(cal[row]) and cal[row][col] != 0:
                day = cal[row][col]
                date_str = f"{year}-{month:02d}-{day:02d}"
                
                # Update day number
                components['label'].config(text=str(day))
                
                # Highlight today
                current_date = datetime(year, month, day).date()
                if current_date == today:
                    components['frame'].config(bg='#e8f0fe')
                    components['label'].config(bg='#e8f0fe', fg='#1a73e8', font=('Arial', 11, 'bold'))
                else:
                    components['frame'].config(bg='white')
                    components['label'].config(bg='white', fg='#333', font=('Arial', 11))
                
                # Clear events
                for widget in components['events'].winfo_children():
                    widget.destroy()
                
                # Add events with edit functionality
                if date_str in self.events:
                    for idx, event in enumerate(self.events[date_str][:3]):  # Show max 3 events
                        event_label = tk.Label(components['events'],
                                             text=f"• {event['title'][:20]}",
                                             font=('Arial', 8),
                                             bg='#d2e3fc', fg='#1967d2',
                                             anchor='w', padx=3, pady=1,
                                             cursor='hand2')
                        event_label.pack(fill='x', pady=1)
                        # Bind click to edit event
                        event_label.bind('<Button-1>', 
                                       lambda e, d=date_str, i=idx: self.edit_event(d, i))
                    
                    if len(self.events[date_str]) > 3:
                        more_label = tk.Label(components['events'],
                                            text=f"+{len(self.events[date_str])-3} more",
                                            font=('Arial', 7),
                                            bg='white', fg='#666',
                                            anchor='w', padx=3)
                        more_label.pack(fill='x')
            else:
                components['label'].config(text='')
                components['frame'].config(bg='#fafafa')
                for widget in components['events'].winfo_children():
                    widget.destroy()
        
        self.update_mini_calendar()
        self.update_events_list()
    
    def update_mini_calendar(self):
        """Update mini calendar in sidebar with today highlighted"""
        # Clear previous mini calendar
        for widget in self.mini_cal_frame.winfo_children():
            widget.destroy()
        
        year = self.current_date.year
        month = self.current_date.month
        today = datetime.now().date()
        
        # Month/Year label
        month_year = tk.Label(self.mini_cal_frame, 
                             text=f"{calendar.month_name[month]} {year}",
                             font=('Arial', 10, 'bold'),
                             bg='#f8f9fa', fg='#333')
        month_year.grid(row=0, column=0, columnspan=7, pady=5)
        
        # Day headers
        days = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
        for i, day in enumerate(days):
            tk.Label(self.mini_cal_frame, text=day, font=('Arial', 8, 'bold'),
                    bg='#f8f9fa', fg='#666', width=3).grid(row=1, column=i)
        
        # Get calendar
        cal = calendar.monthcalendar(year, month)
        
        # Display dates
        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day == 0:
                    label = tk.Label(self.mini_cal_frame, text='', 
                                   bg='#f8f9fa', width=3, height=1)
                else:
                    current_date = datetime(year, month, day).date()
                    
                    # Highlight today
                    if current_date == today:
                        label = tk.Label(self.mini_cal_frame, text=str(day),
                                       font=('Arial', 8, 'bold'),
                                       bg='#1a73e8', fg='white',
                                       width=3, height=1,
                                       relief='solid', bd=1)
                    else:
                        label = tk.Label(self.mini_cal_frame, text=str(day),
                                       font=('Arial', 8),
                                       bg='#f8f9fa', fg='#333',
                                       width=3, height=1)
                    
                label.grid(row=week_num+2, column=day_num, padx=1, pady=1)
    
    def on_canvas_configure(self, event):
        """Adjust canvas window width when canvas is resized"""
        self.events_canvas.itemconfig(self.events_canvas_window, width=event.width)
    
    def update_events_list(self):
        """Update upcoming events list with expandable cards"""
        # Clear existing events
        for widget in self.events_inner_frame.winfo_children():
            widget.destroy()
        
        # Get all events with proper date parsing
        all_events = []
        today = datetime.now().date()
        
        for date_str, events in self.events.items():
            try:
                # Parse the date string to a datetime object
                event_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                # Only include today and future events
                if event_date.date() >= today:
                    for idx, event in enumerate(events):
                        # Store as tuple: (datetime object for sorting, date_str, idx, event)
                        all_events.append((event_date, date_str, idx, event))
            except ValueError:
                # Skip invalid dates
                continue
        
        # Sort by datetime object (earliest first)
        all_events.sort(key=lambda x: x[0])
        
        # Add event cards in sorted order
        for event_date, date_str, event_idx, event in all_events:
            self.create_event_card(date_str, event_idx, event)
        
        # Update scroll region
        self.events_inner_frame.update_idletasks()
        self.events_canvas.configure(scrollregion=self.events_canvas.bbox('all'))
    
    def create_event_card(self, date_str, event_idx, event):
        """Create an expandable event card"""
        # Card container
        card_frame = tk.Frame(self.events_inner_frame, bg='white', 
                             relief='solid', bd=1)
        card_frame.pack(fill='x', padx=5, pady=5)
        
        # Header frame (always visible)
        header_frame = tk.Frame(card_frame, bg='#f0f0f0', cursor='hand2')
        header_frame.pack(fill='x', padx=1, pady=1)
        
        # Date and title
        date_label = tk.Label(header_frame, 
                             text=f"📅 {date_str}",
                             font=('Arial', 8, 'bold'),
                             bg='#f0f0f0', fg='#666',
                             anchor='w')
        date_label.pack(side='top', fill='x', padx=8, pady=(5, 2))
        
        title_label = tk.Label(header_frame,
                              text=event['title'],
                              font=('Arial', 10, 'bold'),
                              bg='#f0f0f0', fg='#333',
                              anchor='w')
        title_label.pack(side='top', fill='x', padx=8, pady=(0, 5))
        
        time_label = tk.Label(header_frame,
                             text=f"🕐 {event.get('time', 'No time set')}",
                             font=('Arial', 8),
                             bg='#f0f0f0', fg='#666',
                             anchor='w')
        time_label.pack(side='top', fill='x', padx=8, pady=(0, 5))
        
        # Details frame (expandable)
        details_frame = tk.Frame(card_frame, bg='white')
        details_expanded = [False]  # Use list to make it mutable in nested function
        
        def toggle_details(event=None):
            if details_expanded[0]:
                details_frame.pack_forget()
                details_expanded[0] = False
            else:
                details_frame.pack(fill='x', padx=1, pady=(0, 1))
                details_expanded[0] = True
        
        # Bind click to toggle
        header_frame.bind('<Button-1>', toggle_details)
        date_label.bind('<Button-1>', toggle_details)
        title_label.bind('<Button-1>', toggle_details)
        time_label.bind('<Button-1>', toggle_details)
        
        # Description
        desc_label = tk.Label(details_frame,
                             text="Description:",
                             font=('Arial', 8, 'bold'),
                             bg='white', fg='#666',
                             anchor='w')
        desc_label.pack(side='top', fill='x', padx=8, pady=(8, 2))
        
        desc_text = tk.Label(details_frame,
                            text=event.get('description', 'No description'),
                            font=('Arial', 9),
                            bg='white', fg='#333',
                            anchor='w',
                            justify='left',
                            wraplength=200)
        desc_text.pack(side='top', fill='x', padx=8, pady=(0, 8))
        
        # Edit button
        edit_btn = tk.Button(details_frame,
                            text="✏️ Edit Event",
                            font=('Arial', 9),
                            bg='#1a73e8', fg='white',
                            relief='flat',
                            cursor='hand2',
                            command=lambda: self.edit_event(date_str, event_idx))
        edit_btn.pack(side='bottom', padx=8, pady=8, fill='x')
    
    def select_date(self, row, col):
        """Handle date selection"""
        year = self.current_date.year
        month = self.current_date.month
        cal = calendar.monthcalendar(year, month)
        
        if row < len(cal) and col < len(cal[row]) and cal[row][col] != 0:
            day = cal[row][col]
            selected_date = datetime(year, month, day)
            
            # Check if date is in the past (before today, not including today)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if selected_date < today:
                messagebox.showwarning("Warning", 
                                      "Cannot create events in the past.\nPlease select today or a future date.")
                return
            
            self.selected_date = selected_date
            self.open_event_dialog()
    
    def open_event_dialog(self, edit_mode=False, date_str=None, event_idx=None):
        """Open dialog to create or edit event"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Event" if edit_mode else "Create Event")
        dialog.geometry("400x400")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Get existing event data if editing
        existing_event = None
        if edit_mode and date_str and event_idx is not None:
            existing_event = self.events[date_str][event_idx]
        
        # Event title
        tk.Label(dialog, text="Event Title:", font=('Arial', 10),
                bg='white').pack(pady=(20, 5), anchor='w', padx=20)
        title_entry = tk.Entry(dialog, font=('Arial', 11), width=40)
        title_entry.pack(padx=20, pady=5)
        if existing_event:
            title_entry.insert(0, existing_event['title'])
        title_entry.focus()
        
        # Date
        tk.Label(dialog, text="Date:", font=('Arial', 10),
                bg='white').pack(pady=(10, 5), anchor='w', padx=20)
        date_frame = tk.Frame(dialog, bg='white')
        date_frame.pack(padx=20, pady=5)
        
        if edit_mode and date_str:
            default_date = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            default_date = self.selected_date if self.selected_date else datetime.now()
        
        year_var = tk.StringVar(value=str(default_date.year))
        month_var = tk.StringVar(value=str(default_date.month))
        day_var = tk.StringVar(value=str(default_date.day))
        
        tk.Entry(date_frame, textvariable=year_var, width=6).pack(side='left', padx=2)
        tk.Label(date_frame, text="-", bg='white').pack(side='left')
        tk.Entry(date_frame, textvariable=month_var, width=4).pack(side='left', padx=2)
        tk.Label(date_frame, text="-", bg='white').pack(side='left')
        tk.Entry(date_frame, textvariable=day_var, width=4).pack(side='left', padx=2)
        
        # Time
        tk.Label(dialog, text="Time:", font=('Arial', 10),
                bg='white').pack(pady=(10, 5), anchor='w', padx=20)
        time_entry = tk.Entry(dialog, font=('Arial', 11), width=40)
        if existing_event:
            time_entry.insert(0, existing_event.get('time', '10:00 AM'))
        else:
            time_entry.insert(0, "10:00 AM")
        time_entry.pack(padx=20, pady=5)
        
        # Description
        tk.Label(dialog, text="Description:", font=('Arial', 10),
                bg='white').pack(pady=(10, 5), anchor='w', padx=20)
        desc_text = tk.Text(dialog, font=('Arial', 10), width=40, height=4)
        desc_text.pack(padx=20, pady=5)
        if existing_event:
            desc_text.insert('1.0', existing_event.get('description', ''))
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg='white')
        btn_frame.pack(pady=20)
        
        def save_event():
            title = title_entry.get().strip()
            if not title:
                messagebox.showwarning("Warning", "Please enter event title")
                return
            
            try:
                new_date_str = f"{year_var.get()}-{int(month_var.get()):02d}-{int(day_var.get()):02d}"
                event_date = datetime.strptime(new_date_str, '%Y-%m-%d')
                
                # Check if date is in the past (only for new events or if date changed)
                # Allow events on today
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                if not edit_mode or new_date_str != date_str:
                    if event_date < today:
                        messagebox.showerror("Error", 
                                           "Cannot create events in the past.\nPlease select today or a future date.")
                        return
            except:
                messagebox.showerror("Error", "Invalid date format")
                return
            
            event = {
                'title': title,
                'time': time_entry.get(),
                'description': desc_text.get('1.0', 'end-1c')
            }
            
            if edit_mode:
                # Remove old event
                if date_str in self.events and event_idx < len(self.events[date_str]):
                    del self.events[date_str][event_idx]
                    if not self.events[date_str]:
                        del self.events[date_str]
            
            # Add new/updated event
            if new_date_str not in self.events:
                self.events[new_date_str] = []
            self.events[new_date_str].append(event)
            
            self.save_events()
            self.update_calendar()
            dialog.destroy()
            messagebox.showinfo("Success", 
                              "Event updated successfully!" if edit_mode else "Event created successfully!")
        
        def delete_event():
            if edit_mode and messagebox.askyesno("Confirm Delete", 
                                                "Are you sure you want to delete this event?"):
                if date_str in self.events and event_idx < len(self.events[date_str]):
                    del self.events[date_str][event_idx]
                    if not self.events[date_str]:
                        del self.events[date_str]
                    self.save_events()
                    self.update_calendar()
                    dialog.destroy()
                    messagebox.showinfo("Success", "Event deleted successfully!")
        
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 bg='white', relief='solid', bd=1, padx=15, pady=5).pack(side='left', padx=5)
        
        if edit_mode:
            tk.Button(btn_frame, text="Delete", command=delete_event,
                     bg='#dc3545', fg='white', relief='flat', padx=15, pady=5).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="Save", command=save_event,
                 bg='#1a73e8', fg='white', relief='flat', padx=20, pady=5).pack(side='left', padx=5)
    
    def edit_event(self, date_str, event_idx):
        """Edit an existing event"""
        self.open_event_dialog(edit_mode=True, date_str=date_str, event_idx=event_idx)
    
    def prev_month(self):
        """Go to previous month"""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year-1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month-1)
        self.update_calendar()
    
    def next_month(self):
        """Go to next month"""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year+1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month+1)
        self.update_calendar()
    
    def goto_today(self):
        """Go to current month"""
        self.current_date = datetime.now()
        self.update_calendar()

if __name__ == "__main__":
    root = tk.Tk()
    app = CalendarApp(root)
    root.mainloop()