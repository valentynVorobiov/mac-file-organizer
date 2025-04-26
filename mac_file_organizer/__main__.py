"""
Entry point for direct execution of the Mac File Organizer.
"""
import sys
import logging
import argparse

from mac_file_organizer.daemon import run_daemon
from mac_file_organizer.file_manager import FileManager
from mac_file_organizer.config import DEBUG

# Set up logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mac-file-organizer')


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description='Mac File Organizer - Automatically organize your Downloads and Desktop')
    parser.add_argument('--daemon', action='store_true', help='Run as a daemon')
    parser.add_argument('--once', action='store_true', help='Run organization once and exit')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    # Configure logging based on args
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        if args.daemon:
            logger.info("Starting in daemon mode")
            run_daemon()
        elif args.once:
            logger.info("Running organization once")
            file_manager = FileManager()
            file_manager.run_scan_cycle()
            logger.info("Organization completed")
        else:
            # By default, run in daemon mode
            logger.info("Starting in daemon mode (default)")
            run_daemon()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running Mac File Organizer: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
