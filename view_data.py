#!/usr/bin/env python3
"""
Time Tracker Data Viewer
A simple utility to view your tracking data without opening the database directly
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import sys

class DataViewer:
    def __init__(self):
        self.db_path = Path.home() / ".timetracker" / "tracking.db"
        if not self.db_path.exists():
            print("❌ No tracking database found. Have you started the tracker yet?")
            sys.exit(1)
    
    def format_duration(self, seconds):
        """Format seconds into readable duration"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def show_menu(self):
        """Display main menu"""
        print("\n" + "="*60)
        print("  📊 TIME TRACKER DATA VIEWER")
        print("="*60)
        print("\n1. View Today's Summary")
        print("2. View Yesterday's Summary")
        print("3. View Last 7 Days")
        print("4. View Specific Date")
        print("5. View All-Time Top Applications")
        print("6. Search by Application")
        print("7. Exit")
        print("\n" + "="*60)
        
        choice = input("\nEnter your choice (1-7): ").strip()
        return choice
    
    def get_date_stats(self, date_str):
        """Get statistics for a specific date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT app_name, SUM(duration) as total_time, COUNT(*) as sessions
            FROM app_usage
            WHERE date = ?
            GROUP BY app_name
            ORDER BY total_time DESC
        ''', (date_str,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def display_day_summary(self, date_str, title="Summary"):
        """Display summary for a day"""
        stats = self.get_date_stats(date_str)
        
        if not stats:
            print(f"\n❌ No data found for {date_str}")
            return
        
        total_time = sum(duration for _, duration, _ in stats)
        
        print(f"\n{'='*60}")
        print(f"  {title} - {date_str}")
        print(f"{'='*60}")
        print(f"\n⏱️  Total Active Time: {self.format_duration(total_time)}")
        print(f"📱 Applications Used: {len(stats)}")
        print(f"\n{'Application':<30} {'Time':<15} {'Sessions':<10} {'%'}")
        print("-"*60)
        
        for app_name, duration, sessions in stats:
            percentage = (duration / total_time * 100) if total_time > 0 else 0
            print(f"{app_name:<30} {self.format_duration(duration):<15} {sessions:<10} {percentage:>5.1f}%")
    
    def view_today(self):
        """View today's summary"""
        today = datetime.now().strftime('%Y-%m-%d')
        self.display_day_summary(today, "Today's Summary")
    
    def view_yesterday(self):
        """View yesterday's summary"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.display_day_summary(yesterday, "Yesterday's Summary")
    
    def view_last_7_days(self):
        """View summary for last 7 days"""
        print(f"\n{'='*60}")
        print("  LAST 7 DAYS SUMMARY")
        print(f"{'='*60}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get data for last 7 days
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT SUM(duration), COUNT(DISTINCT app_name)
                FROM app_usage
                WHERE date = ?
            ''', (date,))
            
            result = cursor.fetchone()
            total_time = result[0] if result[0] else 0
            app_count = result[1] if result[1] else 0
            
            day_name = (datetime.now() - timedelta(days=i)).strftime('%A')
            
            print(f"\n{day_name}, {date}:")
            if total_time > 0:
                print(f"  ⏱️  Active Time: {self.format_duration(total_time)}")
                print(f"  📱 Apps Used: {app_count}")
            else:
                print("  No data")
        
        conn.close()
    
    def view_specific_date(self):
        """View data for a specific date"""
        date_str = input("\nEnter date (YYYY-MM-DD): ").strip()
        
        try:
            # Validate date format
            datetime.strptime(date_str, '%Y-%m-%d')
            self.display_day_summary(date_str, f"Summary for {date_str}")
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD")
    
    def view_top_apps(self):
        """View all-time top applications"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT app_name, SUM(duration) as total_time, COUNT(*) as total_sessions,
                   COUNT(DISTINCT date) as days_used
            FROM app_usage
            GROUP BY app_name
            ORDER BY total_time DESC
            LIMIT 20
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            print("\n❌ No data found")
            return
        
        total_time = sum(duration for _, duration, _, _ in results)
        
        print(f"\n{'='*70}")
        print("  🏆 ALL-TIME TOP APPLICATIONS")
        print(f"{'='*70}")
        print(f"\n{'Application':<25} {'Total Time':<15} {'Sessions':<12} {'Days':<8} {'%'}")
        print("-"*70)
        
        for app_name, duration, sessions, days in results:
            percentage = (duration / total_time * 100) if total_time > 0 else 0
            print(f"{app_name:<25} {self.format_duration(duration):<15} {sessions:<12} {days:<8} {percentage:>5.1f}%")
    
    def search_by_app(self):
        """Search and view data for a specific application"""
        app_name = input("\nEnter application name (e.g., Safari, Terminal): ").strip()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, SUM(duration) as total_time, COUNT(*) as sessions
            FROM app_usage
            WHERE app_name LIKE ?
            GROUP BY date
            ORDER BY date DESC
            LIMIT 30
        ''', (f'%{app_name}%',))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            print(f"\n❌ No data found for '{app_name}'")
            return
        
        total_time = sum(duration for _, duration, _ in results)
        total_sessions = sum(sessions for _, _, sessions in results)
        
        print(f"\n{'='*60}")
        print(f"  📊 USAGE HISTORY: {app_name}")
        print(f"{'='*60}")
        print(f"\nTotal Time: {self.format_duration(total_time)}")
        print(f"Total Sessions: {total_sessions}")
        print(f"Days Used: {len(results)}")
        
        print(f"\n{'Date':<15} {'Time':<20} {'Sessions'}")
        print("-"*60)
        
        for date, duration, sessions in results[:20]:  # Show last 20 days
            print(f"{date:<15} {self.format_duration(duration):<20} {sessions}")
    
    def run(self):
        """Main application loop"""
        while True:
            choice = self.show_menu()
            
            if choice == '1':
                self.view_today()
            elif choice == '2':
                self.view_yesterday()
            elif choice == '3':
                self.view_last_7_days()
            elif choice == '4':
                self.view_specific_date()
            elif choice == '5':
                self.view_top_apps()
            elif choice == '6':
                self.search_by_app()
            elif choice == '7':
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    viewer = DataViewer()
    viewer.run()