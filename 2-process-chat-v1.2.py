from openai import OpenAI
import json
import pandas as pd
import time
import sys
from datetime import datetime
from api_key import OPENAI_API_KEY

def get_unique_filename(base_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.csv"

main_output_file = get_unique_filename("classification_sampled_july_batch_1")
incorrect_output_file = get_unique_filename("classification_sampled_july_batch_1_incorrect")


client = OpenAI(api_key=OPENAI_API_KEY)
seed = 12345

# SUMMARIZATION_SYSTEM = """
# Analyze the conversation between the customer service agent and the customer for a large coffee chain. Extract and summarize the key information as follows:

# 1. Cause of Issue(s):
# Identify the root cause of the issue that the customer is facing
# YOU MUST NOTE ALL specific details or concerns mentioned by the customer or agent

# 2. Primary Customer Issue:
# Identify the main problem or question raised by the customer
# YOU MUST NOTE ALL specific details or concerns mentioned by the customer

# 3. Overall Summary:
# Provide a brief, concise summary of the entire interaction, including the main issue, secondary issues, resolutions (if any), and outcome

# Format the summary as follows:
# Customer sentiment: [Sentiment]
# Cause of issue: [Description of what is the cause of the Primary Issue, if not available return "n/a"]
# Primary Issue: [Description of the primary issue without leaving out context]
# Overall Summary: [Brief summary of the interaction, including primary issue and cause]
# """

SUMMARIZATION_SYSTEM = """You are an expert customer service analyst tasked with reviewing a chat history between a customer and an agent for a large coffee chain. Your goal is to extract and summarize the key information to help identify the root cause of the issue raised by the customer. Present the information in a concise and structured manner using the format below.
Instructions:
1.Review the entire conversation between the customer and the agent.
2.Extract the key points, identifying the main issue or complaint raised by the customer.
3.Highlight any contributing factors that may have led to or worsened the problem.
4.Determine the emotional tone based on how the customer expresses themselves throughout the chat.
5.Note the agent's first response and any proposed or implemented solutions.
6.Suggest relevant departments or individuals who should be involved in further investigation or resolution.

Output Format:
Primary Concern: [Brief description of the main issue]
Identified Problem: [Main reason for the issue]
Contributing Factors:
-[Factor 1]
-[Factor 2]
Customer sentiment: [Identify customer's sentiment]
Resolution Offered: [Solution proposed or implemented]
Potential Relevant Departments/Persons:
-[Department/Person 1]
-[Department/Person 2]"""

TEXT_CLASSIFICATION_SYSTEM = """
You are an AI assistant specializing in classifying customer service issues for a food and beverage business. Your task is to analyze the provided summary of a customer service interaction and categorize the primary issue and the cause of the issues (if present) into the predefined categories. Follow these guidelines:

Carefully read the entire summary, paying special attention to:
[IMPORTANT]Cause of Issue(s)[/IMPORTANT]
Primary Issue
Overall Summary

Identify the MOST RELEVANT intent based on primarily "Cause of Issue(s)" & secondly "primary issue" based on the intent class from the following options:

{context}

When categorizing, consider the following:

1. Main cause of issue by agent/customer
2. Customer's primary issue
3. The specific products or services mentioned
4. The nature of the complaint or inquiry (e.g., quality, delivery, app functionality)
5. The actions taken by the customer service agent
6. Any technical or operational details provided in the summary

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

    # print(response.choices[0].dict()['message']['content'].replace('\n', ''))
    summarization_result = response.choices[0].dict()['message']['content']
    logs = get_logs(response)
    
    return summarization_result, logs


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


# print(level_1_descriptions_result)
# print(level_2_descriptions_result)
# print(level_1_level_2_mapping)
# print(gt_mapping)

# "Bot Conversations",
# "Career",
# "Wrong Outlet / Address - NA",
# "Slow Order Preparation",
# "Product",

## Load sample data from july 2024 user correct dataset (2 samples from each category-2)
july_data = pd.read_csv("./july-2024-mapped.csv")

target_gt_list = list(gt_mapping.values())

july_data = july_data.dropna()
july_data = july_data[july_data["new-category-2"].isin(target_gt_list)]

july_data["new-category-2"].value_counts()

# ------------------------------------------------------------

# def sample_group(group):
#     n = min(len(group), 1)  # Take 2 samples or all if less than 2
#     return group.sample(n=n, random_state=42)

# sampled_july_df_batch_1 = july_data.groupby("new-category-2").apply(sample_group).reset_index(drop=True)

# sampled_july_df_batch_1 = sampled_july_df_batch_1[['ticket.id', 'new-category-1', 'new-category-2', 'new-department', 'text']]

# ------------------------------------------------------------

# Count the number of unique categories
num_categories = july_data['new-category-2'].nunique()

# Calculate samples per category (round down to ensure we don't exceed 3000)
samples_per_category = 3000 // num_categories

# Modify the sample_group function
def sample_group(group):
    n = min(len(group), samples_per_category)
    return group.sample(n=n, random_state=42)

# Apply the sampling
sampled_july_df_batch_1 = july_data.groupby("new-category-2").apply(sample_group).reset_index(drop=True)

# If the total is less than 3000, you can add more samples randomly
if len(sampled_july_df_batch_1) < 3000:
    remaining = 3000 - len(sampled_july_df_batch_1)
    additional_samples = july_data[~july_data.index.isin(sampled_july_df_batch_1.index)].sample(n=remaining, random_state=42)
    sampled_july_df_batch_1 = pd.concat([sampled_july_df_batch_1, additional_samples])

# Shuffle the final DataFrame
# sampled_july_df_batch_1 = sampled_july_df_batch_1.sample(frac=1, random_state=42).reset_index(drop=True)

# Verify the result
print(f"Total samples: {len(sampled_july_df_batch_1)}")
print(sampled_july_df_batch_1['new-category-2'].value_counts())

# ------------------------------------------------------------


# sampled_july_df_batch_1.shape[0]
# sys.exit()
# july_data.shape[0]

# july_data[july_data['old-category-2'] == july_data['new-category-2']].shape[0]


# Inference

level_1_context = ""
for i, (name, description) in enumerate(level_1_descriptions_result.items()):
    level_1_context += f"{i+1}. {name}:{description}\n\n"


result = {'ticket.id': [], 'gt_category_1': [], 'gt_department': [], 'text': [], 'summary': [], 'gt_category_2': [], 'level_2': [], 'level_2_category_2': [], 'level_1': [], 'token_count':[]}

for i, row in sampled_july_df_batch_1.iterrows():
    
    text = row['text']
    
    result['ticket.id'].append(row['ticket.id'])
    result['text'].append(text)
    result['gt_category_1'].append(row['new-category-1'])
    result['gt_category_2'].append(row['new-category-2'])
    result['gt_department'].append(row['new-department'])
    
    summary, text_summarization_logs = text_summarization(text)
    result['summary'].append(summary)

    # print(summary)

    print('level 1:')
    # print(level_1_context)

    level_1_result, level_1_logs = text_classification(summary, level_1_context, "gpt-4o-mini")

    print(level_1_result)
    
    individual_logs = {
        "text_summarization_logs": text_summarization_logs,
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
        # print(level_2_context)
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


    classification_sampled_july_df = pd.DataFrame(result)
    classification_sampled_july_df.to_csv(main_output_file, index=False)

    incorrect_df = classification_sampled_july_df[classification_sampled_july_df['gt_category_2'] != classification_sampled_july_df['level_2_category_2']]
    incorrect_df.to_csv(incorrect_output_file, index=False)

print(f"Main output saved to: {main_output_file}")
print(f"Incorrect classifications saved to: {incorrect_output_file}")

    # pd.DataFrame(result)

    # classification_sampled_july_df = pd.DataFrame(result)
    # classification_sampled_july_df.to_csv("classification_sampled_july_batch_1.csv", index=False)

    # classification_sampled_july_df[classification_sampled_july_df['gt_category_2'] != classification_sampled_july_df['level_2_category_2']].to_csv("classification_sampled_july_batch_1_incorrect.csv", index=False)

    # classification_sampled_july_df.shape[0]

    # classification_sampled_july_df[classification_sampled_july_df['gt_category_2'] == classification_sampled_july_df['level_2_category_2']].shape[0]



# SINGLE EXAMPLE TEST
# text = """
# user: Wrong order
# agent: Hi this is Nabilah, please give me a moment to carefully review your selected options and I'll get back to you soon. Your patience is appreciated!

# user: Please help i need to refund because wrong location
# agent: Kindly let me check this for you and will get back to you as soon as possible.
# user: im at zuss paka
# agent: We have refunded the amount of RM40.7 to your ZUS balance.
# agent: You may check your ZUS apps for the refunded amount and reorder at the correct outlet.
# agent: Please kindly check the location before placing the order to avoid the same issue from happening.
# agent: Hi there, just wanted to check in and see if you are still here with me?
# agent: 
# As we have not heard back from you for some time, we'll proceed to close this chat. Should you need further assistance, please do not hesitate to chat with us here and we will assist you as soon as we can.

# Thank you and have a pleasant day ahead! 😊
# """
# summary_text, text_summarization_logs = text_summarization(text)


# summary_text = """
# ### Summary of Customer Service Conversation

# #### 1. Customer's Main Issue:
# - **Primary Problem:** The customer, Jin Mey Shum, did not receive their order, which included a Hot Japanese Genmaicha Latté and an Iced Spanish Latté.
# - **Secondary Issue:** The customer had left specific delivery instructions that were not followed.

# #### 2. Order-Related Details:
# - **Order Numbers:** 
#   - Original Order: 24071629987
#   - Recovery Order: 24071641933
# - **Products:** Hot Japanese Genmaicha Latté and Iced Spanish Latté
# - **Delivery Information:** The order was marked as delivered at 5:07 PM by a Grab rider but was not received by the customer.

# #### 3. Customer Inquiry:
# - **Main Question:** The customer wanted to know the status of their order and why it was not received despite specific instructions.
# - **Specific Questions:**
#   - Is there a picture of where the order was left?
#   - Can the order be resent?

# #### 4. Resolution or Next Steps:
# - **Solutions Provided:**
#   - The agent confirmed that the order was returned to the sender.
#   - A recovery order was arranged to resend the drinks.
# - **Promised Actions:**
#   - The recovery order would include specific instructions: less ice, extra hot, and packed separately.
#   - The driver would call the customer's mother, Amy, at 0124719289 upon delivery.

# #### 5. Customer Sentiment:
# - **Emotional State:** The customer appeared frustrated initially but became cooperative and appreciative once a resolution was offered.
# - **Urgency:** The customer expressed a need for immediate resolution by asking for the drinks to be resent promptly.

# #### 6. Key Points:
# - The customer initially had issues with entering the correct phone number.
# - Multiple agents were involved in the conversation, causing some delays.
# - The customer was patient despite the delays and multiple inquiries being handled by the agents.
# - The customer requested specific delivery instructions to be followed for the recovery order.

# This summary captures the essential details and interactions from the customer service conversation, providing a clear overview of the issue, inquiry, resolution, and customer sentiment.
# """

# level_1_result, level_1_logs = text_classification(summary_text, level_1_context)

# print(level_1_result)


# if level_1_result in level_1_level_2_mapping:
#     level_2_names = level_1_level_2_mapping[level_1_result]
#     level_2_context = ""
#     index = 1
#     for name, description in level_2_descriptions_result.items():
#         if name in level_2_names:
#             level_2_context += f"{index}. {name}\n\t{description}\n\n"
#             index += 1
    
#     level_2, level_2_logs = text_classification(summary_text, level_2_context)
#     print(level_2)