#!/usr/bin/env python3

import csv
import os

def create_levis_template():
    """Create a CSV template for manual Levi's data collection"""
    
    # Define the schema based on your requirements
    fieldnames = [
        'product_id',      # Unique identifier
        'product_name',    # Full display name of the product
        'fit_id',         # Levi's lot number (501, 511, etc.)
        'fabric_id',      # Leave blank (Levi's doesn't specify like N&F)
        'wash_state',     # Leave blank (unless specifically mentioned)
        'gender',         # "mens" for men's jeans
        'colorway',       # Color as indicated on webpage
        'status',         # "regular" or "on-sales"
        'product_url'     # Direct link to product page
    ]
    
    # Create the template file
    os.makedirs('data/processed', exist_ok=True)
    template_file = 'data/processed/levis_manual_sample.csv'
    
    with open(template_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        
        # Add a few example rows to show the format
        examples = [
            {
                'product_id': 'levis_501_001',
                'product_name': '501® Original Fit Men\'s Jeans',
                'fit_id': '501',
                'fabric_id': '',
                'wash_state': '',
                'gender': 'mens',
                'colorway': 'Dark Wash',
                'status': 'regular',
                'product_url': 'https://www.levi.com/CA/en_CA/clothing/men/jeans/straight/501-original-fit-mens-jeans/p/005013127'
            },
            {
                'product_id': 'levis_511_001',
                'product_name': '511™ Slim Fit Men\'s Jeans',
                'fit_id': '511',
                'fabric_id': '',
                'wash_state': '',
                'gender': 'mens',
                'colorway': 'Black',
                'status': 'on-sales',
                'product_url': 'https://www.levi.com/CA/en_CA/clothing/men/jeans/slim/511-slim-fit-mens-jeans/p/005113127'
            }
        ]
        
        for example in examples:
            writer.writerow(example)
    
    print(f"✅ Levi's template created: {template_file}")
    print(f"📋 Template includes {len(fieldnames)} columns with example data")
    
    return template_file

def show_data_collection_guide():
    """Show detailed guide for manual data collection"""
    
    print("\n" + "="*60)
    print("📋 LEVI'S MANUAL DATA COLLECTION GUIDE")
    print("="*60)
    
    print("\n🎯 TARGET: Collect 20-30 Levi's products")
    print("📍 FOCUS: Men's jeans only")
    print("🔗 WEBSITE: https://www.levi.com/CA/en_CA/clothing/men/jeans")
    
    print("\n📊 DATA COLLECTION PROCESS:")
    print("1. Open Levi's website in your browser")
    print("2. Navigate to Men's Jeans section")
    print("3. For each product you want to collect:")
    print("   - Click on the product")
    print("   - Copy the required information")
    print("   - Add to your CSV file")
    
    print("\n📝 FIELD INSTRUCTIONS:")
    print("┌─────────────────┬─────────────────────────────────────────────┐")
    print("│ Field           │ How to Fill                                 │")
    print("├─────────────────┼─────────────────────────────────────────────┤")
    print("│ product_id      │ Create unique ID: levis_[fit]_[number]      │")
    print("│                 │ Example: levis_501_001, levis_511_002        │")
    print("├─────────────────┼─────────────────────────────────────────────┤")
    print("│ product_name    │ Full product name from page title           │")
    print("│                 │ Example: '501® Original Fit Men's Jeans'    │")
    print("├─────────────────┼─────────────────────────────────────────────┤")
    print("│ fit_id          │ The fit number (501, 511, 505, etc.)       │")
    print("│                 │ Example: '501', '511', '505'                │")
    print("├─────────────────┼─────────────────────────────────────────────┤")
    print("│ fabric_id       │ Leave EMPTY (Levi's doesn't specify)        │")
    print("├─────────────────┼─────────────────────────────────────────────┤")
    print("│ wash_state      │ Leave EMPTY (unless specifically mentioned) │")
    print("├─────────────────┼─────────────────────────────────────────────┤")
    print("│ gender          │ Always 'mens' for men's jeans              │")
    print("├─────────────────┼─────────────────────────────────────────────┤")
    print("│ colorway        │ Color from product page                     │")
    print("│                 │ Example: 'Dark Wash', 'Black', 'Light Wash' │")
    print("├─────────────────┼─────────────────────────────────────────────┤")
    print("│ status          │ 'regular' or 'on-sales' (check for sale)     │")
    print("├─────────────────┼─────────────────────────────────────────────┤")
    print("│ product_url     │ Full URL to product page                     │")
    print("└─────────────────┴─────────────────────────────────────────────┘")
    
    print("\n🎯 RECOMMENDED PRODUCTS TO COLLECT:")
    print("• 501® Original (3-4 variations)")
    print("• 511™ Slim (3-4 variations)")
    print("• 505™ Regular (2-3 variations)")
    print("• 514™ Straight (2-3 variations)")
    print("• 517™ Bootcut (2-3 variations)")
    print("• 541™ Athletic (2-3 variations)")
    print("• 550™ Relaxed (2-3 variations)")
    
    print("\n🎨 RECOMMENDED COLORS:")
    print("• Dark Wash")
    print("• Light Wash")
    print("• Medium Wash")
    print("• Black")
    print("• Grey")
    print("• White")
    
    print("\n💡 TIPS:")
    print("• Look for products on sale to get 'on-sales' status")
    print("• Choose different colors for the same fit")
    print("• Make sure product_id is unique for each entry")
    print("• Copy the exact product name from the page")
    print("• Save the CSV file after each entry")
    
    print("\n📁 FILE LOCATION:")
    print("Your data will be saved to: data/processed/levis_manual_sample.csv")

def show_csv_editing_guide():
    """Show how to edit the CSV file"""
    
    print("\n" + "="*60)
    print("📝 HOW TO EDIT THE CSV FILE")
    print("="*60)
    
    print("\n🔧 METHOD 1: Using Excel/Google Sheets")
    print("1. Open the CSV file in Excel or Google Sheets")
    print("2. Add new rows for each product")
    print("3. Fill in the data following the field instructions")
    print("4. Save the file")
    
    print("\n🔧 METHOD 2: Using a Text Editor")
    print("1. Open the CSV file in a text editor")
    print("2. Add new lines at the end")
    print("3. Follow this format:")
    print('   "levis_501_002","501® Original Fit Men\'s Jeans","501","","","mens","Light Wash","regular","https://www.levi.com/...')
    
    print("\n🔧 METHOD 3: Using Python (if you prefer)")
    print("1. Open the CSV file")
    print("2. Add new rows programmatically")
    print("3. Save the file")
    
    print("\n⚠️  IMPORTANT NOTES:")
    print("• Always use commas to separate fields")
    print("• Put text in quotes if it contains commas")
    print("• Don't delete the header row")
    print("• Make sure product_id is unique")
    print("• Save frequently to avoid losing data")

if __name__ == "__main__":
    # Create the template
    template_file = create_levis_template()
    
    # Show the data collection guide
    show_data_collection_guide()
    
    # Show CSV editing guide
    show_csv_editing_guide()
    
    print(f"\n✅ Setup complete! Start collecting data in: {template_file}")
