import os
import pandas as pd
from datetime import datetime
import csv
import json



composite_header = "Composite by pair"
occurrence_header = "Occurrence"
percentage_header = "% AVG"

def get_unique_filename(base_name, ext="xlsx"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.{ext}"

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
        composite_header: concat_counts.index,
        occurrence_header: concat_counts.values,
        percentage_header: concat_percentages.values
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

    return result_df_mismatch, result_df_match, summary_df, df  # Returning the original df for concatenation

def write_to_excel(result_df_mismatch, result_df_match, summary_df, output_filename):
    """Write analysis results to an Excel file."""
    with pd.ExcelWriter(get_unique_filename(output_filename), engine='xlsxwriter') as writer:
        result_df_mismatch.to_excel(writer, sheet_name='Mismatch Analysis', index=False)
        result_df_match.to_excel(writer, sheet_name='Match Analysis', index=False)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

def sanitize_text(cell):
    """Sanitize cell text to replace problematic characters, especially newlines."""
    if isinstance(cell, str):
        return cell.replace('\r\n', '\n').replace('\r', '\\r')
    return cell

def write_to_csv(combined_df, output_filename):
    """Write concatenated CSV data to a CSV file, handling cells with special characters, preserving newlines."""
    # Pre-process the DataFrame to sanitize all text fields
    sanitized_df = combined_df.applymap(sanitize_text)

    # Write to CSV with quoting to preserve newlines and handle cells with special characters
    sanitized_df.to_csv(get_unique_filename(output_filename, "csv"), index=False, quoting=csv.QUOTE_ALL)

def process_folder(folder_path, output_filename, combined_output_filename,filtered_output_filename):
    """Process all CSV files in the given folder and produce a single Excel and CSV output."""
    all_mismatches = []
    all_matches = []
    all_summaries = []
    all_data = []  # To store all raw data from all files for concatenation

    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(folder_path, filename)
            mismatch, match, summary, original_df = process_file(file_path)
            all_mismatches.append(mismatch)
            all_matches.append(match)
            all_summaries.append(summary)
            all_data.append(original_df)  # Append the raw data
        print(f"Processed {filename}")

    combined_mismatch = pd.concat(all_mismatches, ignore_index=True)
    combined_match = pd.concat(all_matches, ignore_index=True)
    combined_summary = pd.concat(all_summaries, ignore_index=True)
    combined_data = pd.concat(all_data, ignore_index=True)  # Concatenate all original data

    # Aggregate and sort results
    final_mismatch = combined_mismatch.groupby(composite_header).agg({occurrence_header: 'sum'}).reset_index()
    final_mismatch[percentage_header] = (final_mismatch[occurrence_header] / final_mismatch[occurrence_header].sum()) * 100
    final_mismatch = final_mismatch.sort_values(occurrence_header, ascending=False).reset_index(drop=True)

    final_match = combined_match.groupby(composite_header).agg({occurrence_header: 'sum'}).reset_index()
    final_match[percentage_header] = (final_match[occurrence_header] / final_match[occurrence_header].sum()) * 100
    final_match = final_match.sort_values(occurrence_header, ascending=False).reset_index(drop=True)

    # Create overall summary
    total_records = combined_summary['Value'][combined_summary['Metric'] == 'Total Records'].sum()
    total_mismatches = combined_summary['Value'][combined_summary['Metric'] == 'Total Mismatches'].sum()
    total_matches = combined_summary['Value'][combined_summary['Metric'] == 'Total Matches'].sum()
    mismatch_percentage = (total_mismatches / total_records) * 100
    match_percentage = (total_matches / total_records) * 100

    overall_summary = pd.DataFrame({
        'Metric': ['Total Records', 'Total Mismatches', 'Total Matches'],
        'Value': [total_records, total_mismatches, total_matches],
        'Percentage': ['', f"{mismatch_percentage:.2f}%", f"{match_percentage:.2f}%"]
    })

    # Write the results to Excel
    write_to_excel(final_mismatch, final_match, overall_summary, output_filename)

    # Write the concatenated CSV data to a CSV file
    write_to_csv(combined_data, combined_output_filename)

    # Write separate sheets for each mismatched pair
    write_mismatched_pairs(final_mismatch, combined_data, filtered_output_filename)

    return overall_summary

def write_mismatched_pairs(mismatch_df, raw_df, output_filename):
    """Write each mismatched pair to a separate sheet in an Excel file using row numbers as sheet names, with headers in a specified order."""
    # Define the desired column order
    column_order = [
        'ticket.id', 'summary', 'gt_category_2', 'level_2_category_2', 
        'token_count', 'text', 'gt_department', 'gt_category_1', 
        'level_1', 'level_1_confidence', 'level_2', 'level_2_confidence'
    ]

    with pd.ExcelWriter(get_unique_filename(output_filename), engine='xlsxwriter') as writer:
        # Write the Mismatch Analysis sheet
        mismatch_df.to_excel(writer, sheet_name='Mismatch Analysis', index=False)
        
        # Write only the first 50 mismatched pairs to separate sheets with row numbers as names
        for index, row in mismatch_df.head(50).iterrows():
            pair = row[composite_header]
            sheet_name = f"Pair_{index+1}"  # Use row number as sheet name, starting from 1
            filtered_data = raw_df[(raw_df['gt_category_2'] + ' ; ' + raw_df['level_2_category_2']) == pair]
            # Reorder columns and write to Excel
            filtered_data = filtered_data[column_order]
            filtered_data = filtered_data.sort_values(by=['level_2_confidence', 'level_1_confidence'])
            filtered_data.to_excel(writer, sheet_name=sheet_name, index=False)




# def sanitize_sheet_name(name):
#     """Sanitize the sheet name to remove invalid characters and limit length."""
#     # Remove invalid characters
#     name = re.sub(r'[\\/:*?\"<>|]', '', name)
#     # Trim to 31 characters
#     return name[:31]

# def write_mismatched_pairs(mismatch_df, raw_df, output_filename):
#     """Write each mismatched pair to a separate sheet in an Excel file."""
#     with pd.ExcelWriter(get_unique_filename(output_filename), engine='xlsxwriter') as writer:
#         # Write the Mismatch Analysis sheet
#         mismatch_df.to_excel(writer, sheet_name='Mismatch Analysis', index=False)
        
#         # Write each mismatched pair to a separate sheet
#         for _, row in mismatch_df.iterrows():
#             pair = row[composite_header]
#             sheet_name = sanitize_sheet_name(pair)
#             filtered_data = raw_df[(raw_df['gt_category_2'] + ' ; ' + raw_df['level_2_category_2']) == pair]
#             filtered_data.to_excel(writer, sheet_name=sheet_name, index=False)


if __name__ == "__main__":
    input_folder = "20240913"
    analysis_output_filename = "analysis"
    filtered_output_filename = "filtered"
    combined_output_filename = "combine"

    
    overall_summary = process_folder(input_folder, analysis_output_filename, combined_output_filename,filtered_output_filename)
    
    print(f"Analysis has been written to files.")
    for _, row in overall_summary.iterrows():
        print(f"{row['Metric']} - {row['Value']} - {row['Percentage']}")
