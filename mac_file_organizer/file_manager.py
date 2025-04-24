"""
Core file management logic.
"""
import os
import logging
import time
import itertools
import re  # Added missing import
import shutil  # Added import for handling app bundles
from pathlib import Path
from collections import defaultdict

from mac_file_organizer.config import (
    DOWNLOADS_DIR, DESKTOP_DIR,
    MANUAL_FOLDER_NAME, REVIEW_FOLDER_NAME,
    MANUAL_TAG, REVIEW_TAG
)
from mac_file_organizer.file_classifier import FileClassifier
from mac_file_organizer.file_grouper import FileGrouper
from mac_file_organizer.file_monitor import FileMonitor
from mac_file_organizer.folder_cleaner import FolderCleaner
from mac_file_organizer.tag_manager import TagManager

logger = logging.getLogger('mac-file-organizer')


class FileManager:
    """Main class for managing file organization."""

    def __init__(self):
        """Initialize file manager components."""
        self.classifier = FileClassifier()
        self.grouper = FileGrouper()
        self.monitor = FileMonitor()
        self.cleaner = FolderCleaner()
        self.tag_manager = TagManager()

        # Ensure special folders exist and are tagged
        self._initialize_special_folders()

    def _initialize_special_folders(self):
        """Create and tag special folders if they don't exist."""
        for directory in [DOWNLOADS_DIR, DESKTOP_DIR]:
            manual_dir = directory / MANUAL_FOLDER_NAME
            review_dir = directory / REVIEW_FOLDER_NAME

            # Create Manual folder if it doesn't exist
            if not manual_dir.exists():
                manual_dir.mkdir(exist_ok=True)
                logger.info(f"Created Manual folder at {manual_dir}")

            # Create Review folder if it doesn't exist
            if not review_dir.exists():
                review_dir.mkdir(exist_ok=True)
                logger.info(f"Created Review folder at {review_dir}")

            # Apply tags
            self.tag_manager.apply_tag(manual_dir, MANUAL_TAG)
            self.tag_manager.apply_tag(review_dir, REVIEW_TAG)

    def run_scan_cycle(self):
        """Run a complete scan and organization cycle."""
        # Process Downloads folder
        self._process_directory(DOWNLOADS_DIR)

        # Process Desktop folder
        self._process_directory(DESKTOP_DIR)

        # Smart grouping phase - identify prefixes and group by business/product
        self._smart_grouping(DOWNLOADS_DIR)
        self._smart_grouping(DESKTOP_DIR)

        # Move old files to Review folders
        self._move_to_review()

        # Clean up empty folders
        self._clean_empty_folders()

    def _process_directory(self, directory):
        """Process all files in the given directory."""
        logger.info(f"Processing directory: {directory}")

        # Skip special folders
        special_folders = [MANUAL_FOLDER_NAME, REVIEW_FOLDER_NAME]

        for item in directory.iterdir():
            # Skip special folders and hidden files
            if (item.name in special_folders or
                    item.name.startswith('.')):
                continue

            # Skip directories that are in our category structure
            if item.is_dir() and any(item.name == cat for cat in self.classifier.get_categories()):
                continue

            # Process the item
            try:
                if item.is_file():
                    self._process_file(item, directory)
                elif item.is_dir():
                    self._process_folder(item, directory)
            except Exception as e:
                logger.error(f"Error processing {item}: {e}", exc_info=True)

    def _process_file(self, file_path, base_dir):
        """Process a single file."""
        logger.info(f"Processing file: {file_path}")

        # Get category for this file
        category = self.classifier.classify_file(file_path)

        # Create category folder if it doesn't exist
        category_dir = base_dir / category
        category_dir.mkdir(exist_ok=True)

        # Get subcategory based on file extension
        extension = file_path.suffix.lstrip('.').upper()
        if not extension:
            extension = "Other"

        # Create extension folder if it doesn't exist
        extension_dir = category_dir / extension
        extension_dir.mkdir(exist_ok=True)

        # Find group for this file
        group = self.grouper.find_group_for_file(file_path, extension_dir)

        if group == "Ungrouped":
            # Place the file directly in the extension directory
            target_path = extension_dir / file_path.name
        else:
            # Create group folder if it doesn't exist
            group_dir = extension_dir / group
            group_dir.mkdir(exist_ok=True)
            target_path = group_dir / file_path.name

        # Handle name conflicts
        if target_path.exists():
            base_name = file_path.stem
            extension = file_path.suffix
            counter = 1
            while target_path.exists():
                new_name = f"{base_name}_{counter}{extension}"
                if group == "Ungrouped":
                    target_path = extension_dir / new_name
                else:
                    target_path = group_dir / new_name
                counter += 1

        # Move the file
        file_path.rename(target_path)
        logger.info(f"Moved {file_path} to {target_path}")

    def _process_folder(self, folder_path, base_dir):
        """Process a folder as a single entity."""
        logger.info(f"Processing folder: {folder_path}")

        # Folders go to a dedicated 'Folders' category
        folders_dir = base_dir / "Folders"
        folders_dir.mkdir(exist_ok=True)

        # Find group for this folder
        group = self.grouper.find_group_for_folder(folder_path, folders_dir)

        if group == "Ungrouped":
            # Place the folder directly in the Folders directory
            target_path = folders_dir / folder_path.name
        else:
            # Create group folder if it doesn't exist
            group_dir = folders_dir / group
            group_dir.mkdir(exist_ok=True)
            target_path = group_dir / folder_path.name

        # Handle name conflicts
        if target_path.exists():
            base_name = folder_path.name
            counter = 1
            while target_path.exists():
                new_name = f"{base_name}_{counter}"
                if group == "Ungrouped":
                    target_path = folders_dir / new_name
                else:
                    target_path = group_dir / new_name
                counter += 1

        # Move the folder
        folder_path.rename(target_path)
        logger.info(f"Moved {folder_path} to {target_path}")

    def _smart_grouping(self, directory):
        """Intelligently group files based on business/product prefixes and patterns."""
        logger.info(f"Running smart grouping in: {directory}")

        # Process each category directory
        for category_dir in directory.iterdir():
            if not category_dir.is_dir() or category_dir.name in [MANUAL_FOLDER_NAME, REVIEW_FOLDER_NAME]:
                continue

            # Process each extension directory
            for extension_dir in category_dir.iterdir():
                if not extension_dir.is_dir():
                    continue

                # Find all ungrouped files (directly in the extension directory)
                ungrouped_files = [f for f in extension_dir.iterdir() if f.is_file()]

                if len(ungrouped_files) < self.grouper.min_files_for_group:
                    continue

                # First analysis - identify potential groups
                potential_groups = self._identify_potential_groups(ungrouped_files)

                # Only create groups with multiple files
                for group_name, group_files in potential_groups.items():
                    if len(group_files) >= self.grouper.min_files_for_group:
                        # Create group folder
                        group_dir = extension_dir / group_name
                        group_dir.mkdir(exist_ok=True)

                        # Move files to group
                        for file_path in group_files:
                            if file_path.exists():  # It might have been moved already
                                target_path = group_dir / file_path.name

                                # Handle name conflicts
                                if target_path.exists() and target_path != file_path:
                                    base_name = file_path.stem
                                    extension = file_path.suffix
                                    counter = 1
                                    while target_path.exists() and target_path != file_path:
                                        new_name = f"{base_name}_{counter}{extension}"
                                        target_path = group_dir / new_name
                                        counter += 1

                                try:
                                    file_path.rename(target_path)
                                    logger.info(f"Grouped file {file_path} into {group_name}")
                                except Exception as e:
                                    logger.error(f"Error moving file {file_path} to group {group_name}: {e}")

    def _identify_potential_groups(self, files):
        """
        Identify potential groups among a set of files.

        Args:
            files (list): List of file paths

        Returns:
            dict: Mapping of group names to lists of files
        """
        # Dictionary to track potential groups
        potential_groups = defaultdict(list)

        # First pass - look for obvious prefix groups
        for file_path in files:
            # Skip files that don't exist (might have been moved already)
            if not file_path.exists():
                continue

            stem = file_path.stem

            # Try to extract a meaningful prefix
            prefix = self.grouper._extract_business_prefix(stem)
            if prefix and len(prefix) >= self.grouper.min_prefix_length:
                # Standardize prefix format
                group_name = prefix.capitalize()
                potential_groups[group_name].append(file_path)

        # Second pass - look for similar files
        # We'll only do this for files not already grouped
        already_grouped = set()
        for group_files in potential_groups.values():
            already_grouped.update(group_files)

        remaining_files = [f for f in files if f not in already_grouped and f.exists()]

        # Compare files in pairs
        for i, file1 in enumerate(remaining_files):
            for file2 in remaining_files[i + 1:]:
                # Skip if either file was already processed
                if file1 in already_grouped or file2 in already_grouped:
                    continue

                # Compare names with high similarity threshold
                similarity = self.grouper._calculate_name_similarity(file1.stem, file2.stem)

                if similarity >= self.grouper.similarity_threshold:
                    # Find a meaningful group name
                    group_name = self._find_meaningful_group_name(file1, file2)

                    if group_name != "Ungrouped":
                        if file1 not in potential_groups[group_name]:
                            potential_groups[group_name].append(file1)
                            already_grouped.add(file1)
                        if file2 not in potential_groups[group_name]:
                            potential_groups[group_name].append(file2)
                            already_grouped.add(file2)

        # Remove any groups that don't have enough files
        return {k: v for k, v in potential_groups.items() if len(v) >= self.grouper.min_files_for_group}

    def _find_meaningful_group_name(self, file1, file2):
        """
        Find a meaningful group name for two similar files.

        Args:
            file1 (Path): First file
            file2 (Path): Second file

        Returns:
            str: A meaningful group name or "Ungrouped"
        """
        stem1 = file1.stem
        stem2 = file2.stem

        # Find common prefix
        i = 0
        while i < min(len(stem1), len(stem2)) and stem1[i].lower() == stem2[i].lower():
            i += 1

        common_prefix = stem1[:i].strip('- _').capitalize()
        if len(common_prefix) >= self.grouper.min_prefix_length:
            # Check if this is just a common word
            if common_prefix.lower() not in self.grouper.common_words:
                return common_prefix

        # Find common substrings
        common_words = set()
        words1 = re.findall(r'\b[A-Za-z]{3,}\b', stem1.lower())
        words2 = re.findall(r'\b[A-Za-z]{3,}\b', stem2.lower())

        for word in words1:
            if word in words2 and word not in self.grouper.common_words:
                common_words.add(word.capitalize())

        if common_words:
            return next(iter(common_words))

        # Try to extract a business/product name
        prefix1 = self.grouper._extract_business_prefix(stem1)
        prefix2 = self.grouper._extract_business_prefix(stem2)

        if prefix1 and prefix1 == prefix2:
            return prefix1.capitalize()

        # If no good name found, return "Ungrouped"
        return "Ungrouped"

    def _group_by_prefixes(self, files, extension_dir):
        """Group files by their business/vendor prefixes."""
        # Group files by prefix
        prefix_groups = defaultdict(list)

        for file_path in files:
            prefix = self.grouper._extract_business_prefix(file_path.stem)
            if prefix:
                prefix_groups[prefix.lower()].append(file_path)

        # Create folders for prefix groups with multiple files
        for prefix, group_files in prefix_groups.items():
            # Only create a group if there are AT LEAST 2 FILES
            if len(group_files) >= self.grouper.min_files_for_group:
                # Create a folder with the prefix name
                group_dir = extension_dir / prefix.capitalize()
                group_dir.mkdir(exist_ok=True)

                # Move files to the group folder
                for file_path in group_files:
                    if file_path.exists():  # It might have been moved already
                        target_path = group_dir / file_path.name

                        # Handle name conflicts
                        if target_path.exists() and target_path != file_path:
                            base_name = file_path.stem
                            extension = file_path.suffix
                            counter = 1
                            while target_path.exists() and target_path != file_path:
                                new_name = f"{base_name}_{counter}{extension}"
                                target_path = group_dir / new_name
                                counter += 1

                        try:
                            file_path.rename(target_path)
                            logger.info(f"Grouped file {file_path} into {prefix} group")
                        except Exception as e:
                            logger.error(f"Error moving file {file_path} to group {prefix}: {e}")

    def _group_by_date_patterns(self, files, extension_dir):
        """Group files by common date patterns in their names."""
        # Dictionary to track date-based groups
        date_groups = defaultdict(list)

        # Find files with the same date
        for file_path in files:
            date_match = self.grouper.date_pattern.search(file_path.stem)
            if date_match:
                date_value = date_match.group(0)
                date_groups[date_value].append(file_path)

        # Process date groups with multiple files
        for date_value, group_files in date_groups.items():
            # Only create a group if there are AT LEAST 2 FILES
            if len(group_files) >= self.grouper.min_files_for_group:
                # Check if these files also have common prefixes
                prefixes = [self.grouper._extract_business_prefix(f.stem) for f in group_files]
                prefixes = [p for p in prefixes if p]

                # If they have different prefixes, don't group them just because of the date
                if len(set(prefixes)) > 1:
                    continue

                # Create a date-based group
                group_dir = extension_dir / f"Date-{date_value}"
                group_dir.mkdir(exist_ok=True)

                # Move files to the group folder
                for file_path in group_files:
                    if file_path.exists():  # It might have been moved already
                        target_path = group_dir / file_path.name

                        # Handle name conflicts
                        if target_path.exists() and target_path != file_path:
                            base_name = file_path.stem
                            extension = file_path.suffix
                            counter = 1
                            while target_path.exists() and target_path != file_path:
                                new_name = f"{base_name}_{counter}{extension}"
                                target_path = group_dir / new_name
                                counter += 1

                        try:
                            file_path.rename(target_path)
                            logger.info(f"Grouped file {file_path} into date group Date-{date_value}")
                        except Exception as e:
                            logger.error(f"Error moving file {file_path} to date group Date-{date_value}: {e}")

    def _group_similar_files(self, files, extension_dir):
        """Group similar files based on name similarity."""
        # Dictionary to track groups
        potential_groups = {}

        # Compare files in pairs
        for i, file1 in enumerate(files):
            for file2 in files[i + 1:]:
                # Skip if either file was already processed and no longer exists
                if not file1.exists() or not file2.exists():
                    continue

                # Compare names
                similarity = self.grouper._calculate_name_similarity(file1.stem, file2.stem)

                if similarity >= self.grouper.similarity_threshold:
                    # Extract a meaningful group name
                    group_name = self.grouper._extract_group_name(file1.stem)

                    if group_name != "Ungrouped" and group_name not in potential_groups:
                        potential_groups[group_name] = []

                    # Add both files if they're not already in the group
                    if group_name != "Ungrouped":
                        if file1 not in potential_groups[group_name]:
                            potential_groups[group_name].append(file1)
                        if file2 not in potential_groups[group_name]:
                            potential_groups[group_name].append(file2)

        # Create groups
        for group_name, group_files in potential_groups.items():
            # Only create a group if there are AT LEAST 2 FILES
            if len(group_files) >= self.grouper.min_files_for_group:
                # Create the group folder
                group_dir = extension_dir / group_name
                group_dir.mkdir(exist_ok=True)

                # Move the files to the group folder
                for file_path in group_files:
                    if file_path.exists():  # It might have been moved already
                        target_path = group_dir / file_path.name

                        # Handle name conflicts
                        if target_path.exists() and target_path != file_path:
                            base_name = file_path.stem
                            extension = file_path.suffix
                            counter = 1
                            while target_path.exists() and target_path != file_path:
                                new_name = f"{base_name}_{counter}{extension}"
                                target_path = group_dir / new_name
                                counter += 1

                        try:
                            file_path.rename(target_path)
                            logger.info(f"Grouped file {file_path} into {group_name}")
                        except Exception as e:
                            logger.error(f"Error moving file {file_path} to group {group_name}: {e}")

    def _move_to_review(self):
        """Move files not accessed for over 2 weeks to Review folder."""
        logger.info("Checking for old files to move to Review...")

        for base_dir in [DOWNLOADS_DIR, DESKTOP_DIR]:
            review_dir = base_dir / REVIEW_FOLDER_NAME

            # Get list of old files
            old_files = self.monitor.get_old_files(base_dir)

            # Move each old file to Review
            for file_path in old_files:
                # Skip special folders
                if (file_path.parent.name == MANUAL_FOLDER_NAME or
                        file_path.parent.name == REVIEW_FOLDER_NAME):
                    continue

                target_path = review_dir / file_path.name

                # Handle name conflicts
                if target_path.exists():
                    base_name = file_path.stem if file_path.is_file() else file_path.name
                    extension = file_path.suffix if file_path.is_file() else ""
                    counter = 1
                    while target_path.exists():
                        if file_path.is_file():
                            new_name = f"{base_name}_{counter}{extension}"
                        else:
                            new_name = f"{base_name}_{counter}"
                        target_path = review_dir / new_name
                        counter += 1

                try:
                    # Special handling for .app directories
                    if file_path.is_dir() and str(file_path).endswith('.app'):
                        # Use shutil for app bundles
                        shutil.copytree(file_path, target_path, symlinks=True)
                        shutil.rmtree(file_path)
                        logger.info(f"Moved application bundle {file_path} to Review: {target_path}")
                    else:
                        # Move the file or folder using regular rename
                        file_path.rename(target_path)
                        logger.info(f"Moved {file_path} to Review: {target_path}")
                except Exception as e:
                    logger.error(f"Error moving {file_path} to Review: {e}")

    def _clean_empty_folders(self):
        """Clean up empty folders."""
        logger.info("Cleaning empty folders...")

        for base_dir in [DOWNLOADS_DIR, DESKTOP_DIR]:
            self.cleaner.clean_empty_folders(base_dir)