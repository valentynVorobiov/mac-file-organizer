"""
Group related files based on naming patterns.
"""
import os
import re
import logging
import difflib
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger('mac-file-organizer')


class FileGrouper:
    """Group files based on common patterns and prefixes."""

    def __init__(self):
        """Initialize the file grouper with patterns and thresholds."""
        # Common words that should NOT be used for grouping by themselves
        self.common_words = {
            'active', 'new', 'copy', 'backup', 'final', 'draft', 'old', 'image',
            'file', 'document', 'untitled', 'screenshot', 'photo', 'picture',
            'scan', 'export', 'import', 'temp', 'tmp', 'test', 'sample', 'demo',
            'menu', 'icon', 'button', 'tile', 'list', 'item', 'header', 'footer',
            'sidebar', 'navbar', 'panel', 'tab', 'background', 'logo', 'banner'
        }

        # Date pattern for grouping date-based files
        self.date_pattern = re.compile(r'(20\d{2}[-_]?\d{2}[-_]?\d{2}|'  # YYYY-MM-DD, YYYY_MM_DD
                                       r'\d{2}[-_]?\d{2}[-_]?20\d{2}|'  # MM-DD-YYYY, MM_DD_YYYY
                                       r'\d{8}|'  # YYYYMMDD
                                       r'17\d{8})')  # Specific timestamp pattern seen in files

        # Higher similarity threshold for fuzzy matching to avoid false positives
        self.similarity_threshold = 0.8

        # Minimum prefix length to consider for grouping
        self.min_prefix_length = 4

        # Regular expression for finding business/product names
        self.business_prefix_pattern = re.compile(r'^([A-Za-z0-9]+[-_.][A-Za-z0-9]+|[A-Za-z]{3,})')

        # Strict minimum file count to form a group
        self.min_files_for_group = 2

    def find_group_for_file(self, file_path, target_dir):
        """
        Find the most appropriate group for a file.

        Args:
            file_path (Path): Path to the file
            target_dir (Path): Directory where groups are located

        Returns:
            str: Group name or "Ungrouped" if no suitable group is found
        """
        # Extract filename components
        filename = file_path.name
        stem = file_path.stem
        extension = file_path.suffix.lower()

        # Only check for existing groups - never suggest new ones
        for group_dir in target_dir.iterdir():
            if not group_dir.is_dir():
                continue

            # Skip if group name is just a common word
            if group_dir.name.lower() in self.common_words:
                continue

            # Only add to existing group if there's a STRONG match
            if self._is_strong_match(stem, group_dir.name):
                # Check if the group has at least one file already
                file_count = sum(1 for _ in group_dir.iterdir() if _.is_file())
                if file_count > 0:
                    return group_dir.name

        # No suitable existing group found
        return "Ungrouped"

    def find_group_for_folder(self, folder_path, target_dir):
        """
        Find the most appropriate group for a folder.

        Args:
            folder_path (Path): Path to the folder
            target_dir (Path): Directory where groups are located

        Returns:
            str: Group name or "Ungrouped" if no suitable group is found
        """
        # Extract folder name
        folder_name = folder_path.name

        # Only check for existing groups - never suggest new ones
        for group_dir in target_dir.iterdir():
            if not group_dir.is_dir():
                continue

            # Skip if group name is just a common word
            if group_dir.name.lower() in self.common_words:
                continue

            # Only add to existing group if there's a STRONG match
            if self._is_strong_match(folder_name, group_dir.name):
                # Check if the group has at least one subfolder already
                subfolder_count = sum(1 for _ in group_dir.iterdir() if _.is_dir())
                if subfolder_count > 0:
                    return group_dir.name

        # No suitable group found
        return "Ungrouped"

    def _is_strong_match(self, name, group_name):
        """
        Determine if a file/folder name strongly matches a group name.

        Args:
            name (str): File or folder name
            group_name (str): Group name to compare against

        Returns:
            bool: True if there's a strong match, False otherwise
        """
        # Convert to lowercase for case-insensitive comparison
        name_lower = name.lower()
        group_lower = group_name.lower()

        # 1. Exact name match (case-insensitive)
        if name_lower == group_lower:
            return True

        # 2. Strong prefix match (e.g., "document-1" matches group "Document")
        if (name_lower.startswith(group_lower + '-') or
            name_lower.startswith(group_lower + '_')):
            return True

        # 3. Strong suffix match (e.g., "old-document" matches group "Document")
        if name_lower.endswith('-' + group_lower) or name_lower.endswith('_' + group_lower):
            return True

        # 4. Complete word match within name (with word boundaries)
        if re.search(r'\b' + re.escape(group_lower) + r'\b', name_lower):
            # Verify this isn't just matching a common word
            if group_lower not in self.common_words:
                return True

        # No strong match found
        return False

    def _extract_business_prefix(self, name):
        """
        Extract a likely business or product prefix from a filename.

        Args:
            name (str): Filename to analyze

        Returns:
            str: Extracted prefix or empty string if none found
        """
        # Remove any numeric prefixes or date prefixes
        clean_name = re.sub(r'^\d+[-_ ]', '', name)
        clean_name = re.sub(r'^20\d{2}[-_]\d{2}[-_]\d{2}[-_ ]', '', clean_name)

        # Try to extract a business/product prefix
        match = self.business_prefix_pattern.search(clean_name)
        if match:
            prefix = match.group(1)
            # Don't use common words as prefixes
            if prefix.lower() in self.common_words:
                return ""
            return prefix
        return ""

    def _calculate_name_similarity(self, name1, name2):
        """
        Calculate similarity between two filenames.

        Args:
            name1 (str): First filename
            name2 (str): Second filename

        Returns:
            float: Similarity score between 0 and 1
        """
        # Clean up names for comparison
        clean1 = self._clean_name_for_comparison(name1)
        clean2 = self._clean_name_for_comparison(name2)

        # Calculate similarity ratio
        similarity = difflib.SequenceMatcher(None, clean1, clean2).ratio()

        # Boost similarity for names with common prefixes or common words
        words1 = set(re.findall(r'\b\w{3,}\b', clean1.lower()))
        words2 = set(re.findall(r'\b\w{3,}\b', clean2.lower()))

        common_words = words1.intersection(words2)

        # Don't boost similarity based on very common words
        meaningful_common_words = common_words - self.common_words

        if meaningful_common_words:
            boost = min(0.2, 0.05 * len(meaningful_common_words))
            similarity += boost

        return min(1.0, similarity)

    def _clean_name_for_comparison(self, name):
        """
        Clean up filename for comparison by removing common suffixes and patterns.

        Args:
            name (str): Filename to clean

        Returns:
            str: Cleaned filename
        """
        # Remove numbers in parentheses like " (1)", " (2)", etc.
        cleaned = re.sub(r' \(\d+\)', '', name)

        # Remove version suffixes like "v1", "v2.1", etc.
        cleaned = re.sub(r' v\d+(\.\d+)?', '', cleaned)

        # Remove date patterns
        cleaned = re.sub(r'20\d{2}[-_]\d{2}[-_]\d{2}', '', cleaned)

        # Remove common modifiers
        for modifier in [' - Copy', ' copy', ' final', ' draft', ' new']:
            cleaned = cleaned.replace(modifier, '')

        return cleaned

    def _extract_group_name(self, filename):
        """
        Extract a meaningful group name from a filename.

        Args:
            filename (str): Filename to analyze

        Returns:
            str: Suggested group name or "Ungrouped" if none found
        """
        # Try to extract a business/product name first
        business_prefix = self._extract_business_prefix(filename)
        if business_prefix and len(business_prefix) >= self.min_prefix_length and business_prefix.lower() not in self.common_words:
            return business_prefix.capitalize()

        # Try to extract a meaningful word (at least 4 letters, not a common word)
        words = re.findall(r'\b[A-Za-z]{4,}\b', filename)
        for word in words:
            if word.lower() not in self.common_words:
                return word.capitalize()

        # Check for hyphenated words or camelCase that could be meaningful
        hyphenated = re.search(r'([A-Za-z]{3,})[-_]([A-Za-z]{3,})', filename)
        if hyphenated:
            compound = f"{hyphenated.group(1)}-{hyphenated.group(2)}"
            if compound.lower() not in self.common_words:
                return compound.capitalize()

        # Check for CamelCase
        camel_case = re.search(r'([A-Z][a-z]{2,})([A-Z][a-z]{2,})', filename)
        if camel_case:
            return camel_case.group(0)

        # If all else fails, return "Ungrouped"
        return "Ungrouped"
