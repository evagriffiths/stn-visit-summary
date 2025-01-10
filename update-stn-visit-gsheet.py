import gspread
import pandas as pd
import numpy as np
import re
from natsort import natsorted
from update_config import credentials
import pdb

# connect to google sheets
gc = gspread.service_account_from_dict(credentials)
sh = gc.open("Weather Station Visit Form")

# get worksheet names
worksheet_objs = sh.worksheets()
ws_names = []
for ws in worksheet_objs:
    ws_names.append(ws.title)

# rm merged worksheet from list
if np.isin('Weather Station Visit MERGED', ws_names):
    merged_exists = True
    ws_names.remove('Weather Station Visit MERGED')      
else:
    merged_exists = False

# sort worksheets by version (newest first)
ws_names_sorted = natsorted(ws_names, reverse=True)

# let's use the most recent sheet to begin the merge
ws = sh.worksheet(ws_names_sorted[0])
df_merge_list = [pd.DataFrame(ws.get_all_records())]

# loop through all other sheets
for ws_name in ws_names_sorted[1:]:
    # load sheet into df
    ws = sh.worksheet(ws_name)
    df_ws = pd.DataFrame(ws.get_all_records())
    # get fieldnames
    fld_ws = df_ws.columns
    # apply fieldname corrections
    fld_ws = [x.replace('Course_Job.', 'Course.') for x in fld_ws]
    fld_ws = [x.replace('Enter_Snow_Core_Data.', 'Add_Snow_Core.') for x in fld_ws]
    fld_ws = [re.sub('Volume_Added$', 'Volume_Added_ml', x) for x in fld_ws]
    fld_ws = [x.replace('Snow_Course.Add_Snow_Core.Mass_Final__g_', 'Snow_Course.Add_Snow_Core.Total_Mass__g_') for x in fld_ws]
    fld_ws = [x.replace('Snow_Course.Add_Snow_Core.SWE', 'Snow_Course.Add_Snow_Core.SWE__cm_') for x in fld_ws]
    if np.isin('General_Maintenance_Notes_', df_ws.columns):
        df_ws['General_Notes'] = df_ws['General_Maintenance_Notes_'] + df_ws['General_Notes']
        df_ws = df_ws.drop('General_Maintenance_Notes_', axis=1)
        fld_ws.remove('General_Maintenance_Notes_')

    # update df with corrected fieldnames
    df_ws.columns = fld_ws
    # add df to list
    df_merge_list.append(df_ws)

# merge all sheets together
df_merged = pd.concat(df_merge_list, ignore_index=True)

# Ensure 'Job_Start_Time' column is in datetime format
df_merged['Job_Start_Time'] = pd.to_datetime(df_merged['Job_Start_Time'], errors='coerce')

# Sort the merged dataframe by 'Job_Start_Time' in ascending order
df_merged_sorted = df_merged.sort_values(by='Job_Start_Time', ascending=False)

# Convert 'Job_Start_Time' to string to make it JSON serializable
df_merged_sorted['Job_Start_Time'] = df_merged_sorted['Job_Start_Time'].dt.strftime('%Y-%m-%d %H:%M:%S')

# replace NaN with empty so that it can be sent to google sheets (JSON compliant)
df_merged_sorted.fillna('', inplace=True)

# get fieldnames of sorted merged df
fld_merged_sorted = df_merged_sorted.columns

# Create merged sheet if it doesn't already exist
if merged_exists is False:
    # Get the number of rows and columns from the merged dataframe
    rows, cols = df_merged_sorted.shape
    
    # Add 1 to rows for the header row
    ws_merged = sh.add_worksheet(title="Weather Station Visit MERGED", rows=str(rows + 1), cols=str(cols), index=0)  # Insert at the first (leftmost) position
    
    # Insert headers at the top (row 1)
    index = 1
    ws_merged.insert_row(fld_merged_sorted.tolist(), index)
else:
    ws_merged = sh.worksheet('Weather Station Visit MERGED')

# Update the merged worksheet with the data
ws_merged.update([df_merged_sorted.columns.values.tolist()] + df_merged_sorted.values.tolist())


# Print confirmation message
print(f'Google Sheet "Weather Station Visit Form" has been updated')
