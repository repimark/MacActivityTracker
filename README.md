# QUICK START GUIDE

## Get Started in 3 Steps 🚀

### Step 1: Install Dependencies
```bash
./install.sh
```

The installer will:
- Check for Python 3
- Install required packages (rumps, pyobjc)
- Create launch scripts
- Optionally create a macOS app bundle

### Step 2: Grant Permissions

When you first run the app, macOS will ask for permissions:

1. **System Settings** → **Privacy & Security** → **Accessibility**
2. Click the **lock icon** to make changes
3. Click the **+** button and add **Python** or **TimeTracker**
4. **Enable the toggle** next to it

This is required for the app to monitor which windows are active.

### Step 3: Launch the Tracker

Choose one method:

**Option A: Direct launch**
```bash
python3 time_tracker.py
```

**Option B: Using the launch script**
```bash
./launch_tracker.sh
```

**Option C: Double-click the app** (if you created TimeTracker.app during installation)

---

## What You'll See

Once running, you'll see a **⏱️ icon** in your menu bar (top-right corner of your screen).

Click it to access:
- **Today's Summary** - Quick stats
- **View Report** - Detailed HTML report
- **Pause Tracking** - Temporarily stop
- **Export Data** - Save to CSV
- **Settings** - Configure idle timeout
- **Quit** - Close the app

---

## First-Time Tips

✅ **Let it run** - The tracker works best when it runs all day  
✅ **Check after an hour** - Click "Today's Summary" to see initial data  
✅ **Review end of day** - Click "View Report" for detailed insights  
✅ **Don't worry about breaks** - Idle detection pauses tracking automatically  

---

## Common First-Time Issues

### "Permission Denied" or "No tracking data"
→ You need to grant Accessibility permissions (see Step 2 above)

### Menu bar icon not showing
→ The app might be running in background. Check Activity Monitor for "Python"

### Nothing is being tracked
→ Make sure the icon shows ⏱️ (not ⏸️) - if paused, click to resume

---

## Where Is My Data?

All data is stored in:
```
~/.timetracker/
├── tracking.db              # Your tracking database
├── report_2026-02-01.html   # Daily HTML reports
└── export_*.csv             # Exported CSV files
```

You can view this folder anytime:
```bash
open ~/.timetracker
```

---

## View Your Data Without the Menu Bar

Use the included data viewer:
```bash
python3 view_data.py
```

This provides a terminal-based interface to:
- View today's summary
- Check last 7 days
- Search by application
- See all-time top apps

---

## Next Steps

1. **Run at login** (optional): Add to System Settings → Login Items
2. **Check reports daily**: Get insights into your work patterns
3. **Export for billing**: Use CSV export for client time tracking
4. **Customize settings**: Adjust idle timeout to match your workflow

---

## Need Help?

Check the full **README.md** for:
- Detailed documentation
- Troubleshooting guide
- Advanced usage tips
- FAQ section

---

**You're all set! Happy tracking! 🎉**

The tracker will automatically monitor your work and help you understand where your time goes.