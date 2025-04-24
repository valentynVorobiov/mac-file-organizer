#!/bin/bash
set -e

echo "Installing Mac File Organizer..."

# Navigate to the project directory
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

# Create and activate a virtual environment
echo "Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Build and install the Python package
echo "Installing Python package..."
pip install -e .

# Install 'tag' command line tool if not already installed
if ! command -v tag &> /dev/null; then
    echo "Installing 'tag' command line tool..."
    if command -v brew &> /dev/null; then
        brew install tag
    else
        echo "Error: Homebrew not found. Please install Homebrew first:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
fi

# Verify tag installation
if ! command -v tag &> /dev/null; then
    echo "Warning: 'tag' command could not be installed. File tagging may not work correctly."
    echo "You may need to install it manually later with 'brew install tag'"
fi

# Create a symlink for the executable
EXEC_PATH="$PROJECT_ROOT/.venv/bin/mac-file-organizer"
if [ ! -f "$EXEC_PATH" ]; then
    echo "Error: Could not find mac-file-organizer executable"
    exit 1
fi

# Create /usr/local/bin if it doesn't exist
if [ ! -d "/usr/local/bin" ]; then
    sudo mkdir -p /usr/local/bin
fi

sudo ln -sf "$EXEC_PATH" /usr/local/bin/mac-file-organizer
sudo chmod +x /usr/local/bin/mac-file-organizer

# Create a wrapper script with ABSOLUTE paths (fixing the main issue)
WRAPPER_PATH="/usr/local/bin/mac-file-organizer-wrapper"
cat > /tmp/mac-file-organizer-wrapper << EOF
#!/bin/bash
# Wrapper script to activate the virtual environment before running mac-file-organizer
# Using absolute paths to avoid path resolution issues
source "$PROJECT_ROOT/.venv/bin/activate"
"$PROJECT_ROOT/.venv/bin/mac-file-organizer" "\$@"
EOF

sudo mv /tmp/mac-file-organizer-wrapper "$WRAPPER_PATH"
sudo chmod +x "$WRAPPER_PATH"

# Install the LaunchAgent
PLIST_SRC="$PROJECT_ROOT/resources/com.user.mac-file-organizer.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.user.mac-file-organizer.plist"

# Copy the plist file
mkdir -p "$HOME/Library/LaunchAgents"
cp "$PLIST_SRC" "$PLIST_DEST"

# Expand the ~ in the plist file paths and update to use the wrapper
sed -i '' "s#~/Library#$HOME/Library#g" "$PLIST_DEST"
sed -i '' "s#/usr/local/bin/mac-file-organizer#$WRAPPER_PATH#g" "$PLIST_DEST"

# Ensure log directories exist
mkdir -p "$HOME/Library/Logs"

# Unload first if already loaded
if launchctl list | grep -q "com.user.mac-file-organizer"; then
    launchctl unload "$PLIST_DEST"
fi

# Load the LaunchAgent
launchctl load "$PLIST_DEST"

echo "Mac File Organizer has been installed and started!"
echo "It will automatically organize files in your Downloads and Desktop folders."
echo ""
echo "Special folders created:"
echo "  - ~/Downloads/Manual (files here will never be moved)"
echo "  - ~/Downloads/Review (files not accessed for 2 weeks)"
echo "  - ~/Desktop/Manual"
echo "  - ~/Desktop/Review"