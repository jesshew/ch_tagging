from openai import OpenAI
import pandas as pd
import time
import os
from datetime import datetime
from api_key import OPENAI_API_KEY

def get_unique_filename(base_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.csv"

# main_output_file = get_unique_filename("classification_sampled_july_batch_1")
# incorrect_output_file = get_unique_filename("classification_sampled_july_batch_1_incorrect")


# input_file_name = '20240912_problematic_rerun.csv'
input_file_name = '20240906_classification_sampled_july_batch_1_incorrect - classification_sampled_july_batch_1_incorrect_20240906_032652.csv'
main_output_file = get_unique_filename(f"summarization_from_{input_file_name}")


client = OpenAI(api_key=OPENAI_API_KEY)
seed = 12345

# 6.Suggest relevant departments or individuals who should be involved in further investigation or resolution.


SUMMARIZATION_SYSTEM = """You are an expert customer service analyst tasked with reviewing a chat history between a customer and an agent for a large coffee chain. Your goal is to extract and summarize the key information to help identify the root cause of the issue raised by the customer. Present the information in a concise and structured manner using the format below.
Instructions:
1.Review the entire conversation between the customer and the agent.
2.Extract the key points, identifying the main issue or complaint raised by the customer. YOU MUST NOTE ALL specific details or concerns mentioned by the customer or agent, while avoiding attributing blame to the chat agent for response times or immediate actions.
3.Focus on analyzing what or who could have caused the issue the customer is facing, based on the details provided. Investigate underlying factors such as system errors, product/service failures, miscommunication, or external circumstances.
4.Determine the emotional tone based on how the customer expresses themselves throughout the chat.
5.Provide a brief, concise summary of the entire interaction, including the main issue, secondary issues, resolutions (if any), and outcome, while emphasizing the root cause of the issue rather than the performance of the agent.

Output Format:
Customer sentiment: [One word Sentiment]
Primary Concern: [Brief description of the main issue]
Identified Problem: [Main reason for the issue]
Contributing Factors:
-[Factor 1]
-[Factor 2]
Resolution Offered: [Solution proposed or implemented]
Overall Summary: [Brief summary of the interaction, including primary issue and cause]
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

def text_summarization(text):
    response = client.chat.completions.create(
      model="gpt-4o-mini",
      temperature=0,
      messages=[
        {"role": "system", "content": SUMMARIZATION_SYSTEM},
        {
          "role": "user",
          "content": text
        }
      ],
      max_tokens=400,
    )

    summarization_result = response.choices[0].dict()['message']['content']
    logs = get_logs(response)
    
    return summarization_result, logs

# Load sample data with specific headers
# july_data = pd.read_csv(f"./{input_file_name}", usecols=['ticket.id', 'new-category-1', 'new-department', 'new-category-2', 'text'])
july_data = pd.read_csv(f"./{input_file_name}", usecols=['ticket.id', 'gt_category_1', 'gt_department', 'gt_category_2', 'text'])
july_data = july_data.dropna(subset=['text'])

# Sample the data (adjust as needed)
# july_data = july_data.sample(n=3000, random_state=42)
# Check if file exists to write header or not
file_exists = os.path.isfile(main_output_file)
import csv

# Open CSV file for appending data
with open(main_output_file, 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    
    # Write the header only if the file doesn't exist (first time)
    if not file_exists:
        # writer.writerow(["ticket.id", "new-category-1", "new-department", "new-category-2", "text", "summary", "token_count"])
        writer.writerow(["ticket.id", "gt_category_1", "gt_department", "gt_category_2", "text", "summary", "token_count"])
    
    # for i, row in july_data.iterrows():
    for i, row in july_data.iloc[1077:].iterrows():
        text = row['text'].replace('"', '""')  # Escape double quotes in text
        
        # Summarize the text
        summary, text_summarization_logs = text_summarization(text)
        summary = summary.replace('"', '""')  # Escape double quotes in summary
        
        # Prepare data for the CSV row, preserving newlines
        # csv_row = [
        #     row['ticket.id'],
        #     row['new-category-1'],
        #     row['new-department'],
        #     row['new-category-2'],
        #     text,  # Allow newlines to be preserved in text
        #     summary,  # Allow newlines to be preserved in summary
        #     text_summarization_logs['usage']['total_tokens']
        # ]
        csv_row = [
            row['ticket.id'],
            row['gt_category_1'],
            row['gt_department'],
            row['gt_category_2'],
            text,  # Allow newlines to be preserved in text
            summary,  # Allow newlines to be preserved in summary
            text_summarization_logs['usage']['total_tokens']
        ]
        
        # Write the row to the CSV immediately
        writer.writerow(csv_row)

        # Optional: Print status for progress
        print(f"Processed {i + 1} rows.")

print(f"Summarization complete. Output saved to: {main_output_file}")