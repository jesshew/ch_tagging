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

def find_ai_catergory_1(category, mapping):
    """Find the immediate parent category for a given category."""
    for parent, subcategories in mapping.items():
        # If the category is a direct child
        if category in subcategories:
            return parent
        # If the category is nested further
        for sub_parent, sub_subcategories in subcategories.items():
            if category in sub_subcategories:
                return sub_parent
    return None

# Load JSON mapping
with open('gt_lvl1_lvl2_mapping.json', 'r') as file:
    category_mapping = json.load(file)

# Clean and build the mapping for level 2 categories
mapping = {}
for parent, subcategories in category_mapping["Ticket Categories"].items():
    parent_clean = parent
    for sub_parent, sub_subcategories in subcategories.items():
        sub_parent_clean = sub_parent
        mapping.setdefault(sub_parent_clean, {})
        for sub_subcategory in sub_subcategories:
            sub_subcategory_clean = clean_text(sub_subcategory)
            mapping[sub_parent_clean][sub_subcategory_clean] = sub_subcategories

# Load CSV file
# Clean level_2_category_2 values in the DataFrame
df['level_2_category_2_clean'] = df['level_2_category_2'].apply(clean_text)
# Map the immediate parent category
df['ai_catergory_1'] = df['level_2_category_2_clean'].apply(lambda x: find_ai_catergory_1(x, mapping))

# Drop the temporary cleaned column
df = df.drop(columns=['level_2_category_2_clean'])
df['ai_category_2'] = df['level_2_category_2']
df['match'] = df['gt_category_2'] == df['level_2_category_2']

columns = df.columns.tolist()
columns.remove('ai_catergory_1')
columns.remove('ai_category_2')
level_2_index = columns.index('level_2_category_2') +1
columns.insert(level_2_index, 'ai_category_2')
columns.insert(level_2_index, 'ai_catergory_1')

df = df[columns]

# Save updated CSV
df.to_csv('updated_output.csv', index=False)

print("CSV file updated successfully.")
