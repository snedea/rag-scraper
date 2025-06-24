#!/bin/bash

# Exit on error
set -e

# --- Configuration ---
PYTHON_VENV_DIR="venv"
DATA_DIR="$HOME/.rag_scraper_data"
LOG_DIR="$HOME/.rag_scraper_logs"

# --- Functions ---
install_system_deps() {
    echo "--- Updating package list and installing system dependencies ---"
    apt-get update
    # Install Python
    apt-get install -y python3 python3-pip python3-venv
    # Install Node.js (for frontend)
    echo "--- Installing Node.js and npm ---"
    apt-get install -y ca-certificates curl gnupg
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
    NODE_MAJOR=20
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list
    apt-get update
    apt-get install -y nodejs
}

# --- Main Script ---

# Check if script is run with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo privileges to install system dependencies."
    echo "Example: sudo ./setup_debian.sh"
    echo ""
    echo "If you prefer not to use sudo, you can skip system dependencies and"
    echo "only create the virtual environment and install Python packages."
    echo "Would you like to continue without installing system dependencies? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "Skipping system dependency installation..."
    else
        exit 1
    fi
else
    install_system_deps
fi

# Create Python virtual environment
echo "--- Creating Python virtual environment in './${PYTHON_VENV_DIR}' ---"
python3 -m venv "${PYTHON_VENV_DIR}"

# Install Python dependencies into the virtual environment
echo "--- Installing Python dependencies from requirements.txt ---"
"${PYTHON_VENV_DIR}/bin/pip" install -r requirements.txt

# Create output directories in the user's home directory
echo "--- Creating data and log directories ---"
mkdir -p "${DATA_DIR}" "${LOG_DIR}"

# Set permissions to be writable by the user who ran sudo
if [ "$SUDO_USER" ]; then
    chown -R "$SUDO_USER":"$SUDO_USER" "${DATA_DIR}" "${LOG_DIR}" "${PYTHON_VENV_DIR}"
    # Also ensure the current project dir is owned by user, not root
    chown -R "$SUDO_USER":"$SUDO_USER" .
fi
chmod -R 775 "${DATA_DIR}" "${LOG_DIR}"

# Print success message
echo ""
echo "✅ Setup completed!"
echo ""
echo "To use the scraper:"
echo "1. Activate the virtual environment: source ${PYTHON_VENV_DIR}/bin/activate"
echo "2. Run the scraper: python3 rag_scraper.py --help"
echo ""
echo "To start the frontend (after running 'npm install' in the 'frontend' directory):"
echo "1. cd frontend"
echo "2. npm run dev"
echo ""
echo "For more details, see README.md"
