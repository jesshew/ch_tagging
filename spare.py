import pandas as pd
import json

# Load CSV file
df = pd.read_csv('combine_20240913_113622.csv')

# Load JSON mapping
with open('gt_lvl1_lvl2_mapping.json', 'r') as file:
    category_mapping = json.load(file)

# Create a dictionary to map Level 2 categories to Level 1 categories with case-insensitive keys
level_2_to_level_1 = {}
for level_1, level_2_dict in category_mapping["Ticket Categories"].items():
    level_1_lower = level_1.lower()
    for level_2, sub_levels in level_2_dict.items():
        level_2_lower = level_2.lower()
        for sub_level_2 in sub_levels:
            sub_level_2_lower = sub_level_2.lower()
            level_2_to_level_1[sub_level_2_lower] = level_1_lower


# Convert level_2_category_2 column to lowercase for case-insensitive matching
df['level_2_category_2_lower'] = df['level_2_category_2'].str.lower()

# Define the new column 'parent_level_1'
df['ai_category_1'] = df['level_2_category_2_lower'].map(level_2_to_level_1)

# Drop the temporary lowercase column
df = df.drop(columns=['level_2_category_2_lower'])
# Define the new column 'ai_category_1'
df['ai_category_2'] = df['level_2_category_2']
df['match'] = df['gt_category_2'] == df['level_2_category_2']

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
