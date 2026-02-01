#!/usr/bin/env python3
"""
macOS Time Tracker - Automatic application usage tracking
Tracks active window focus time and generates daily reports
"""

import sqlite3
import rumps
from AppKit import NSWorkspace, NSApplicationActivationPolicyRegular
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID
)
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import time
import threading

class TimeTrackerApp(rumps.App):
    def __init__(self):
        super(TimeTrackerApp, self).__init__(
            "⏱️",
            quit_button=None
        )
        
        # Setup paths
        self.home_dir = Path.home() / ".timetracker"
        self.home_dir.mkdir(exist_ok=True)
        self.db_path = self.home_dir / "tracking.db"
        
        # Initialize database
        self.init_database()
        
        # Tracking state
        self.current_app = None
        self.current_window = None
        self.session_start = None
        self.is_tracking = True
        self.last_activity = datetime.now()
        self.idle_threshold = 300  # 5 minutes in seconds
        
        # Live tracking menu items (will be updated dynamically)
        self.live_tracking_items = []
        
        # Menu items
        self.menu = [
            rumps.MenuItem("📊 Live Tracking", callback=None),
            rumps.MenuItem("─" * 40, callback=None),
            None,
            rumps.MenuItem("Today's Summary", callback=self.show_today_summary),
            rumps.MenuItem("View Report", callback=self.view_report),
            None,
            rumps.MenuItem("Pause Tracking", callback=self.toggle_tracking),
            None,
            rumps.MenuItem("Export Data", callback=self.export_data),
            rumps.MenuItem("Settings", callback=self.show_settings),
            None,
            rumps.MenuItem("Quit", callback=self.quit_app)
        ]
        
        # Start tracking thread
        self.tracking_thread = threading.Thread(target=self.track_active_window, daemon=True)
        self.tracking_thread.start()
        
        # Start menu update thread
        self.menu_update_thread = threading.Thread(target=self.update_menu_display, daemon=True)
        self.menu_update_thread.start()
        
    def init_database(self):
        """Initialize SQLite database for tracking data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT NOT NULL,
                window_title TEXT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                duration INTEGER NOT NULL,
                date TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                total_active_time INTEGER NOT NULL,
                apps_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_date ON app_usage(date)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_app_name ON app_usage(app_name)
        ''')
        
        conn.commit()
        conn.close()
        
    def get_active_window_info(self):
        """Get the currently active window and application"""
        try:
            # Get active application
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.activeApplication()
            app_name = active_app.get('NSApplicationName', 'Unknown')
            
            # Get window title
            window_list = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly,
                kCGNullWindowID
            )
            
            window_title = "Unknown"
            for window in window_list:
                owner_name = window.get('kCGWindowOwnerName', '')
                if owner_name == app_name:
                    window_title = window.get('kCGWindowName', 'No Title')
                    if window_title and window_title != '':
                        break
            
            return app_name, window_title
            
        except Exception as e:
            print(f"Error getting window info: {e}")
            return None, None
    
    def save_session(self, app_name, window_title, start_time, end_time):
        """Save a tracking session to the database"""
        if not app_name or start_time >= end_time:
            return
            
        duration = int((end_time - start_time).total_seconds())
        
        # Only save sessions longer than 1 second
        if duration < 1:
            return
            
        date_str = start_time.strftime('%Y-%m-%d')
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO app_usage (app_name, window_title, start_time, end_time, duration, date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (app_name, window_title, start_time.isoformat(), end_time.isoformat(), duration, date_str))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error saving session: {e}")
    
    def track_active_window(self):
        """Main tracking loop - runs in background thread"""
        while True:
            try:
                if not self.is_tracking:
                    time.sleep(1)
                    continue
                
                app_name, window_title = self.get_active_window_info()
                current_time = datetime.now()
                
                # Check for idle time
                if self.session_start:
                    idle_time = (current_time - self.last_activity).total_seconds()
                    if idle_time > self.idle_threshold:
                        # User has been idle, end previous session
                        if self.current_app:
                            self.save_session(self.current_app, self.current_window, 
                                            self.session_start, self.last_activity)
                        self.current_app = None
                        self.session_start = None
                
                # Check if app changed
                if app_name != self.current_app:
                    # Save previous session
                    if self.current_app and self.session_start:
                        self.save_session(self.current_app, self.current_window, 
                                        self.session_start, current_time)
                    
                    # Start new session
                    self.current_app = app_name
                    self.current_window = window_title
                    self.session_start = current_time
                
                self.last_activity = current_time
                
                # Update every 2 seconds
                time.sleep(2)
                
            except Exception as e:
                print(f"Tracking error: {e}")
                time.sleep(5)
    
    def get_today_stats(self):
        """Get statistics for today"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT app_name, SUM(duration) as total_time
                FROM app_usage
                WHERE date = ?
                GROUP BY app_name
                ORDER BY total_time DESC
            ''', (today,))
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"Error getting stats: {e}")
            return []
    
    def get_current_session_time(self):
        """Get the duration of the current active session"""
        if self.current_app and self.session_start:
            return int((datetime.now() - self.session_start).total_seconds())
        return 0
    
    def update_menu_display(self):
        """Update the menu bar with live tracking info - runs in background thread"""
        while True:
            try:
                if not self.is_tracking:
                    time.sleep(5)
                    continue
                
                # Get today's stats from database
                stats = self.get_today_stats()
                
                # Create a dictionary to accumulate times
                app_times = {}
                for app_name, duration in stats:
                    app_times[app_name] = duration
                
                # Add current session time to the active app
                if self.current_app:
                    current_session_time = self.get_current_session_time()
                    if self.current_app in app_times:
                        app_times[self.current_app] += current_session_time
                    else:
                        app_times[self.current_app] = current_session_time
                
                # Sort by time and get top 5
                sorted_apps = sorted(app_times.items(), key=lambda x: x[1], reverse=True)[:5]
                
                # Calculate total time
                total_time = sum(duration for _, duration in sorted_apps)
                
                # Clear existing live tracking items from menu
                # Remove old items (indices 2 to 2+len(live_tracking_items)-1)
                while len(self.live_tracking_items) > 0:
                    item = self.live_tracking_items.pop()
                    try:
                        del self.menu[2]
                    except:
                        break
                
                # Add new live tracking items
                new_items = []
                
                if sorted_apps:
                    # Add total time at the top
                    total_item = rumps.MenuItem(
                        f"⏱️  Total: {self.format_duration(total_time)}",
                        callback=None
                    )
                    self.menu.insert(2, total_item)
                    new_items.append(total_item)
                    
                    # Add separator
                    sep = rumps.MenuItem("─" * 40, callback=None)
                    self.menu.insert(3, sep)
                    new_items.append(sep)
                    
                    # Add top 5 apps
                    for i, (app_name, duration) in enumerate(sorted_apps):
                        # Add active indicator for current app
                        indicator = "▶ " if app_name == self.current_app else "  "
                        
                        # Format app name (truncate if too long)
                        display_name = app_name[:20] + "..." if len(app_name) > 20 else app_name
                        
                        # Calculate percentage
                        percentage = (duration / total_time * 100) if total_time > 0 else 0
                        
                        item_text = f"{indicator}{display_name}: {self.format_duration(duration)} ({percentage:.0f}%)"
                        menu_item = rumps.MenuItem(item_text, callback=None)
                        
                        self.menu.insert(4 + i, menu_item)
                        new_items.append(menu_item)
                else:
                    # No data yet
                    no_data_item = rumps.MenuItem("No tracking data yet...", callback=None)
                    self.menu.insert(2, no_data_item)
                    new_items.append(no_data_item)
                
                self.live_tracking_items = new_items
                
                # Update every 5 seconds
                time.sleep(5)
                
            except Exception as e:
                print(f"Menu update error: {e}")
                time.sleep(10)
    
    def format_duration(self, seconds):
        """Format seconds into readable duration"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    @rumps.clicked("Today's Summary")
    def show_today_summary(self, _):
        """Show today's usage summary"""
        stats = self.get_today_stats()
        
        if not stats:
            rumps.alert("No Data", "No tracking data for today yet.")
            return
        
        total_time = sum(duration for _, duration in stats)
        
        message = f"Total Active Time: {self.format_duration(total_time)}\n\n"
        message += "Application Usage:\n"
        message += "-" * 40 + "\n"
        
        for app_name, duration in stats[:10]:  # Top 10 apps
            percentage = (duration / total_time * 100) if total_time > 0 else 0
            message += f"{app_name}: {self.format_duration(duration)} ({percentage:.1f}%)\n"
        
        rumps.alert("Today's Summary", message)
    
    @rumps.clicked("View Report")
    def view_report(self, _):
        """Generate and open detailed report"""
        report_path = self.generate_daily_report()
        if report_path:
            os.system(f'open "{report_path}"')
    
    @rumps.clicked("Pause Tracking")
    def toggle_tracking(self, sender):
        """Toggle tracking on/off"""
        self.is_tracking = not self.is_tracking
        
        if self.is_tracking:
            sender.title = "Pause Tracking"
            self.title = "⏱️"
        else:
            sender.title = "Resume Tracking"
            self.title = "⏸️"
            
            # Save session when pausing
            if self.current_app and self.session_start:
                self.save_session(self.current_app, self.current_window, 
                                self.session_start, datetime.now())
                self.current_app = None
                self.session_start = None
            
            # Clear live tracking items when paused
            while len(self.live_tracking_items) > 0:
                item = self.live_tracking_items.pop()
                try:
                    del self.menu[2]
                except:
                    break
            
            # Add paused message
            if not self.is_tracking:
                paused_item = rumps.MenuItem("⏸️  Tracking Paused", callback=None)
                self.menu.insert(2, paused_item)
                self.live_tracking_items.append(paused_item)
    
    @rumps.clicked("Export Data")
    def export_data(self, _):
        """Export data to CSV"""
        export_path = self.home_dir / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT date, app_name, window_title, start_time, end_time, duration
                FROM app_usage
                ORDER BY start_time DESC
            ''')
            
            with open(export_path, 'w') as f:
                f.write("Date,Application,Window Title,Start Time,End Time,Duration (seconds)\n")
                for row in cursor.fetchall():
                    f.write(','.join(f'"{str(item)}"' for item in row) + '\n')
            
            conn.close()
            
            rumps.alert("Export Successful", f"Data exported to:\n{export_path}")
            os.system(f'open "{self.home_dir}"')
            
        except Exception as e:
            rumps.alert("Export Failed", f"Error: {str(e)}")
    
    @rumps.clicked("Settings")
    def show_settings(self, _):
        """Show settings dialog"""
        current_idle = self.idle_threshold // 60
        response = rumps.Window(
            message=f"Current idle timeout: {current_idle} minutes",
            title="Settings",
            default_text=str(current_idle),
            ok="Save",
            cancel="Cancel",
            dimensions=(200, 20)
        ).run()
        
        if response.clicked:
            try:
                new_idle = int(response.text)
                if new_idle > 0:
                    self.idle_threshold = new_idle * 60
                    rumps.alert("Settings Updated", f"Idle timeout set to {new_idle} minutes")
            except ValueError:
                rumps.alert("Invalid Input", "Please enter a valid number")
    
    def generate_daily_report(self):
        """Generate HTML report for today"""
        today = datetime.now().strftime('%Y-%m-%d')
        report_path = self.home_dir / f"report_{today}.html"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get app statistics
            cursor.execute('''
                SELECT app_name, SUM(duration) as total_time, COUNT(*) as sessions
                FROM app_usage
                WHERE date = ?
                GROUP BY app_name
                ORDER BY total_time DESC
            ''', (today,))
            
            app_stats = cursor.fetchall()
            
            # Get hourly breakdown
            cursor.execute('''
                SELECT strftime('%H', start_time) as hour, SUM(duration) as total_time
                FROM app_usage
                WHERE date = ?
                GROUP BY hour
                ORDER BY hour
            ''', (today,))
            
            hourly_stats = cursor.fetchall()
            
            conn.close()
            
            total_time = sum(duration for _, duration, _ in app_stats)
            
            # Generate HTML
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Time Tracker Report - {today}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f7;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1d1d1f;
            margin-bottom: 10px;
        }}
        .summary {{
            background: #007aff;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .summary h2 {{
            margin: 0 0 10px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e5e7;
        }}
        th {{
            background: #f5f5f7;
            font-weight: 600;
        }}
        .bar {{
            background: #007aff;
            height: 20px;
            border-radius: 4px;
            transition: width 0.3s;
        }}
        .bar-container {{
            background: #e5e5e7;
            border-radius: 4px;
            overflow: hidden;
        }}
        .hour-chart {{
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            height: 200px;
            margin: 30px 0;
            padding: 10px;
            border: 1px solid #e5e5e7;
            border-radius: 8px;
        }}
        .hour-bar {{
            flex: 1;
            background: #007aff;
            margin: 0 2px;
            border-radius: 4px 4px 0 0;
            min-height: 2px;
            position: relative;
        }}
        .hour-label {{
            text-align: center;
            font-size: 11px;
            color: #666;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Daily Time Tracking Report</h1>
        <p style="color: #666;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <h2>Total Active Time</h2>
            <h1 style="margin: 0;">{self.format_duration(total_time)}</h1>
        </div>
        
        <h2>Application Usage</h2>
        <table>
            <thead>
                <tr>
                    <th>Application</th>
                    <th>Total Time</th>
                    <th>Sessions</th>
                    <th>Percentage</th>
                    <th>Usage</th>
                </tr>
            </thead>
            <tbody>
"""
            
            for app_name, duration, sessions in app_stats:
                percentage = (duration / total_time * 100) if total_time > 0 else 0
                html += f"""
                <tr>
                    <td><strong>{app_name}</strong></td>
                    <td>{self.format_duration(duration)}</td>
                    <td>{sessions}</td>
                    <td>{percentage:.1f}%</td>
                    <td>
                        <div class="bar-container">
                            <div class="bar" style="width: {percentage}%"></div>
                        </div>
                    </td>
                </tr>
"""
            
            html += """
            </tbody>
        </table>
        
        <h2>Hourly Activity</h2>
        <div class="hour-chart">
"""
            
            # Create hourly chart
            hourly_dict = {int(hour): duration for hour, duration in hourly_stats}
            max_hour_time = max(hourly_dict.values()) if hourly_dict else 1
            
            for hour in range(24):
                hour_time = hourly_dict.get(hour, 0)
                height_percent = (hour_time / max_hour_time * 100) if max_hour_time > 0 else 0
                html += f"""
            <div style="flex: 1; display: flex; flex-direction: column; align-items: center;">
                <div class="hour-bar" style="height: {height_percent}%" title="{self.format_duration(hour_time)}"></div>
                <div class="hour-label">{hour:02d}:00</div>
            </div>
"""
            
            html += """
        </div>
    </div>
</body>
</html>
"""
            
            with open(report_path, 'w') as f:
                f.write(html)
            
            return report_path
            
        except Exception as e:
            print(f"Error generating report: {e}")
            rumps.alert("Report Error", f"Failed to generate report: {str(e)}")
            return None
    
    @rumps.clicked("Quit")
    def quit_app(self, _):
        """Quit the application"""
        # Save current session before quitting
        if self.current_app and self.session_start:
            self.save_session(self.current_app, self.current_window, 
                            self.session_start, datetime.now())
        
        rumps.quit_application()


if __name__ == "__main__":
    app = TimeTrackerApp()
    app.run()