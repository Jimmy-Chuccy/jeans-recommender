#!/bin/bash
# Fix chromedriver permissions on macOS

echo "Fixing chromedriver permissions..."

# Find all chromedriver executables in the webdriver manager cache
CHROMEDRIVER_DIR="$HOME/.wdm/drivers/chromedriver"

if [ -d "$CHROMEDRIVER_DIR" ]; then
    echo "Found chromedriver directory: $CHROMEDRIVER_DIR"
    
    # Find all chromedriver executables
    find "$CHROMEDRIVER_DIR" -name "chromedriver" -type f | while read driver; do
        echo "Processing: $driver"
        
        # Remove quarantine attribute
        xattr -d com.apple.quarantine "$driver" 2>/dev/null || echo "  (No quarantine attribute or permission denied)"
        
        # Make sure it's executable
        chmod +x "$driver" 2>/dev/null || echo "  (Could not set execute permission)"
        
        echo "  ✓ Fixed: $driver"
    done
    
    echo ""
    echo "Done! Try running your test script again."
else
    echo "Chromedriver directory not found: $CHROMEDRIVER_DIR"
    echo "This is normal if chromedriver hasn't been downloaded yet."
fi
