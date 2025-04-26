"""
Configuration settings for the Mac File Organizer.
"""
import json
from pathlib import Path

# User directories
HOME_DIR = Path.home()
DOWNLOADS_DIR = HOME_DIR / "Downloads"
DESKTOP_DIR = HOME_DIR / "Desktop"

# Special folders
MANUAL_FOLDER_NAME = "Manual"
REVIEW_FOLDER_NAME = "Review"

# Tags
MANUAL_TAG = "Manual"
REVIEW_TAG = "Review"
MANUAL_TAG_COLOR = "red"
REVIEW_TAG_COLOR = "blue"

# Time threshold for moving to review (2 weeks in seconds)
REVIEW_THRESHOLD = 60 * 60 * 24 * 14  # 14 days

# Load file categories
def get_file_categories():
    """Load file categories from JSON file."""
    try:
        resource_path = Path(__file__).parent.parent / "resources" / "file_categories.json"
        with open(resource_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Default categories if file not found or invalid
        return {
            "Documents": ["pdf", "doc", "docx", "txt", "rtf", "odt", "pages", "xls", "xlsx", "csv"],
            "Images": ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "svg", "heic"],
            "Videos": ["mp4", "mov", "avi", "wmv", "mkv", "m4v"],
            "Audio": ["mp3", "wav", "aac", "flac", "m4a"],
            "Archives": ["zip", "rar", "7z", "tar", "gz"],
            "Applications": ["dmg", "app", "pkg", "exe"],
            "Code": ["py", "js", "java", "c", "cpp", "html", "css", "sql", "swift"],
            "Others": []
        }

# Scan interval (in seconds)
SCAN_INTERVAL = 3600  # Check every hour

# Debugging flag (set to True for more verbose output)
DEBUG = False
