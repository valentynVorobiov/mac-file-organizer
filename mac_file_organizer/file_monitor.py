"""
Monitoring file access times.
"""
import os
import time
import logging
from pathlib import Path

from mac_file_organizer.config import (
    REVIEW_THRESHOLD, MANUAL_FOLDER_NAME, REVIEW_FOLDER_NAME
)

logger = logging.getLogger('mac-file-organizer')


class FileMonitor:
    """Monitors file access times."""

    def __init__(self):
        """Initialize the file monitor."""
        pass

    def get_old_files(self, directory):
        """Get files that haven't been accessed in the threshold period."""
        old_files = []
        now = time.time()

        # Define special folders to ignore
        special_folders = [directory / MANUAL_FOLDER_NAME, directory / REVIEW_FOLDER_NAME]

        # Recursively scan the directory
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)

            # Skip special folders and app bundle internals
            if (any(str(root_path).startswith(str(folder)) for folder in special_folders) or
                (".app/" in str(root_path) or ".app\\" in str(root_path))):
                continue

            # Check each file
            for filename in files:
                file_path = root_path / filename

                try:
                    # Get last access time
                    atime = file_path.stat().st_atime

                    # Check if file is old enough
                    if now - atime > REVIEW_THRESHOLD:
                        old_files.append(file_path)
                except Exception as e:
                    logger.error(f"Error checking access time for {file_path}: {e}")

            # Check each directory (except top-level category dirs)
            for dirname in dirs:
                dir_path = root_path / dirname

                # Skip top-level category directories and hidden directories
                if root_path == directory or dirname.startswith('.'):
                    continue

                try:
                    # Get last access time
                    atime = dir_path.stat().st_atime

                    # Check if directory is old enough
                    if now - atime > REVIEW_THRESHOLD:
                        old_files.append(dir_path)
                except Exception as e:
                    logger.error(f"Error checking access time for directory {dir_path}: {e}")

        return old_files