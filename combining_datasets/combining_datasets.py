#Load libaries
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import datetime as dt


def main():
    # Load datasets
    FireRec = pd.read_csv('mapdataall.csv')
    FireRec = FireRec[["incident_type",
                    "incident_dateonly_extinguished",
                    "incident_dateonly_created",
                    "calfire_incident",
                    "incident_county"]]

    Data_Wildfire = Data[Data['incident_type'] == 'Wildfire']
    Data_CAFire = Data_Wildfire[Data_Wildfire['calfire_incident'] == True]
    DataDropNaN = Data_CAFire.dropna()
    DataDropNaN.dtypes
    DataDropNaN.loc[:, ("Date")] = pd.to_datetime(DataDropNaN['incident_dateonly_created'])
    dataFormattedDates = DataDropNaN
    dataFormattedDatesAfter2019 = dataFormattedDates[dataFormattedDates['Date'].dt.year >= 2019]
    dataFormattedDatesAfter2019andBefore2021 = dataFormattedDatesAfter2019[dataFormattedDatesAfter2019['Date'].dt.year <= 2020]
    fireRecordData = dataFormattedDatesAfter2019andBefore2021
    fireRecordData2 = fireRecordData[["incident_dateonly_extinguished","incident_dateonly_created"]]

    fireRecordData2[["incident_dateonly_extinguished", "incident_dateonly_created"]] = fireRecordData2[
        ["incident_dateonly_extinguished", "incident_dateonly_created"]].apply(pd.to_datetime)
    fireRecordData2  # Data in datetime format

    fireRecord = datesplit(fireRecordData2)  # Get all date in range of start and end date
    fireRecord = fireRecord.drop_duplicates(subset='BurnedDate')  # Drop duplicates

    # TA = pd.read_csv('TA.csv')
    # NDVI = pd.read_csv('NDVI2018_2020.csv')
    # LST = pd.read_csv('LST_BA.csv')

    # TA["Class"] = "No_fire"
    # TA['Date'] = pd.to_datetime(TA['Date']).dt.date
    #
    # for idx, TADate in enumerate(TA['Date']):
    #     for fireDate in fireRecord['BurnedDate']:
    #         if ((TADate == fireDate)):
    #             TA['Class'][idx] = 'Fire'
    # #             print(TADate, fireDate) # for debugging

    # if TADate == FireDate and TACounty == FireCounty:
    #     TA['Class'][idx] = 'Fire'


    TA['Class'].value_counts()
    NDVI = NDVI.reindex(list(range(0, 731))).reset_index(drop=True)

    data = [NDVI["NDVI"], LST["LST"], TA["TA"], TA["Class"]]
    Cols_name = ["NDVI", "LST", "TA", "Class"]

    CA_Wildfires = pd.concat(data, axis=1, keys=Cols_name)
    CA_Wildfires['NDVI'].isna().sum()


if __name__ == '__main__':
    main()
def datesplit(data):
    parts = []
    for idx, row in data.iterrows():
        parts.append(pd.DataFrame(index=pd.date_range(start=row['incident_dateonly_created'], end=row['incident_dateonly_extinguished'],name='BurnedDate')))
    return pd.concat(parts).reset_index()
