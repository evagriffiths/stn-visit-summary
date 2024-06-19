import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

'''
# CHRL Wx Station Pretrip Report

1. Please allow a moment for the database to load.
2. Select desired station and number of recent trip reports to be included.
3. Click "Get pretrip report" button.
4. A download button will appear - click this to download pretrip report.
'''







# read google sheet on app launch so that station names dropdown menu can be auto-populated
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
sh = gc.open("Weather Station Visit UPDATED")

# pull wx station visit sheet and put in dataframe
worksheet = sh.sheet1;
df = pd.DataFrame(worksheet.get_all_records())

# drop duplicates created by snow course (= multiple entries per visit)
# df.drop_duplicates(subset=['submissionid'], inplace=True, ignore_index=True)
df.drop_duplicates(subset=['Submission ID'], inplace=True, ignore_index=True)

# columns to search for station names
station_cols = ['Central Coast Stations','South Coast Mainland Stations','Haida Gwaii Stations','Vancouver Island Stations',
                'Russell Creek Substation','Mt Cain Substation','Calvert Watershed Name','Other Station Name']
# get unique stations names to populate dropdown options
station_names = np.unique(df.loc[:, station_cols].astype(str).values)

station = st.selectbox('Select station', station_names, index=None)
num_entries = st.number_input('Select number of recent entries to include', value=5)

if st.button('Get Pretrip Report'):
#     check inputs
    if station is None:
        st.write(':red[Please select a station.]')
    elif num_entries <= 0:
        st.write(':red[Please select a sensible number.]')
    else:
        # get entries for target station
        df_station = df.loc[np.where(np.any(df == station, axis=1))].copy()

        # select columns to keep in table and define new column names for each
        cols2keep = ['Job Start Time', 'User',
               'What jobs are being completed? : Snow Course',
               'What jobs are being completed? : Drone Survey',
               'What jobs are being completed? : CF',
               'What jobs are being completed? : Sensor Change',
               'What jobs are being completed? : Precip Gage',
               'What jobs are being completed? : Lys Calibration',
               'What jobs are being completed? : Tipping Bucket Calibration',
               'What jobs are being completed? : Data Download',
               'What jobs are being completed? : General Maintenance',
               'Sensor Change : Type of Sensor',
               'Sensor Change : Why is the sensor being changed',
               'Sensor Change : Additional Notes',
               'General Notes']
        new_colnames = ['date', 'users', 'snow_course', 'drone', 'CF', 'sens_change', 'p_gage', 'lys_cal', 'buck_cal', 'data', 'gen_maint', 'sens_changed','reason', 'sens_notes', 'general_notes'] # GS
        # get selected columns
        df_station = df_station[cols2keep].set_axis(new_colnames, axis='columns')

        # find the n most recent entries
        df_station = df_station.sort_values(by="date")
        df_table = df_station.iloc[-num_entries:, :].copy()

        # clean up for html table readability
        df_table[df_table == 'no'] = ' '
        df_table[df_table == 'yes'] = 'Y'

        # convert to html file
        df_table.to_html(open(station.replace(" ", "") + '_pretrip_example.html', 'w', encoding="utf-8"), index=False)
        
        # download on button click
        with open(station.replace(" ", "") + '_pretrip_example.html', "r") as file:
            btn = st.download_button(
                label='Click to download pretrip report',
                data=file,
                file_name=station.replace(" ", "") + '_pretrip_' + date.today().strftime("%d %b %Y").replace(" ", "") + '.html',
                mime="text/html"
              )

            