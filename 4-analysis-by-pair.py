# from datetime import datetime
# import pandas as pd

# # input_filename = "sample.csv"
# input_filename = "retest_classification_sampled_july_batch_1_20240912_211259.csv"
# output_filename = "analysis_results"

# # Load your data
# df = pd.read_csv(f"./{input_filename}")
# df['level_2_category_2'] = df['level_2_category_2'].replace("OOS (OUT OF STOCK)", "OOS")

# def get_unique_filename(base_name):
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     return f"{base_name}_{timestamp}.xlsx"

# def analyze_categories(df, match_status):
#     """Analyzes category matches or mismatches and returns a DataFrame with counts and percentages."""
#     if match_status == 'mismatch':
#         df_filtered = df[df['gt_category_2'] != df['level_2_category_2']].copy()
#     elif match_status == 'match':
#         df_filtered = df[df['gt_category_2'] == df['level_2_category_2']].copy()
#     else:
#         raise ValueError("Invalid match_status. Use 'match' or 'mismatch'.")

#     # Create concatenated category column using .loc to avoid SettingWithCopyWarning
#     df_filtered.loc[:, 'concat_category'] = df_filtered['gt_category_2'] + ' ; ' + df_filtered['level_2_category_2']
    
#     # Count occurrences and calculate percentages
#     concat_counts = df_filtered['concat_category'].value_counts()
#     concat_percentages = (concat_counts / concat_counts.sum()) * 100
    
#     # Create result DataFrame
#     result_df = pd.DataFrame({
#         'Concatenation': concat_counts.index,
#         'Count': concat_counts.values,
#         'Percentage': concat_percentages.values
#     })
    
#     return result_df

# # Perform mismatch and match analysis
# result_df_mismatch = analyze_categories(df, 'mismatch')
# result_df_match = analyze_categories(df, 'match')

# # Accuracy Analysis
# total_records = len(df)
# total_mismatch = len(df[df['gt_category_2'] != df['level_2_category_2']])
# total_match = len(df[df['gt_category_2'] == df['level_2_category_2']])

# # Calculate percentages
# mismatch_percentage = (total_mismatch / total_records) * 100
# match_percentage = (total_match / total_records) * 100

# # Create a summary DataFrame
# summary_df = pd.DataFrame({
#     'Total Records': [total_records],
#     'Total Mismatches': [total_mismatch],
#     'Mismatch Percentage': [f"{mismatch_percentage:.2f}%"],
#     'Total Matches': [total_match],
#     'Match Percentage': [f"{match_percentage:.2f}%"]
# })

# # Write results to an Excel file
# with pd.ExcelWriter(get_unique_filename(output_filename), engine='xlsxwriter') as writer:
#     result_df_mismatch.to_excel(writer, sheet_name='Mismatch Analysis', index=False)
#     result_df_match.to_excel(writer, sheet_name='Match Analysis', index=False)
#     summary_df.to_excel(writer, sheet_name='Summary', index=False)

# print(f"Analysis has been written to {get_unique_filename(output_filename)}")
# print(f'Total Mismatches - {total_mismatch}')
# print(f'Total Matches - {total_match}')
# print(f'Total Records - {total_records}')



from datetime import datetime
import pandas as pd

def get_unique_filename(base_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.xlsx"

def analyze_categories(df, match_status):
    """Analyzes category matches or mismatches and returns a DataFrame with counts and percentages."""
    if match_status == 'mismatch':
        df_filtered = df[df['gt_category_2'] != df['level_2_category_2']].copy()
    elif match_status == 'match':
        df_filtered = df[df['gt_category_2'] == df['level_2_category_2']].copy()
    else:
        raise ValueError("Invalid match_status. Use 'match' or 'mismatch'.")

    df_filtered.loc[:, 'concat_category'] = df_filtered['gt_category_2'] + ' ; ' + df_filtered['level_2_category_2']
    
    concat_counts = df_filtered['concat_category'].value_counts()
    concat_percentages = (concat_counts / concat_counts.sum()) * 100
    
    result_df = pd.DataFrame({
        'Concatenation': concat_counts.index,
        'Count': concat_counts.values,
        'Percentage': concat_percentages.values
    })
    
    return result_df

def process_file(file_path):
    """Process a single file and return analysis results."""
    df = pd.read_csv(file_path)
    df['level_2_category_2'] = df['level_2_category_2'].replace("OOS (OUT OF STOCK)", "OOS")

    result_df_mismatch = analyze_categories(df, 'mismatch')
    result_df_match = analyze_categories(df, 'match')

    total_records = len(df)
    total_mismatch = len(df[df['gt_category_2'] != df['level_2_category_2']])
    total_match = len(df[df['gt_category_2'] == df['level_2_category_2']])

    mismatch_percentage = (total_mismatch / total_records) * 100
    match_percentage = (total_match / total_records) * 100

    summary_df = pd.DataFrame({
        'Metric': ['Total Records', 'Total Mismatches', 'Mismatch Percentage', 'Total Matches', 'Match Percentage'],
        'Value': [total_records, total_mismatch, f"{mismatch_percentage:.2f}%", total_match, f"{match_percentage:.2f}%"]
    })

    return result_df_mismatch, result_df_match, summary_df

def write_to_excel(result_df_mismatch, result_df_match, summary_df, output_filename):
    """Write analysis results to an Excel file."""
    with pd.ExcelWriter(get_unique_filename(output_filename), engine='xlsxwriter') as writer:
        result_df_mismatch.to_excel(writer, sheet_name='Mismatch Analysis', index=False)
        result_df_match.to_excel(writer, sheet_name='Match Analysis', index=False)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

if __name__ == "__main__":
    # # input_filename = "sample.csv"
    input_filename = "retest_classification_sampled_july_batch_1_20240912_211259.csv"
    output_filename = "analysis_results"
    # input_filename = input("Enter the input CSV filename: ")
    # output_filename = input("Enter the base name for the output file (without extension): ")

    result_df_mismatch, result_df_match, summary_df = process_file(input_filename)
    write_to_excel(result_df_mismatch, result_df_match, summary_df, output_filename)

    print(f"Analysis has been written to {get_unique_filename(output_filename)}")
    for _, row in summary_df.iterrows():
        print(f"{row['Metric']} - {row['Value']}")