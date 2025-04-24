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
            'scan', 'export', 'import', 'temp', 'tmp', 'test', 'sample', 'demo'
        }

        # Date pattern for grouping date-based files
        self.date_pattern = re.compile(r'(20\d{2}[-_]?\d{2}[-_]?\d{2}|'  # YYYY-MM-DD, YYYY_MM_DD
                                       r'\d{2}[-_]?\d{2}[-_]?20\d{2}|'  # MM-DD-YYYY, MM_DD_YYYY
                                       r'\d{8}|'  # YYYYMMDD
                                       r'17\d{8})')  # Specific timestamp pattern seen in files

        # Similarity threshold for fuzzy matching
        self.similarity_threshold = 0.65

        # Minimum prefix length to consider for grouping
        self.min_prefix_length = 4

        # Regular expression for finding business/product names
        self.business_prefix_pattern = re.compile(r'^([A-Za-z0-9]+[-_.][A-Za-z0-9]+|[A-Za-z]{3,})')

        # Minimum file count to form a group automatically
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

        # 1. Check for existing groups with exact matches
        for group_dir in target_dir.iterdir():
            if not group_dir.is_dir():
                continue

            # Skip if group name is just a common word
            if group_dir.name.lower() in self.common_words:
                continue

            # Check if filename contains group name as a distinct word
            if (re.search(r'\b' + re.escape(group_dir.name.lower()) + r'\b',
                         stem.lower())):
                return group_dir.name

        # 2. Try to find a business/product prefix
        business_prefix = self._extract_business_prefix(stem)
        if business_prefix and len(business_prefix) >= self.min_prefix_length:
            # Check if a group with this prefix already exists
            for group_dir in target_dir.iterdir():
                if not group_dir.is_dir():
                    continue

                # Similar prefix (case-insensitive)
                if (group_dir.name.lower().startswith(business_prefix.lower()) or
                    business_prefix.lower().startswith(group_dir.name.lower())):
                    return group_dir.name

            # No existing group found, suggest a new one if prefix is meaningful
            if business_prefix.lower() not in self.common_words:
                return business_prefix.capitalize()

        # 3. Check for date-based grouping
        date_match = self.date_pattern.search(stem)
        if date_match:
            date_str = date_match.group(0)
            # Format date more intuitively if it's a full timestamp
            if len(date_str) > 8:  # It's a detailed timestamp
                # Extract a more meaningful date format (e.g., YYYY-MM-DD)
                if date_str.startswith('17'):  # Special timestamp format
                    formatted_date = f"Date-{date_str[:10]}"
                else:
                    # Standard date format
                    formatted_date = f"Date-{date_str[:10]}"
                return formatted_date
            return f"Date-{date_str}"

        # 4. Use fuzzy matching for similar filenames
        best_match = None
        highest_similarity = 0

        for group_dir in target_dir.iterdir():
            if not group_dir.is_dir():
                continue

            # Check similarity with existing files in the group
            for existing_file in group_dir.iterdir():
                if not existing_file.is_file():
                    continue

                similarity = self._calculate_name_similarity(stem, existing_file.stem)
                if similarity > highest_similarity and similarity >= self.similarity_threshold:
                    highest_similarity = similarity
                    best_match = group_dir.name

        if best_match:
            return best_match

        # 5. No suitable group found
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

        # Similar logic as find_group_for_file but adapted for folders

        # 1. Check for existing groups with exact matches
        for group_dir in target_dir.iterdir():
            if not group_dir.is_dir():
                continue

            # Skip if group name is just a common word
            if group_dir.name.lower() in self.common_words:
                continue

            # Check if folder name contains group name as a distinct word
            if (re.search(r'\b' + re.escape(group_dir.name.lower()) + r'\b',
                         folder_name.lower())):
                return group_dir.name

        # 2. Try to find a business/product prefix
        business_prefix = self._extract_business_prefix(folder_name)
        if business_prefix and len(business_prefix) >= self.min_prefix_length:
            # Check if a group with this prefix already exists
            for group_dir in target_dir.iterdir():
                if not group_dir.is_dir():
                    continue

                # Similar prefix (case-insensitive)
                if (group_dir.name.lower().startswith(business_prefix.lower()) or
                    business_prefix.lower().startswith(group_dir.name.lower())):
                    return group_dir.name

            # No existing group found, suggest a new one if prefix is meaningful
            if business_prefix.lower() not in self.common_words:
                return business_prefix.capitalize()

        # 3. Check for date-based grouping
        date_match = self.date_pattern.search(folder_name)
        if date_match:
            date_str = date_match.group(0)
            # Format date more intuitively
            if len(date_str) > 8:  # It's a detailed timestamp
                formatted_date = f"Date-{date_str[:10]}"
            else:
                formatted_date = f"Date-{date_str}"
            return formatted_date

        # 4. Use fuzzy matching for similar folder names
        best_match = None
        highest_similarity = 0

        for group_dir in target_dir.iterdir():
            if not group_dir.is_dir():
                continue

            # Check if this is a meaningful group name (not just a common word)
            if group_dir.name.lower() in self.common_words:
                continue

            # Check similarity with existing folder names in the group
            for existing_folder in group_dir.iterdir():
                if not existing_folder.is_dir():
                    continue

                similarity = self._calculate_name_similarity(folder_name, existing_folder.name)
                if similarity > highest_similarity and similarity >= self.similarity_threshold:
                    highest_similarity = similarity
                    best_match = group_dir.name

        if best_match:
            return best_match

        # 5. No suitable group found
        return "Ungrouped"

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