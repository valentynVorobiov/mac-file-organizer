# Mac File Organizer

A Python daemon that automatically organizes files in your Downloads and Desktop folders on macOS.

## Features

- **Automatic Organization**: Files are grouped by category, extension, and then by similar names
- **Special Folders**: 
  - **Manual**: Files placed here will never be moved
  - **Review**: Files not accessed for 2+ weeks are moved here
- **Intelligent Grouping**: Files with similar names or dates are grouped together
- **Empty Folder Cleanup**: Removes empty folders after files are moved
- **Color-coded Tags**: Special folders are tagged for easy identification
- **Background Operation**: Runs silently as a macOS daemon

## Installation

### Prerequisites

- Python 3.8 or higher
- macOS
- Homebrew (for installing dependencies)

### Easy Install

```bash
# Clone the repository
git clone https://github.com/yourusername/mac-file-organizer.git
cd mac-file-organizer

# Run the installation script
bash scripts/install.sh
```

The script will:
1. Install the Python package
2. Install the 'tag' command line tool if needed
3. Create a symlink in /usr/local/bin
4. Install and load the LaunchAgent for automatic startup

### Manual Installation

```bash
# Install the Python package
pip3 install --user -e .

# Install the tag command-line tool
brew install tag

# Create a symlink
sudo ln -sf "$(which mac-file-organizer)" /usr/local/bin/mac-file-organizer
sudo chmod +x /usr/local/bin/mac-file-organizer

# Install the LaunchAgent
mkdir -p "$HOME/Library/LaunchAgents"
cp resources/com.user.mac-file-organizer.plist "$HOME/Library/LaunchAgents/"
sed -i '' "s#~/Library#$HOME/Library#g" "$HOME/Library/LaunchAgents/com.user.mac-file-organizer.plist"
launchctl load "$HOME/Library/LaunchAgents/com.user.mac-file-organizer.plist"
```

## Usage

Once installed, the daemon runs automatically in the background.

### Special Folders

The daemon creates these special folders in both Downloads and Desktop:

- **Manual**: Place files here that you don't want the daemon to move
- **Review**: Files not accessed for 2 weeks are moved here for review

### Running Manually

You can also run the organizer manually:

```bash
# Run once and exit
mac-file-organizer --once

# Run in daemon mode
mac-file-organizer --daemon

# Run with debug logging
mac-file-organizer --debug
```

## How It Works

1. **File Classification**: Files are first categorized by type (Documents, Images, etc.)
2. **Subcategorization**: Within each category, files are organized by extension (PDF, DOCX, etc.)
3. **Grouping**: Files with similar names or dates are grouped together
4. **Access Monitoring**: Files not accessed for 2 weeks are moved to Review
5. **Cleanup**: Empty folders are removed automatically

## Uninstallation

```bash
# Run the uninstallation script
bash scripts/uninstall.sh
```

## Customization

You can customize the file categories by editing `resources/file_categories.json`.

## Project Structure

```
mac-file-organizer/
│
├── mac_file_organizer/         # Main package
│   ├── __init__.py             # Package initialization
│   ├── __main__.py             # Entry point
│   ├── config.py               # Configuration settings
│   ├── daemon.py               # Daemon implementation
│   ├── file_manager.py         # Core file management logic
│   ├── file_classifier.py      # Logic for classifying files
│   ├── file_grouper.py         # Logic for grouping similar files
│   ├── file_monitor.py         # Monitoring file access times
│   ├── folder_cleaner.py       # Logic for removing empty folders
│   └── tag_manager.py          # Managing macOS file tags
│
├── resources/                  # Resources for the app
│   ├── com.user.mac-file-organizer.plist  # LaunchAgent plist
│   └── file_categories.json    # File category definitions
│
├── scripts/                    # Helper scripts
│   ├── install.sh              # Installation script
│   └── uninstall.sh            # Uninstallation script
│
└── tests/                      # Test suite
```

## License

MIT License
