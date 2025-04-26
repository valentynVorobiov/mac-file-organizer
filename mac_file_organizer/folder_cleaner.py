"""
Logic for removing empty folders.
"""
import logging
# from pathlib import Path

from mac_file_organizer.config import (
    MANUAL_FOLDER_NAME, REVIEW_FOLDER_NAME
)

logger = logging.getLogger('mac-file-organizer')


class FolderCleaner:
    """Cleans up empty folders."""

    def __init__(self):
        """Initialize the folder cleaner."""
        pass

    def clean_empty_folders(self, directory):
        """Remove empty folders recursively."""
        # Define special folders to ignore
        special_folders = [MANUAL_FOLDER_NAME, REVIEW_FOLDER_NAME]

        # Track if folders were deleted
        folders_deleted = True

        # Keep cleaning until no more empty folders are found
        while folders_deleted:
            folders_deleted = False

            # Get all subdirectories
            all_dirs = [d for d in directory.glob('**/*') if d.is_dir()]

            # Sort by depth (deepest first)
            all_dirs.sort(key=lambda d: len(d.parts), reverse=True)

            for dir_path in all_dirs:
                # Skip special folders
                if dir_path.name in special_folders:
                    continue

                # Skip if the directory is not empty
                if any(dir_path.iterdir()):
                    continue

                # It's an empty directory, delete it
                try:
                    dir_path.rmdir()
                    logger.info(f"Removed empty folder: {dir_path}")
                    folders_deleted = True
                except Exception as e:
                    logger.error(f"Error removing empty folder {dir_path}: {e}")