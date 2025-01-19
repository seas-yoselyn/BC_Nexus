# Initialize and update all submodules recursively
echo "Initializing and updating submodules..."
git submodule update --init --recursive

# Navigate to the Linking_tool submodule and install it
if [ -f setup.py ]; then
    echo "Installing bcnexus packages from setup.py..."
    pip install -e .
else
    echo "setup.py not found in root (BC_NEXUS). Skipping installation."
fi

echo "Module initialized and bcnexus package installed successfully."