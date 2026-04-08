#!/bin/bash
# Monitor test script and notify when done

while true; do
    # Check if process is still running
    if ! ps aux | grep -i "test_scraper_fixes.py" | grep -v grep > /dev/null; then
        # Process finished, check if results file exists
        if [ -f "data/test_scraper_fixes_results.csv" ]; then
            echo "✅ Test script completed! Results saved to data/test_scraper_fixes_results.csv"
            exit 0
        else
            echo "⚠️ Test script finished but no results file found"
            exit 1
        fi
    fi
    sleep 60  # Check every minute
done

