"""
Daemon implementation for running as a background service.
"""
import time
import logging
import signal
import sys
from pathlib import Path

from mac_file_organizer.config import SCAN_INTERVAL
from mac_file_organizer.file_manager import FileManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / 'Library' / 'Logs' / 'mac-file-organizer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('mac-file-organizer')

# Global flag for graceful shutdown
running = True


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    global running
    logger.info(f"Received signal {sig}, shutting down...")
    running = False


def run_daemon():
    """Run the file organizer daemon."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting Mac File Organizer daemon...")

    # Initialize file manager
    file_manager = FileManager()

    # Main daemon loop
    while running:
        try:
            logger.info("Running scan cycle...")
            file_manager.run_scan_cycle()
            logger.info("Scan cycle completed.")

            # Sleep until next cycle, but check for termination regularly
            for _ in range(SCAN_INTERVAL):
                if not running:
                    break
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error in scan cycle: {e}", exc_info=True)
            # Sleep before retry
            time.sleep(60)

    logger.info("Mac File Organizer daemon stopped.")


if __name__ == "__main__":
    run_daemon()