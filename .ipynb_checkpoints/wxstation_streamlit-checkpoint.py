import gspread
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import date

gc = gspread.oauth(credentials_filename='C:/Users/OCONNORB/AppData/Local/gspread/credentials.json')
sh = gc.open("Weather Station Visit UPDATED")

station = 'Steph 8'
n = 5

# pull wx station visit sheet and put in dataframe
worksheet = sh.sheet1;
df = pd.DataFrame(worksheet.get_all_records())

# drop duplicates created by snow course (= multiple entries per visit) *unless we want snow course info?
# df.drop_duplicates(subset=['submissionid'], inplace=True, ignore_index=True)  # GOOGLE SHEETS
df.drop_duplicates(subset=['Submission ID'], inplace=True, ignore_index=True)

# get entries for target station
df = df.loc[np.where(np.any(df == station, axis=1))]

# drop unwanted columns
# cols2keep = [6,16,17,18,19,20,21,22,23,24,25, 75, 76, 79, 134] # GOOGLE SHEETS
# cols2keep = [8, 19, 20,21,22,23,24,26,27,28,29,121,122,125, 183, 184] # CSV

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

# df = df.iloc[:, cols2keep].set_axis(new_colnames, axis='columns')  # numerical indexing
df = df[cols2keep].set_axis(new_colnames, axis='columns')

# find the n most recent entries
df = df.sort_values(by="date")
df_table = df.iloc[-5:, :].copy()

# clean up for table
df_table[df_table == 'no'] = ' '
df_table[df_table == 'yes'] = 'Y'

display(df_table.style.set_caption(station + ' Pre-Trip Report for ' + str(date.today())))
df_table.to_html(open(station.replace(" ", "") + '_pretrip_example.html', 'w', encoding="utf-8"), index=False)