"""
Managing macOS file tags.
"""
import logging
import subprocess
# from pathlib import Path

from mac_file_organizer.config import MANUAL_TAG_COLOR, REVIEW_TAG_COLOR

logger = logging.getLogger('mac-file-organizer')

class TagManager:
    """Manages macOS file tags."""

    def __init__(self):
        """Initialize the tag manager."""
        # Check if tag command is available
        self._check_tag_command()

    def _check_tag_command(self):
        """Check if 'tag' command-line tool is available."""
        try:
            subprocess.run(["tag", "--version"], capture_output=True, check=True)
            self.tag_command_available = True
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("'tag' command not found. File tagging will be disabled.")
            logger.warning("Install with: brew install tag")
            self.tag_command_available = False

    def apply_tag(self, path, tag_name):
        """Apply a tag to a file or folder using macOS tag system."""
        if not self.tag_command_available:
            logger.warning(f"Tag command not available, cannot tag {path}")
            return

        path_str = str(path)

        try:
            # Determine tag color based on tag name
            tag_color = MANUAL_TAG_COLOR if tag_name == "Manual" else REVIEW_TAG_COLOR

            # First remove any existing tag with this name to ensure we apply the correct color
            try:
                subprocess.run(
                    ["tag", "-r", tag_name, path_str],
                    capture_output=True,
                    check=False  # Don't fail if tag doesn't exist
                )
            except Exception:
                pass

            # Apply the tag with color
            subprocess.run(
                ["tag", "-a", f"{tag_name},{tag_color}", path_str],
                check=True
            )

            logger.info(f"Applied tag '{tag_name}' ({tag_color}) to {path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error applying tag to {path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error applying tag to {path}: {e}")

    def remove_tag(self, path, tag_name):
        """Remove a tag from a file or folder."""
        if not self.tag_command_available:
            return

        path_str = str(path)

        try:
            subprocess.run(
                ["tag", "-r", tag_name, path_str],
                check=True
            )
            logger.info(f"Removed tag '{tag_name}' from {path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error removing tag from {path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error removing tag from {path}: {e}")