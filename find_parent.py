import pandas as pd
import json
import re

df = pd.read_csv('combine_20240913_113622.csv')

# Load JSON mapping
with open('gt_lvl1_lvl2_mapping.json', 'r') as file:
    category_mapping = json.load(file)


def clean_text(text):
    """Remove special characters and convert to lowercase."""
    if isinstance(text, str):
        text = text.lower()  # Convert to lowercase
        text = re.sub(r'[^\w\s]', '', text)  # Remove special characters
    return text

# Create a dictionary to map Level 2 categories to Level 1 categories
level_2_to_level_1 = {}
for level_1, level_2_dict in category_mapping["Ticket Categories"].items():
    level_1_clean = clean_text(level_1)
    for level_2, sub_levels in level_2_dict.items():
        level_2_clean = clean_text(level_2)
        for sub_level_2 in sub_levels:
            sub_level_2_clean = clean_text(sub_level_2)
            level_2_to_level_1[sub_level_2_clean] = level_1_clean

# Load CSV file
# Clean level_2_category_2 values in the DataFrame
df['level_2_category_2_clean'] = df['level_2_category_2'].apply(clean_text)
df['ai_category_1'] = df['level_2_category_2_clean'].map(level_2_to_level_1)

df['ai_category_2'] = df['level_2_category_2']
df['match'] = df['gt_category_2'] == df['level_2_category_2']


# Drop the temporary cleaned column
df = df.drop(columns=['level_2_category_2_clean'])

# Reorder columns to insert 'ai_category_1' before 'level_2_category_2'
columns = df.columns.tolist()
columns.remove('ai_category_1')
columns.remove('ai_category_2')
level_2_index = columns.index('level_2_category_2')
columns.insert(level_2_index+1, 'ai_category_2')
columns.insert(level_2_index+1, 'ai_category_1')

df = df[columns]

# Save updated CSV
df.to_csv('updated_output.csv', index=False)

print("CSV file updated successfully.")
