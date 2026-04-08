#!/usr/bin/env python3

import csv
import os

def update_levis_template():
    """Update the Levi's template to include stretch field"""
    
    input_file = 'data/processed/levis_manual_sample.csv'
    output_file = 'data/processed/levis_manual_sample_updated.csv'
    
    print("=== Updating Levi's Template with Stretch Field ===")
    
    # Read the existing CSV
    rows = []
    with open(input_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        original_fieldnames = reader.fieldnames
        
        for row in reader:
            rows.append(row)
    
    print(f"Original fieldnames: {original_fieldnames}")
    
    # Add the stretch field
    new_fieldnames = original_fieldnames + ['stretch']
    
    # Update existing rows with empty stretch field
    for row in rows:
        row['stretch'] = ''
    
    # Write the updated CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=new_fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    
    print(f"✅ Updated template created: {output_file}")
    print(f"📋 New fieldnames: {new_fieldnames}")
    
    # Replace the original file
    os.replace(output_file, input_file)
    print(f"✅ Original file updated: {input_file}")
    
    return input_file

def show_updated_guide():
    """Show updated guide for the new stretch field"""
    
    print("\n" + "="*60)
    print("📋 UPDATED LEVI'S DATA COLLECTION GUIDE")
    print("="*60)
    
    print("\n🆕 NEW FIELD ADDED: 'stretch'")
    print("┌─────────────────┬─────────────────────────────────────────────┐")
    print("│ Field           │ How to Fill                                 │")
    print("├─────────────────┼─────────────────────────────────────────────┤")
    print("│ stretch         │ 'stretch' or 'non-stretch'                  │")
    print("│                 │ Check product description for stretch info   │")
    print("│                 │ Look for: 'Stretch', 'Flex', 'Elastane'     │")
    print("│                 │ If not mentioned, use 'non-stretch'         │")
    print("└─────────────────┴─────────────────────────────────────────────┘")
    
    print("\n🔍 HOW TO IDENTIFY STRETCH JEANS:")
    print("• Look for these keywords in product description:")
    print("  - 'Stretch'")
    print("  - 'Flex'")
    print("  - 'Elastane'")
    print("  - 'Spandex'")
    print("  - 'Levi's® Flex'")
    print("  - 'Levi's® Ease'")
    print("• Check the product features section")
    print("• Look at the material composition")
    
    print("\n📝 EXAMPLES:")
    print("• '511™ Slim Fit Levi's® Flex Men's Jeans' → 'stretch'")
    print("• '501® Original Fit Men's Jeans' → 'non-stretch'")
    print("• '505™ Regular Fit Men's Jeans' → 'non-stretch'")
    print("• '514™ Straight Fit Men's Jeans' → 'non-stretch'")
    
    print("\n🎯 UPDATED FIELD ORDER:")
    print("1. product_id")
    print("2. product_name")
    print("3. fit_id")
    print("4. fabric_id")
    print("5. wash_state")
    print("6. gender")
    print("7. colorway")
    print("8. status")
    print("9. product_url")
    print("10. stretch ← NEW FIELD")
    
    print("\n💡 TIPS FOR STRETCH IDENTIFICATION:")
    print("• Most Levi's jeans are non-stretch by default")
    print("• Look for 'Flex' or 'Ease' in the product name")
    print("• Check the product description for stretch content")
    print("• When in doubt, use 'non-stretch'")
    print("• Some fits like 511 often come in both stretch and non-stretch versions")

if __name__ == "__main__":
    # Update the template
    updated_file = update_levis_template()
    
    # Show the updated guide
    show_updated_guide()
    
    print(f"\n✅ Template updated successfully!")
    print(f"📁 File location: {updated_file}")
    print(f"🆕 New field 'stretch' added to the schema")
