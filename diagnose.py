#!/usr/bin/env python3
"""
Time Tracker Diagnostic Tool
Checks system requirements and helps troubleshoot common issues
"""

import sys
import os
import subprocess
from pathlib import Path

class DiagnosticTool:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.success = []
    
    def print_header(self):
        print("=" * 70)
        print("  TIME TRACKER DIAGNOSTIC TOOL")
        print("=" * 70)
        print()
    
    def check_python_version(self):
        """Check if Python version is compatible"""
        print("🔍 Checking Python version...")
        
        version = sys.version_info
        if version.major >= 3 and version.minor >= 7:
            self.success.append(f"✅ Python {version.major}.{version.minor}.{version.micro} (OK)")
        else:
            self.issues.append(f"❌ Python {version.major}.{version.minor} is too old. Need Python 3.7+")
    
    def check_dependencies(self):
        """Check if required packages are installed"""
        print("🔍 Checking dependencies...")
        
        required = ['rumps', 'PyObjC']
        
        for package in required:
            try:
                if package == 'PyObjC':
                    import AppKit
                    import Quartz
                    self.success.append(f"✅ {package} installed")
                elif package == 'rumps':
                    import rumps
                    self.success.append(f"✅ {package} installed")
            except ImportError:
                self.issues.append(f"❌ {package} not installed. Run: pip3 install --user {package}")
    
    def check_database(self):
        """Check if database exists and is accessible"""
        print("🔍 Checking database...")
        
        db_path = Path.home() / ".timetracker" / "tracking.db"
        
        if db_path.exists():
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM app_usage")
                count = cursor.fetchone()[0]
                conn.close()
                self.success.append(f"✅ Database found with {count} records")
            except Exception as e:
                self.issues.append(f"❌ Database error: {str(e)}")
        else:
            self.warnings.append(f"⚠️  No database found (will be created on first run)")
    
    def check_permissions(self):
        """Check if Accessibility permissions might be granted"""
        print("🔍 Checking system permissions...")
        
        # We can't directly check this without running the app
        # But we can provide guidance
        self.warnings.append("⚠️  Cannot verify Accessibility permissions from here")
        print("\n  To check manually:")
        print("  1. Open System Settings")
        print("  2. Go to Privacy & Security > Accessibility")
        print("  3. Look for Python or TimeTracker in the list")
        print("  4. Make sure it's enabled")
    
    def check_disk_space(self):
        """Check available disk space"""
        print("🔍 Checking disk space...")
        
        try:
            import shutil
            total, used, free = shutil.disk_usage(Path.home())
            
            free_gb = free // (1024 ** 3)
            
            if free_gb > 1:
                self.success.append(f"✅ Plenty of disk space ({free_gb} GB free)")
            else:
                self.warnings.append(f"⚠️  Low disk space ({free_gb} GB free)")
        except Exception as e:
            self.warnings.append(f"⚠️  Could not check disk space: {str(e)}")
    
    def check_macos_version(self):
        """Check macOS version"""
        print("🔍 Checking macOS version...")
        
        try:
            result = subprocess.run(['sw_vers', '-productVersion'], 
                                  capture_output=True, text=True)
            version = result.stdout.strip()
            
            # Extract major version
            major = int(version.split('.')[0])
            
            if major >= 10:
                self.success.append(f"✅ macOS {version}")
            else:
                self.warnings.append(f"⚠️  macOS {version} might not be supported")
        except Exception as e:
            self.warnings.append(f"⚠️  Could not determine macOS version: {str(e)}")
    
    def check_files_exist(self):
        """Check if required files are present"""
        print("🔍 Checking required files...")
        
        current_dir = Path(__file__).parent
        required_files = ['time_tracker.py', 'requirements.txt']
        
        for filename in required_files:
            filepath = current_dir / filename
            if filepath.exists():
                self.success.append(f"✅ Found {filename}")
            else:
                self.issues.append(f"❌ Missing {filename}")
    
    def test_window_detection(self):
        """Test if we can detect active windows"""
        print("🔍 Testing window detection...")
        
        try:
            from AppKit import NSWorkspace
            from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
            
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.activeApplication()
            app_name = active_app.get('NSApplicationName', 'Unknown')
            
            if app_name and app_name != 'Unknown':
                self.success.append(f"✅ Window detection working (current: {app_name})")
            else:
                self.warnings.append("⚠️  Window detection might need permissions")
        except Exception as e:
            self.issues.append(f"❌ Window detection failed: {str(e)}")
    
    def run_diagnostics(self):
        """Run all diagnostic checks"""
        self.print_header()
        
        self.check_python_version()
        self.check_macos_version()
        self.check_dependencies()
        self.check_files_exist()
        self.check_database()
        self.check_disk_space()
        self.check_permissions()
        self.test_window_detection()
        
        print()
        print("=" * 70)
        print("  DIAGNOSTIC RESULTS")
        print("=" * 70)
        print()
        
        if self.success:
            print("✅ SUCCESSES:")
            for msg in self.success:
                print(f"  {msg}")
            print()
        
        if self.warnings:
            print("⚠️  WARNINGS:")
            for msg in self.warnings:
                print(f"  {msg}")
            print()
        
        if self.issues:
            print("❌ ISSUES FOUND:")
            for msg in self.issues:
                print(f"  {msg}")
            print()
            print("=" * 70)
            print("  RECOMMENDED ACTIONS")
            print("=" * 70)
            print()
            print("1. Install missing dependencies:")
            print("   ./install.sh")
            print()
            print("2. Grant Accessibility permissions:")
            print("   System Settings > Privacy & Security > Accessibility")
            print()
            print("3. If still having issues, check README.md for troubleshooting")
            print()
        else:
            print("=" * 70)
            print("  🎉 ALL CHECKS PASSED!")
            print("=" * 70)
            print()
            print("Your system is ready to run the Time Tracker.")
            print()
            print("To start:")
            print("  python3 time_tracker.py")
            print()
    
    def interactive_menu(self):
        """Provide an interactive troubleshooting menu"""
        print()
        print("=" * 70)
        print("  TROUBLESHOOTING MENU")
        print("=" * 70)
        print()
        print("1. Re-run diagnostics")
        print("2. View database contents")
        print("3. Check log files")
        print("4. Test permissions")
        print("5. Reset database (WARNING: deletes all data)")
        print("6. Exit")
        print()
        
        choice = input("Enter choice (1-6): ").strip()
        
        if choice == '1':
            self.__init__()  # Reset
            self.run_diagnostics()
            self.interactive_menu()
        elif choice == '2':
            self.view_database()
            self.interactive_menu()
        elif choice == '3':
            print("\n⚠️  No log files currently implemented.")
            print("Errors are printed to console when running time_tracker.py")
            self.interactive_menu()
        elif choice == '4':
            self.test_permissions()
            self.interactive_menu()
        elif choice == '5':
            self.reset_database()
            self.interactive_menu()
        elif choice == '6':
            print("\n👋 Goodbye!")
            return
        else:
            print("\n❌ Invalid choice")
            self.interactive_menu()
    
    def view_database(self):
        """Quick view of database contents"""
        db_path = Path.home() / ".timetracker" / "tracking.db"
        
        if not db_path.exists():
            print("\n❌ No database found")
            return
        
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM app_usage")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT date) FROM app_usage")
            days = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT app_name) FROM app_usage")
            apps = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(duration) FROM app_usage")
            total_time = cursor.fetchone()[0] or 0
            
            conn.close()
            
            print(f"\n📊 Database Statistics:")
            print(f"  Total records: {total}")
            print(f"  Days tracked: {days}")
            print(f"  Different apps: {apps}")
            print(f"  Total time: {total_time // 3600}h {(total_time % 3600) // 60}m")
        except Exception as e:
            print(f"\n❌ Error reading database: {str(e)}")
    
    def test_permissions(self):
        """Test if app has necessary permissions"""
        print("\n🔍 Testing permissions...")
        
        try:
            from AppKit import NSWorkspace
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.activeApplication()
            
            if active_app:
                print("✅ Can access application information")
                print(f"   Current app: {active_app.get('NSApplicationName', 'Unknown')}")
            else:
                print("❌ Cannot access application information")
                print("   You may need to grant Accessibility permissions")
        except Exception as e:
            print(f"❌ Permission test failed: {str(e)}")
            print("   This likely means Accessibility permissions are not granted")
    
    def reset_database(self):
        """Reset the database (with confirmation)"""
        print("\n⚠️  WARNING: This will delete ALL tracking data!")
        confirm = input("Type 'YES' to confirm: ").strip()
        
        if confirm != 'YES':
            print("❌ Cancelled")
            return
        
        db_path = Path.home() / ".timetracker" / "tracking.db"
        
        if db_path.exists():
            try:
                db_path.unlink()
                print("✅ Database deleted")
                print("   A new database will be created on next run")
            except Exception as e:
                print(f"❌ Error deleting database: {str(e)}")
        else:
            print("❌ No database to delete")


if __name__ == "__main__":
    tool = DiagnosticTool()
    tool.run_diagnostics()
    
    print()
    continue_menu = input("Would you like to access the troubleshooting menu? (y/n): ").strip().lower()
    if continue_menu == 'y':
        tool.interactive_menu()