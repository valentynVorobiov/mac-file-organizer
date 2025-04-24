"""
Logic for classifying files by type.
"""
import logging
import mimetypes
from pathlib import Path

from mac_file_organizer.config import get_file_categories

logger = logging.getLogger('mac-file-organizer')


class FileClassifier:
    """Classifies files into categories based on extension and mimetype."""

    def __init__(self):
        """Initialize the file classifier."""
        self.categories = get_file_categories()

        # Ensure mimetypes are initialized
        mimetypes.init()

    def get_categories(self):
        """Return the list of top-level categories."""
        return list(self.categories.keys())

    def classify_file(self, file_path):
        """Classify a file into a category."""
        # Get file extension without dot
        extension = file_path.suffix.lower().lstrip('.')

        # Check each category for this extension
        for category, extensions in self.categories.items():
            if extension in extensions:
                return category

        # If no match by extension, try using mimetype
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                main_type = mime_type.split('/')[0]

                if main_type == 'image':
                    return 'Images'
                elif main_type == 'video':
                    return 'Videos'
                elif main_type == 'audio':
                    return 'Audio'
                elif main_type == 'text':
                    return 'Documents'
                elif main_type == 'application':
                    if 'pdf' in mime_type:
                        return 'Documents'
                    elif any(x in mime_type for x in ['msword', 'office', 'document']):
                        return 'Documents'
                    elif any(x in mime_type for x in ['zip', 'compressed', 'archive']):
                        return 'Archives'
                    elif any(x in mime_type for x in ['executable', 'x-app']):
                        return 'Applications'
        except Exception as e:
            logger.warning(f"Error determining mimetype for {file_path}: {e}")

        # Default category
        return 'Others'