from openai import OpenAI
import json
import pandas as pd
import time
import sys
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)
seed = 12345

# Read the CSV file
# df = pd.read_csv("./20240906_classification_sampled_july_batch_1_incorrect - classification_sampled_july_batch_1_incorrect_20240906_032652.csv")
df = pd.read_csv("./new_summary_20240906_classification_sampled_july_batch_1_incorrect.csv")

# Filter the DataFrame to include only rows where wrong_gt is null
df_filtered = df[df['wrong_gt'].isnull()]

# Optional: Reset the index of the filtered DataFrame
df_filtered = df_filtered.reset_index(drop=True)

# TEXT_CLASSIFICATION_SYSTEM = """
# You are an AI assistant specializing in classifying customer service issues for a food and beverage business. Your task is to analyze the provided summary of a customer service interaction and categorize the primary issue and the cause of the issues (if present) into the predefined categories. Follow these guidelines:

# Carefully read the entire summary, paying special attention to:
# [IMPORTANT]Cause of Issue(s)[/IMPORTANT]
# Primary Issue
# Overall Summary

# Identify the MOST RELEVANT intent based on primarily "Cause of Issue(s)" & secondly "primary issue" based on the intent class from the following options:

# {context}

# When categorizing, consider the following:

# 1. Main cause of issue by agent/customer
# 2. Customer's primary issue
# 3. The specific products or services mentioned
# 4. The nature of the complaint or inquiry (e.g., quality, delivery, app functionality)
# 5. The actions taken by the customer service agent
# 6. Any technical or operational details provided in the summary

# If an issue fits multiple categories, choose the one that best represents the core issue or FINAL RESOLUTION based on the overall context of the interaction.
# Consider the customer's sentiment when distinguishing between general inquiries and complaints.

# Your response should consist of only the selected category name in all caps, without any additional explanation or notes.
# """

TEXT_CLASSIFICATION_SYSTEM = """
You are a Customer Service Issue Analyst tasked with evaluating and classifying customer service interactions within a food and beverage business. Your role involves reviewing, analyzing, and categorizing the primary issues and underlying causes of problems presented during these interactions, ensuring they are accurately sorted into predefined categories. Follow these detailed instructions:

Carefully read the entire summary, paying special attention to:
[IMPORTANT] Identified Problem [/IMPORTANT]
Primary Concern
Overall Summary

Identify the MOST RELEVANT intent based on primarily "Identified Problem" & secondly "Primary Concern" based on the intent class from the following options:

{context}

When categorizing, consider the following:
1. The specific products or services mentioned
2. The nature of the complaint or inquiry (e.g., quality, delivery, app functionality)
3. Any technical or operational details provided in the summary

If an issue fits multiple categories, choose the one that best represents the core issue or FINAL RESOLUTION based on the overall context of the interaction.
Consider the customer's sentiment when distinguishing between general inquiries and complaints.

Your response should consist of only the selected category name in all caps, without any additional explanation or notes.
"""

def get_logs(response):
    logs = {}
    received_time = int(time.time())

    logs["time"] = {
        "created": response.created,
        "received": received_time,
        "duration": received_time - response.created,
    }
    logs["model"] = response.model
    logs["usage"] = response.usage.model_dump()

    return logs

def get_summary_logs(individual_logs):
    usage = {"completion_tokens": [], "prompt_tokens": [], "total_tokens": []}
    time = {"created": [], "received": [], "duration": []}
    models = []
    for _, v in individual_logs.items():
        time["created"].append(v["time"]["created"])
        time["received"].append(v["time"]["received"])

        usage["completion_tokens"].append(v["usage"]["completion_tokens"])
        usage["prompt_tokens"].append(v["usage"]["prompt_tokens"])
        usage["total_tokens"].append(v["usage"]["total_tokens"])

        models.append(v["model"])

    time["created"] = min(time["created"])
    time["received"] = max(time["received"])
    time["duration"] = time["received"] - time["created"]

    usage["completion_tokens"] = sum(usage["completion_tokens"])
    usage["prompt_tokens"] = sum(usage["prompt_tokens"])
    usage["total_tokens"] = sum(usage["total_tokens"])

    result = {"time": time, "usage": usage, "model": models[0]}

    return result

def text_classification(text, context, model="gpt-4o-mini"):

    response = client.chat.completions.create(
      model=model,
      temperature=0,
      messages=[
        {"role": "system", "content": TEXT_CLASSIFICATION_SYSTEM.format(context=context)},
        {
          "role": "user",
          "content": text
        }
      ],
      max_tokens=100,
    )

    classification_result = response.choices[0].dict()['message']['content']
    logs = get_logs(response)
    
    # print("System Prompt")
    # print(TEXT_CLASSIFICATION_SYSTEM.format(context=context))
    # print("User Prompt")
    # print(text)
    
    return classification_result, logs

# ALL INTENT 1/2 MAPPINGS
# Load Dataset and Mapping files
with open('level_1_description.json', 'r') as f:
    level_1_descriptions_result = json.load(f)
    
with open('level_2_description.json', 'r') as f:
    level_2_descriptions_result = json.load(f)
    
with open('level_1_level_2_mapping.json', 'r') as f:
    level_1_level_2_mapping = json.load(f)

with open('gt_mapping.json', 'r') as f:
    gt_mapping = json.load(f)

# level_1_level_2_mapping = {key.upper(): value for key, value in level_1_level_2_mapping.items()}
level_1_level_2_mapping = {key.upper(): value for key, value in level_1_level_2_mapping.items()}

def get_unique_filename(base_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.csv"

main_output_file = get_unique_filename("retest_classification_sampled_july_batch_1")

level_1_context = ""
for i, (name, description) in enumerate(level_1_descriptions_result.items()):
    level_1_context += f"{i+1}. {name}:{description}\n\n"

result = {'ticket.id': [], 'gt_category_1': [], 'gt_department': [], 'text': [], 'summary': [], 'gt_category_2': [], 'level_2': [], 'level_2_category_2': [], 'level_1': [], 'token_count':[]}

for i, row in df_filtered.iterrows():
    result['ticket.id'].append(row['ticket.id'])
    result['text'].append(row['text'])
    result['gt_category_1'].append(row['gt_category_1'])
    result['gt_category_2'].append(row['gt_category_2'])
    result['gt_department'].append(row['gt_department'])
    result['summary'].append(row['summary'])

    summary = row['summary']

    print('level 1:')
    level_1_result, level_1_logs = text_classification(summary, level_1_context, "gpt-4o-mini")
    print(level_1_result)
    
    individual_logs = {
        "level_1_logs": level_1_logs
    }
    
    if level_1_result in level_1_level_2_mapping:
        level_2_names = level_1_level_2_mapping[level_1_result]
        level_2_context = ""
        index = 1
        for name, description in level_2_descriptions_result.items():
            if name in level_2_names:
                level_2_context += f"{index}. {name}\n\t{description}\n\n"
                index += 1
        
        level_2, level_2_logs = text_classification(summary, level_2_context, "gpt-4o-mini")

        print('level 2:')
        print(level_2)

        individual_logs["level_2_logs"] = level_2_logs
        
        result['level_1'].append(level_1_result)
        result['level_2'].append(level_2)
        
        if level_2 in gt_mapping:
            result['level_2_category_2'].append(gt_mapping[level_2])
        else:
            result['level_2_category_2'].append(level_2)
        
    else:
        result['level_1'].append(level_1_result)
        result['level_2'].append(level_1_result)
        
        if level_1_result in gt_mapping:
            result['level_2_category_2'].append(gt_mapping[level_1_result])
        else:
            result['level_2_category_2'].append(level_1_result)

    final_logs = get_summary_logs(individual_logs)
    result['token_count'].append(final_logs['usage']['total_tokens'])

    # Save intermediate results
    pd.DataFrame(result).to_csv(main_output_file, index=False)

print(f"Retest results saved to: {main_output_file}")
