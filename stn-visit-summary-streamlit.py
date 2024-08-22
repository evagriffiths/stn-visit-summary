import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components
import gc

st.set_page_config(
    layout="wide"
)

'''
# CHRL Wx Station Visit Summary

1. Please allow a moment for the database to load.
2. The database updates automatically every 24 hrs, but you can also trigger an update manually with the "Update Visit Form Database" button if needed.
2. Select desired station(s) and number of recent trip reports to be included.
3. Click "Get Summary Table" button.
4. Click "Download Summary Table" button if you would like to download a copy.
'''

## READ GOOGLE SHEET ON APP LAUNCH SO THAT STATION NAMES DROPDOWN MENU CAN BE POPULATED
# build credentials from secrets
credentials = {
    "type": st.secrets["gcp_service_account"]["type"],
    "project_id": st.secrets["gcp_service_account"]["project_id"],
    "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
    "private_key": st.secrets["gcp_service_account"]["private_key"],
    "client_email": st.secrets["gcp_service_account"]["client_email"],
    "client_id": st.secrets["gcp_service_account"]["client_id"],
    "token_uri": st.secrets["gcp_service_account"]["token_uri"],
}

# connect to google sheets
gc = gspread.service_account_from_dict(credentials)
sh = gc.open("Weather Station Visit Form Test")

# pull wx station visit sheet and put in dataframe
worksheet = sh.worksheet('Weather Station Visit MERGED')
df = pd.DataFrame(worksheet.get_all_records())

# columns to search for station names
station_cols = ['Central_Coast_Stations','South_Coast_Mainland_Stations','Haida_Gwaii_Stations','Vancouver_Island_Stations',
                'Russell_Creek_Substation','Calvert_Watershed_Name','Other_Station_Name']

# get unique stations names to populate dropdown options
station_names = np.unique(df.loc[:, station_cols].astype(str).values)

# Update database button
if st.button('Update Visit Form Database'):
    exec(open('update-stn-visit-gsheet.py').read())

## APP ELEMENTS FOR USER TO SELECT STATION AND NUMBER OF TRIPS
# station = st.selectbox('Select station', station_names, index=None)

station_list = st.multiselect('Select station', station_names)


num_entries = st.number_input('Select number of recent entries to include', value=5)

## MAIN SCRIPT

if st.button('Get Summary Table'):
#     check inputs
    if station_list is None:
        st.write(':red[Please select a station.]')
    elif num_entries <= 0:
        st.write(':red[Please select a sensible number.]')
    else:
        df_merge_list = []
        for station in station_list:
            # get entries for target station
            df_station = df.loc[np.where(np.any(df == station, axis=1))].copy()

            # select columns to keep in table and define new column names for each (CSV)
            cols2keep = ['Job_Start_Time', 'User',
                'What_jobs_are_being_completed_.Snow_Course',
                'What_jobs_are_being_completed_.Drone_Survey',
                'What_jobs_are_being_completed_.CF',
                'What_jobs_are_being_completed_.Sensor_Change',
                'What_jobs_are_being_completed_.Precip_Gage',
                'What_jobs_are_being_completed_.Lys_Calibration',
                'What_jobs_are_being_completed_.Tipping_Bucket_Calibration',
                'What_jobs_are_being_completed_.Data_Download',
                'What_jobs_are_being_completed_.General_Maintenance',
                'Sensor_Change.Type_of_Sensor',
                'Sensor_Change.Why_is_the_sensor_being_changed',
                'Sensor_Change.Additional_Notes',
                'General_Notes',
                'Add_Image.Photo',
                'Add_Image.Photo_Notes']

            new_colnames = ['date', 'users', 'snow_course', 'drone_survey', 'CF', 'sensor_change', 'precip_gage', 'lys_calibration', 'bucket_calibration', 'data_download', 'general_maintenance', 'sens_changed','change_reason', 'sens_notes', 'general_notes', 'photo', 'photo_note']
            # List of job columns to check
            job_cols = ['snow_course', 'drone_survey', 'CF', 'sensor_change', 'precip_gage', 'lys_calibration', 'bucket_calibration', 'data_download', 'general_maintenance']
            # final column order
            col_order = ['date', 'users', 'jobs_done', 'sens_change', 'change_reason', 'sens_notes', 'general notes', 'photo']
            # get selected columns
            df_station = df_station[cols2keep].set_axis(new_colnames, axis='columns')

            # find the n most recent entry dates
            df_station = df_station.sort_values(by="date")
            unique_dates = np.unique(df_station['date'])[-num_entries:]
            # get df with photo notes for printng on app page
            df_pic = df_station.loc[df_station['date'].isin(unique_dates)]
            # get df for html tables that doesn't include photo notes
            df_table = df_pic.drop(['photo_note'], axis=1)

            # loop dates to combine all photo urls from same stn visit and format into html links
            for dt in unique_dates:
                # get rows for this date that have photos
                ix = (df_table['date'] == dt) & (df_table['photo'] != '')
                # extract the urls
                filtered_strings = df_table.loc[ix, 'photo']
                # concatenate the strings and format as HTML anchor tags
                concatenated_strings = '<br><br>'.join(filtered_strings)
                html_links = ''.join(
                    f'<a href="{url}" target="_blank">{url}</a><br><br>' for url in concatenated_strings.split('<br><br>'))
                # ensure the last link does not have a trailing <br><br>
                if html_links.endswith('<br><br>'):
                    html_links = html_links[:-len('<br><br>')]
                # update the df with the formatted strings
                df_table.loc[df_table['date'] == dt, 'photo'] = html_links

                # format other fields for html
                df_table['general_notes'] = df_table['general_notes'].str.replace('\n', '<br>', regex=False)
                df_table['sens_notes'] = df_table['sens_notes'].str.replace('\n', '<br>', regex=False)

                # now that each entry has links for all photos, drop the duplicates
                df_table = df_table.drop_duplicates(subset='date')

            # function to get list of all jobs done in one string
            def get_jobs_done(row):
                return '<br>'.join([job for job in job_cols if row[job] == 'yes'])

            # Apply the function to each row
            df_table['jobs_done'] = df_table.apply(get_jobs_done, axis=1)
            col = df_table.pop('jobs_done')
            df_table.insert(2, 'jobs_done', col)
            
            # drop individual job cols
            df_table = df_table.drop(job_cols, axis=1)

            df_table.insert(0, 'station', station)

            # add df to list
            df_merge_list.append(df_table)
        
        df_merged = pd.concat(df_merge_list, ignore_index=True)

        # convert to html file
        if len(station_list) == 1:
            filestr = station.replace(" ", "").replace("-", "") + '_summary_' + date.today().strftime("%d %b %Y").replace(" ", "") + '.html'
            df_merged.to_html(open(filestr, 'w', encoding="utf-8"), index=False, escape=False, justify='left')
        else:
            filestr = 'multistation_summary_' + date.today().strftime("%d %b %Y").replace(" ", "") + '.html'
            df_merged.to_html(open(filestr, 'a', encoding="utf-8"), index=False, escape=False, justify='left')
        
        # download on button click
        with open(filestr, 'r+', encoding="utf-8") as file:
            btn = st.download_button(
                label='Download Summary Table',
                data=file,
                file_name=filestr,
                mime="text/html"
              )

        # print html table to app page
        components.html(df_merged.to_html(index=False, escape=False, justify='left'), height=3000)

        # finish by clearing cache and freeing up memory
        del df, df_station, df_table, df_merge_list, df_merged
        gc.collect()
        st.cache_data.clear()
        st.cache_resource.clear()
