import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components
import gdown

import re

st.set_page_config(
    layout="wide"
)

'''
# CHRL Wx Station Visit Summary

1. Please allow a moment for the database to load.
2. Select desired station and number of recent trip reports to be included.
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

# # columns to search for station names
# station_cols = ['Central Coast Stations','South Coast Mainland Stations','Haida Gwaii Stations','Vancouver Island Stations',
#                 'Russell Creek Substation','Mt Cain Substation','Calvert Watershed Name','Other Station Name']
# columns to search for station names
station_cols = ['Central_Coast_Stations','South_Coast_Mainland_Stations','Haida_Gwaii_Stations','Vancouver_Island_Stations',
                'Russell_Creek_Substation','Calvert_Watershed_Name','Other_Station_Name']

# get unique stations names to populate dropdown options
station_names = np.unique(df.loc[:, station_cols].astype(str).values)

## APP ELEMENTS FOR USER TO SELECT STATION AND NUMBER OF TRIPS
station = st.selectbox('Select station', station_names, index=None)
num_entries = st.number_input('Select number of recent entries to include', value=5)
# img_flag = st.checkbox('Display images on page (will increase processing time)')

## MAIN SCRIPT
if st.button('Get Summary Table'):
#     check inputs
    if station is None:
        st.write(':red[Please select a station.]')
    elif num_entries <= 0:
        st.write(':red[Please select a sensible number.]')
    else:
        # get entries for target station
        df_station = df.loc[np.where(np.any(df == station, axis=1))].copy()

        # # select columns to keep in table and define new column names for each (CSV)
        # cols2keep = ['Job Start Time', 'User',
        #        'What jobs are being completed? : Snow Course',
        #        'What jobs are being completed? : Drone Survey',
        #        'What jobs are being completed? : CF',
        #        'What jobs are being completed? : Sensor Change',
        #        'What jobs are being completed? : Precip Gage',
        #        'What jobs are being completed? : Lys Calibration',
        #        'What jobs are being completed? : Tipping Bucket Calibration',
        #        'What jobs are being completed? : Data Download',
        #        'What jobs are being completed? : General Maintenance',
        #        'Sensor Change : Type of Sensor',
        #        'Sensor Change : Why is the sensor being changed',
        #        'Sensor Change : Additional Notes',
        #        'General Notes']

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

        new_colnames = ['date', 'users', 'snow_course', 'drone', 'CF', 'sens_change', 'p_gage', 'lys_cal', 'buck_cal', 'data', 'gen_maint', 'sens_changed','reason', 'sens_notes', 'general_notes', 'photo', 'photo_note']
        
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

        # clean up for html table readability
        df_table[df_table == 'no'] = ' '
        df_table[df_table == 'yes'] = 'Y'

        # convert to html file
        filestr = station.replace(" ", "").replace("-", "") + '_pretrip_' + date.today().strftime("%d %b %Y").replace(" ", "") + '.html'
        df_table.to_html(open(filestr, 'w', encoding="utf-8"), index=False, escape=False, justify='left')
        
        # download on button click
        with open(filestr, 'r+', encoding="utf-8") as file:
            btn = st.download_button(
                label='Download Summary Table',
                data=file,
                file_name=filestr,
                mime="text/html"
              )

        # print html table to app page
        components.html(df_table.to_html(index=False, escape=False, justify='left'), height=3000)

    # # display photos on app page if requested
    # if img_flag:
    #         c = 0
    #         for index, row in df_pic.iterrows():
    #             if row['photo'] != '':
    #                 c = c + 1
    #                 url = row['photo']
    #                 output = 'img.png'
    #                 gdown.download(url=url, output=output, quiet=False, fuzzy=True)
    #                 cap = row['date'] + ': ' + row['photo_note']
    #                 if c == 1:
    #                     col1, col2, col3 = st.columns([0.33, 0.33, 0.33], gap='small', vertical_alignment="bottom")
    #                     with col1:
    #                         st.image('img.png', width=300, caption=cap)
    #                 elif c == 2:
    #                     with col2:
    #                         st.image('img.png', width=300, caption=cap)
    #                 elif c == 3:
    #                     with col3:
    #                         st.image('img.png', width=300, caption=cap)
    #                     c = 0