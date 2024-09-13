import pandas as pd
import json
import re

df = pd.read_csv('combine_20240913_113622.csv')

def clean_text(text):
    """Remove special characters and convert to lowercase."""
    if isinstance(text, str):
        text = text.lower()  # Convert to lowercase
        text = re.sub(r'[^\w\s]', '', text)  # Remove special characters
    return text

def find_ai_category_1(category, mapping):
    """Find the immediate parent category for a given category."""
    for parent, subcategories in mapping.items():
        # If the category is a direct child
        if category in subcategories:
            return parent
    return None

# Load JSON mapping
with open('gt_lvl1_lvl2_mapping.json', 'r') as file:
    category_mapping = json.load(file)

# Clean and build the mapping for level 2 categories
mapping = {}
for parent, subcategories in category_mapping.items():
    parent_clean = parent  # No need to clean the parent as it's the key
    mapping.setdefault(parent_clean, [])
    for subcategory in subcategories:
        subcategory_clean = clean_text(subcategory)
        mapping[parent_clean].append(subcategory_clean)

# Load CSV file
# Clean level_2_category_2 values in the DataFrame
df['level_2_category_2_clean'] = df['level_2_category_2'].apply(clean_text)

# Map the immediate parent category
df['ai_category_1'] = df['level_2_category_2_clean'].apply(lambda x: find_ai_category_1(x, mapping))

# Drop the temporary cleaned column
df = df.drop(columns=['level_2_category_2_clean'])
df['ai_category_2'] = df['level_2_category_2']
df['match'] = df['gt_category_2'] == df['level_2_category_2']

# Reorder columns
columns = df.columns.tolist()
columns.remove('ai_category_1')
columns.remove('ai_category_2')
level_2_index = columns.index('level_2_category_2') + 1
columns.insert(level_2_index, 'ai_category_2')
columns.insert(level_2_index, 'ai_category_1')

df = df[columns]

# Save updated CSV
df.to_csv('updated_output.csv', index=False)

print("CSV file updated successfully.")
