#!/bin/bash
set -e

echo "Uninstalling Mac File Organizer..."

# Unload the LaunchAgent
if launchctl list | grep -q "com.user.mac-file-organizer"; then
    launchctl unload "$HOME/Library/LaunchAgents/com.user.mac-file-organizer.plist"
    echo "LaunchAgent unloaded"
fi

# Remove the LaunchAgent plist
if [ -f "$HOME/Library/LaunchAgents/com.user.mac-file-organizer.plist" ]; then
    rm -f "$HOME/Library/LaunchAgents/com.user.mac-file-organizer.plist"
    echo "LaunchAgent plist removed"
fi

# Remove the symlink
if [ -L "/usr/local/bin/mac-file-organizer" ]; then
    sudo rm -f /usr/local/bin/mac-file-organizer
    echo "Symlink removed"
fi

# Uninstall the Python package
pip3 uninstall -y mac-file-organizer
echo "Python package uninstalled"

echo ""
echo "Mac File Organizer has been uninstalled."
echo "Note: The organized folders and files in your Downloads and Desktop remain untouched."
echo "If you want to remove the special folders (Manual, Review), you'll need to do that manually."