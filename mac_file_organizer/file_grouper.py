"""
Logic for grouping similar files.
"""
import logging
import re
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher

logger = logging.getLogger('mac-file-organizer')


class FileGrouper:
    """Groups similar files based on name patterns."""

    def __init__(self):
        """Initialize the file grouper."""
        # Threshold for considering strings similar (0-1)
        self.similarity_threshold = 0.6

        # Common patterns to look for in filenames
        self.date_pattern = re.compile(r'(\d{4}[-_]?\d{2}[-_]?\d{2})')
        self.time_pattern = re.compile(r'(\d{2}[_:]?\d{2}[_:]?\d{2})')
        self.common_word_pattern = re.compile(r'[A-Za-z]{3,}')

        # Pattern to extract business/product prefixes
        self.prefix_pattern = re.compile(r'^([a-zA-Z0-9_-]+?)(?:[_-]|$)')

        # Additional patterns
        self.invoice_pattern = re.compile(r'(invoice|receipt|bill|payment)[-_\s]?(\d+)', re.IGNORECASE)
        self.project_pattern = re.compile(r'(project|task|ticket|issue)[-_\s]?(\d+|\w+)', re.IGNORECASE)
        self.version_pattern = re.compile(r'v\d+(\.\d+)*|version[-_\s]?\d+(\.\d+)*', re.IGNORECASE)

    def find_group_for_file(self, file_path, extension_dir):
        """Find or create a group for a file."""
        filename = file_path.stem

        # Check if there are any existing files in existing groups that match this file
        for group_dir in extension_dir.iterdir():
            if not group_dir.is_dir():
                continue

            # Compare this file with files in the group
            if self._is_similar_to_group(filename, group_dir):
                return group_dir.name

        # If no matching group found, we don't automatically create a group for a single file
        # Instead, place it directly in the extension directory using "Ungrouped" as a marker
        return "Ungrouped"

    def find_group_for_folder(self, folder_path, folders_dir):
        """Find or create a group for a folder."""
        folder_name = folder_path.name

        # Check existing groups
        for group_dir in folders_dir.iterdir():
            if not group_dir.is_dir():
                continue

            # Compare this folder with folders in the group
            if self._is_similar_to_group(folder_name, group_dir):
                return group_dir.name

        # If no matching group found, we don't automatically create a group for a single folder
        return "Ungrouped"

    def _is_similar_to_group(self, name, group_dir):
        """Check if the name is similar to files in the group."""
        # Get the first few files from the group (for efficiency)
        files = list(group_dir.iterdir())[:5]

        if not files:
            return False

        # Extract business/vendor prefix from name
        name_prefix = self._extract_business_prefix(name)

        # Check similarity with each file
        for file_path in files:
            file_name = file_path.stem if file_path.is_file() else file_path.name
            file_prefix = self._extract_business_prefix(file_name)

            # If both have meaningful prefixes and they match, this is a strong indicator
            if name_prefix and file_prefix and name_prefix.lower() == file_prefix.lower():
                return True

            # Calculate similarity score
            similarity = self._calculate_name_similarity(name, file_name)
            if similarity >= self.similarity_threshold:
                return True

        return False

    def _extract_business_prefix(self, name):
        """Extract business or vendor prefix from filename."""
        # Try to extract the prefix at the start before any separator
        prefix_match = self.prefix_pattern.search(name)
        if prefix_match:
            prefix = prefix_match.group(1)
            # Only use the prefix if it's meaningful (not just "file", "image", etc.)
            if len(prefix) >= 3 and prefix.lower() not in {'file', 'image', 'img', 'doc', 'document', 'test', 'tmp',
                                                           'temp'}:
                return prefix

        return None

    def _calculate_name_similarity(self, name1, name2):
        """Calculate similarity between two filenames."""
        # Extract prefixes
        prefix1 = self._extract_business_prefix(name1)
        prefix2 = self._extract_business_prefix(name2)

        # If both have meaningful prefixes and they match, this is a strong indicator
        if prefix1 and prefix2 and prefix1.lower() == prefix2.lower():
            return 1.0

        # Check for date pattern match
        date_match_1 = self.date_pattern.search(name1)
        date_match_2 = self.date_pattern.search(name2)

        # For date-based files, only group if the prefixes also match
        if date_match_1 and date_match_2:
            if date_match_1.group(0) == date_match_2.group(0):
                # Same date, but only consider it a match if prefixes are similar
                if prefix1 and prefix2:
                    # Calculate prefix similarity
                    prefix_similarity = SequenceMatcher(None, prefix1.lower(), prefix2.lower()).ratio()
                    if prefix_similarity >= 0.7:  # Higher threshold for prefix similarity
                        return 0.8
                    else:
                        return 0.4  # Below threshold
                else:
                    # Without meaningful prefixes, just having the same date isn't enough
                    return 0.4  # Below threshold

        # Check for invoice/receipt pattern match
        invoice_match_1 = self.invoice_pattern.search(name1)
        invoice_match_2 = self.invoice_pattern.search(name2)

        if invoice_match_1 and invoice_match_2:
            # If they both have invoice/receipt prefixes
            if invoice_match_1.group(1).lower() == invoice_match_2.group(1).lower():
                return 0.8

        # Check for project/task pattern match
        project_match_1 = self.project_pattern.search(name1)
        project_match_2 = self.project_pattern.search(name2)

        if project_match_1 and project_match_2:
            # If they both have project/task prefixes
            if project_match_1.group(1).lower() == project_match_2.group(1).lower():
                return 0.8

        # Check for version pattern match
        version_match_1 = self.version_pattern.search(name1)
        version_match_2 = self.version_pattern.search(name2)

        if version_match_1 and version_match_2:
            return 0.8

        # Check for similar words
        common_words_1 = set(self.common_word_pattern.findall(name1.lower()))
        common_words_2 = set(self.common_word_pattern.findall(name2.lower()))

        if common_words_1 and common_words_2:
            # Check for common words
            common_words = common_words_1.intersection(common_words_2)
            if len(common_words) >= 2:
                return 0.8
            elif len(common_words) == 1 and list(common_words)[0].lower() not in {'the', 'and', 'for', 'with'}:
                # One significant common word
                word = list(common_words)[0].lower()
                # Only consider it meaningful if it's not a common substring of many words
                if len(word) >= 5 and word not in {'image', 'file', 'doc', 'document', 'report'}:
                    return 0.7
                else:
                    return 0.4  # Below threshold

        # Check overall string similarity as last resort
        return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()

    def _extract_group_name(self, name):
        """Extract a suitable group name from the filename."""
        # First, try to extract business/vendor prefix
        prefix = self._extract_business_prefix(name)
        if prefix and len(prefix) >= 3:
            return prefix.capitalize()

        # Check for common document types
        document_types = {
            'invoice': re.compile(r'invoice', re.IGNORECASE),
            'receipt': re.compile(r'receipt', re.IGNORECASE),
            'report': re.compile(r'report', re.IGNORECASE),
            'contract': re.compile(r'contract|agreement', re.IGNORECASE),
            'presentation': re.compile(r'presentation|slides|deck', re.IGNORECASE),
            'resume': re.compile(r'resume|cv', re.IGNORECASE),
            'letter': re.compile(r'letter', re.IGNORECASE),
            'proposal': re.compile(r'proposal', re.IGNORECASE),
            'review': re.compile(r'review', re.IGNORECASE),
            'logs': re.compile(r'logs?', re.IGNORECASE),  # Match 'log' or 'logs'
            'backup': re.compile(r'backup', re.IGNORECASE),
            'screenshot': re.compile(r'screenshot|screen', re.IGNORECASE),
            'form': re.compile(r'form', re.IGNORECASE),
            'template': re.compile(r'template', re.IGNORECASE),
            'manual': re.compile(r'manual|guide|instruction', re.IGNORECASE),
            'notes': re.compile(r'notes?', re.IGNORECASE),  # Match 'note' or 'notes'
            'script': re.compile(r'scripts?', re.IGNORECASE),  # Match 'script' or 'scripts'
            'data': re.compile(r'data', re.IGNORECASE),
            'config': re.compile(r'config|configuration|settings', re.IGNORECASE),
            'project': re.compile(r'project', re.IGNORECASE)
        }

        # Check for document type matches
        for doc_type, pattern in document_types.items():
            if pattern.search(name):
                return doc_type.capitalize()

        # Check for invoice/receipt pattern
        invoice_match = self.invoice_pattern.search(name)
        if invoice_match:
            return invoice_match.group(1).capitalize()

        # Check for project/task pattern
        project_match = self.project_pattern.search(name)
        if project_match:
            return project_match.group(1).capitalize()

        # Try to extract common words (at least 3 letters long)
        words = self.common_word_pattern.findall(name)
        if words:
            # Filter out common noise words
            noise_words = {'the', 'and', 'for', 'with', 'from', 'this', 'that', 'have', 'been', 'were', 'file', 'image',
                           'img', 'doc', 'document', 'test', 'tmp', 'temp'}
            meaningful_words = [w for w in words if w.lower() not in noise_words and len(w) >= 3 and len(w) <= 15]

            if meaningful_words:
                # Prefer longer words as they're likely more meaningful
                meaningful_words.sort(key=len, reverse=True)
                return meaningful_words[0].capitalize()

        # If no meaningful words, try to extract a date
        date_match = self.date_pattern.search(name)
        if date_match:
            return date_match.group(0)

        # If nothing else works, use a generic group name
        return "Ungrouped"