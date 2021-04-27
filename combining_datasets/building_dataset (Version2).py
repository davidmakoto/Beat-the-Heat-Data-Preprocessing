
#Load libaries
import pandas as pd 
import seaborn as sns
import matplotlib.pyplot as plt 
import numpy as np 
import datetime as dt 
import geopandas as gpd

#Load datasets
FireRec = pd.read_csv('mapdataall.csv')

FireRec

#Data = FireRec[["incident_type","incident_dateonly_extinguished","incident_dateonly_created","calfire_incident","incident_county"]]
Data = pd.DataFrame(FireRec, columns={"incident_type","incident_dateonly_extinguished","incident_dateonly_created","calfire_incident","incident_county"})

Data.incident_type.unique()



Data_Wildfire = Data.loc[Data.incident_type=='Wildfire']
#Data_Wildfire = Data.where(Data.incident_type=='Wildfire')

Data_Wildfire.incident_county.dropna(inplace=True)


#Data_CAFire= Data_Wildfire[Data_Wildfire['calfire_incident']==True]
Data_CAFire = Data_Wildfire.where(Data_Wildfire.calfire_incident==True)

Data_CAFire

Data_CAFire.dropna()

Data_CAFire.dtypes

Data_CAFire.loc[:,("Date")] = pd.to_datetime(Data_CAFire['incident_dateonly_created'])
dataFormattedDates = Data_CAFire.dropna()
dataFormattedDates

notWildfire.incident_type.size

dataFormattedDatesAfter2019 = dataFormattedDates[dataFormattedDates['Date'].dt.year >= 2019]
dataFormattedDatesAfter2019andBefore2021 = dataFormattedDatesAfter2019[dataFormattedDatesAfter2019['Date'].dt.year <= 2020]
#dataFormattedFireSeason = dataFormattedDatesAfter2019andBefore2021.loc[dataFormattedDatesAfter2019andBefore2021.Date.dt.month>=5]
#dataFormattedFireSeason = dataFormattedFireSeason.loc[dataFormattedFireSeason.Date.dt.month<=11]
fireRecordData =dataFormattedFireSeason



fireRecordData2 = pd.DataFrame(fireRecordData,columns={"incident_dateonly_extinguished","incident_dateonly_created","incident_county"})

fireRecordData2[["incident_dateonly_extinguished","incident_dateonly_created"]]= fireRecordData2[["incident_dateonly_extinguished","incident_dateonly_created"]].apply(pd.to_datetime)

fireRecordData2 #Data in datetime format


fireRecord = datesplit(fireRecordData2)  #Get all date in range of start and end date

fireRecord.drop_duplicates(inplace=True)

CA_counties_geodf = read_geojson_geodf()
COUNTY = pd.DataFrame(CA_counties_geodf, columns={'COUNTY_FIPS','COUNTY_NAME'})


for county_name in fireRecord.incident_county.unique():
      if county_name not in COUNTY.COUNTY_NAME.unique():
        fireRecord.drop(fireRecord.loc[fireRecord.incident_county==county_name].index,inplace=True)

for i, row in COUNTY.iterrows():
      fireRecord.replace(to_replace=row.COUNTY_NAME,value=row.COUNTY_FIPS,inplace=True)

fireRecord.incident_county =  fireRecord.incident_county.astype(str).astype(int)
fireRecord

fireRecord.sort_values(['incident_county','BurnDate'],ascending=[True,True],inplace=True,ignore_index=True)
fireRecord.incident_county.unique()

TA = pd.read_csv('FM2019_2020.csv')
NDVI = pd.read_csv('NDVI_Interpolated_2019_2020.csv')
LST = pd.read_csv('LST_Interpolated_2019_2020.csv')

TA.Date = pd.to_datetime(TA['Date'])
#TA = TA.loc[TA.Date.dt.month>=5]
#TA = TA.loc[TA.Date.dt.month<=11]


NDVI.Date = pd.to_datetime(LST['Date'])
#NDVI = NDVI.loc[NDVI.Date.dt.month>=5]
#NDVI = NDVI.loc[NDVI.Date.dt.month<=11]


LST.Date = pd.to_datetime(LST['Date'])
#LST = LST.loc[LST.Date.dt.month>=5]
#LST = LST.loc[LST.Date.dt.month<=11]

TAdropped = []
for county in TA.County_FIP.unique():
  if county not in fireRecord.incident_county.unique():
    TAdropped.append(county)

for i in TAdropped:
  TA = TA.drop(TA.loc[TA['County_FIP']==i].index)
  NDVI = NDVI.drop(NDVI.loc[NDVI['County_FIP']==i].index)
  LST = LST.drop(LST.loc[LST['County_FIP']==i].index)



TA["Class"] = "No_fire"      #TA dataset
TA.reset_index(inplace=True)
TA

NDVI

for county in fireRecord.incident_county.unique():
      FireRecordCounty = fireRecord.loc[fireRecord.incident_county==county]
      TACounty = TA.loc[TA.County_FIP==county]
      for i, row in FireRecordCounty.iterrows():
        sameDate = TACounty.loc[TACounty.Date==row.BurnDate]
        TA.Class.iloc[sameDate.index]= 'Fire'



TA.drop(axis = 1, columns='index',inplace=True)
TA


TA['Class'].value_counts()

NDVI.Date = pd.to_datetime(NDVI.Date)
NDVI.sort_values(['County_FIP','Date'],ascending=[True,True],inplace=True,ignore_index=True)
LST.Date = pd.to_datetime(LST.Date)
LST.sort_values(['County_FIP','Date'],ascending=[True,True],inplace=True,ignore_index=True)


LST

data =[TA['Date'],NDVI["NDVI"],LST["LST"],TA["FM"],TA["Class"],TA['County_FIP']]
Cols_name=['Date',"NDVI","LST","TA","Class",'County_FIP']

CA_Wildfires = pd.concat(data, axis=1, keys=Cols_name)

CA_Wildfires

CA_Wildfires['NDVI'].isna().sum()

CA_Wildfires.sort_values(['County_FIP', 'Date'], ascending=[True, True], inplace=True, ignore_index=True)

CA_Wildfires.to_csv('CA_Wildfires.csv')

def read_geojson_geodf():
        """ Loading county boundaries via geojson - returns arr of county geometry shapes """
        # source: https://gis.data.ca.gov/datasets/8713ced9b78a4abb97dc130a691a8695_0?geometry=-146.754%2C31.049%2C-91.251%2C43.258&page=7
        CA_cnty_geojson_link = 'https://opendata.arcgis.com/datasets/8713ced9b78a4abb97dc130a691a8695_0.geojson'
        return gpd.read_file(CA_cnty_geojson_link)

def datesplit(data):
  df= pd.concat([pd.DataFrame({'incident_county': row.incident_county,
                         'BurnDate': pd.date_range(row.incident_dateonly_created, row.incident_dateonly_extinguished)},
                          columns=['BurnDate','incident_county'])
                          for i, row in data.iterrows()], ignore_index=True)
  return pd.concat([pd.DataFrame({'incident_county': row.incident_county.split(', '),
                         'BurnDate': row.BurnDate},
                          columns=['BurnDate','incident_county'])
                          for i, row in df.iterrows()], ignore_index=True)