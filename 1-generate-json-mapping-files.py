import json

import pandas as pd

df = pd.read_csv("./intent-mapping-20240912_v3.csv")

# Load Category 1
category_1_df = df[['Level 1', 'Level 1 Description']].copy()
category_1_df = category_1_df.dropna()

# Debug
category_1_df.head()

level_1_description_result = {}

for _, row in category_1_df.iterrows():
    level_1 = row['Level 1']
    level_1 = level_1.upper()
    level_1_description = row['Level 1 Description']
    
    level_1_description_result[level_1] = level_1_description

with open('level_1_description.json', 'w') as f:
    json.dump(level_1_description_result, f, indent=4)

# Load Category 2
category_2_df = df.dropna(subset=['Level 2 (MH)', 'Level 2 Description'])
category_2_df = category_2_df.ffill()

category_2_df.head()

level_2_description_result = {}

for _, row in category_2_df.iterrows():
    level_2 = row['Level 2 (MH)']
    level_2 = ' '.join(level_2.split("_")).upper()
    level_2_description = row['Level 2 Description']
    
    level_2_description_result[level_2] = level_2_description

level_2_description_result = dict(sorted(level_2_description_result.items()))

with open('level_2_description.json', 'w') as f:
    json.dump(level_2_description_result, f, indent=4)

# Debug
# category_2_df.head()

# Map Category 2 to Category 1
level_1_level_2_mapping = {}

for _, row in category_2_df.iterrows():
    level_1 = row['Level 1']
    level_1 = level_1.upper()
    level_2 = row['Level 2 (MH)']
    level_2 = ' '.join(level_2.split("_")).upper()

    level_1_level_2_mapping.setdefault(level_1, []).append(level_2)

with open('level_1_level_2_mapping.json', 'w') as f:
    json.dump(level_1_level_2_mapping, f, indent=4)

print("Done")