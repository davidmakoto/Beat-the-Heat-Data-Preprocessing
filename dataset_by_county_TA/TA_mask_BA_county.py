# NOTES: this file runs smoothly on my machine (no errors and no output)
#   if it doesn't run on yours, it might be because of the dir setup (see below)

# Directory setup notes: in the same dir as this .py file, there should be
# the PreprocessingAuxiliaryFunctions.py, and 2 data folders: 
# input_data_files (all the FM images) and burn_area_files. Within the burn_are_files
# there should be 2 essential folders, burn_date and QA. If all is correct, you shouldn't
# need to reconfigure anything because of the function that uses relative paths 
# (af.create_abs_path_from_relative('rel_path')). If you have questions or want to verify the setup
# Please send me a message on discord

import fiona
import rasterio
import rasterio.mask
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import os   
import sys
import glob
from osgeo import gdal
import numpy as np
import scipy.ndimage
import datetime as dt

from timeit import default_timer as timer
from PreprocessingAuxiliaryFunctions import PreprocessingAuxiliaryFunctions as auxFuncts

def main():
    start = timer()
    af = auxFuncts()
    af.create_paths()

    CA_counties_geodf = af.read_geojson_geodf()
    shapes = af.extract_shapes_from_county_geometry(CA_counties_geodf)
    COUNTY_FIPS = CA_counties_geodf['COUNTY_FIPS']
    #* note: if the shape file doesn't work, uncomment the line below (starting with "shapes = ...") this to fix
    # print(CA_counties_geodf)
    # print(shapes)
    # shapes = af.read_geojson()  # read in list of county boundaries

    out_dir = os.path.normpath(os.path.split(af.BA_burn_date_dir)[0] + os.sep + 'output') + '\\'  # Create and set output directory
    if not os.path.exists(out_dir): os.makedirs(out_dir)
    
    # FM_inDir = (r'C:\Users\Student\Documents\School\Senior design\dataset_by_county\input_data_files')  #Path to FM files
    #* note: dir setup for files should be as follows:
    #* \GitHub\Beat-the-Heat--Machine-Learning\Reprocessing_datasets_by_county\dataset_by_county\FM_by_county.py
    #* within the 'dataset_by_county' folder, also include the FM dataset in a folder named 'input_data_files'
    home_dir = os.getcwd()
    os.chdir(af.FM_inDir)                                                           # Change to working directory
    FMFiles        = glob.glob('VNP14A1.001_FireMask_****.tif')                     # Search for and create a list of FM files
    os.chdir(af.FM_QA_Dir) 
    FMqualityFiles = glob.glob('VNP14A1.001_QA_**.tif')                             # Search the directory for the associated quality .tifs
    os.chdir(af.Support)
    FMlut          = glob.glob('VNP14A1-001-QA-lookup.csv')                         # Search for look up table 
    FM_v6_QA_lut   = pd.read_csv(FMlut[0])   
    FMgoodQuality = af.extracting_good_quality_vals_from_FM_lut(FM_v6_QA_lut)       # print(FMqualityFiles)  # debugging output

    ###### Burn Area Files
    #os.chdir(af.BA_burn_date_dir)                                                   # Change to working directory
    #BAFiles         = glob.glob('MCD64A1.006_Burn_Date_**.tif')                     # Search for and create a list of BA files
    #os.chdir(af.BA_QA_dir) 
    #BAqualityFiles  = glob.glob('MCD64A1.006_QA_**.tif')                            # Search the directory for the associated quality .tifs
    #os.chdir(af.FM_inDir)                                                           # LUTs are in FM folder
    #BAlut           = glob.glob('MCD64A1-006-QA-lookup.csv')                        # Search for BA look up table 
    #v6_BAQA_lut     = pd.read_csv(BAlut[0])                                         # Read in the lut
    #BAgoodQuality   = af.extracting_good_quality_vals_from_BA_lut(v6_BAQA_lut)      # Retrieve list of possible QA values from the quality dataframe
    #BAVal = tuple(range(0, 367, 1))                                                 # List of numbers between 1-366. Used when masking by BA 
    
    ## Initialize Dataframe for final results
    FM_result = []

    # Traverse through the list of FM files 
    for i in range(0, len(FMFiles)):
        os.chdir(af.FM_inDir)
        FM         = gdal.Open(FMFiles[i])                                          # Read file in, starting with MOD13Q1 version 6 #* in dir input_files
        os.chdir(af.FM_QA_Dir)
        FMquality  = gdal.Open(FMqualityFiles[i])                                   # Open the first quality file
        
        FMdate     = af.getFM_Date_Year_Month(FMFiles[i], "D")                      # Get the Date of the file in format MM/DD/YYYY
        FM_year    = af.getFM_Date_Year_Month(FMFiles[i], "Y")                      # Get the year of the file 
        FM_month   = af.getFM_Date_Year_Month(FMFiles[i], "M")                      # Get the month of the file
        #os.chdir(af.BA_burn_date_dir)
        #BAFileName  = af.getBAFileName(BAFiles, FM_month, FM_year)                  # Get BA filename for the current FM file
        #os.chdir(af.BA_QA_dir)
        #BAQAFileName= af.getBAFileName(BAqualityFiles, FM_month, FM_year)           # Get BA QA filename for the current FM file
        #BAscaleFactor = float(1.0)                                                  # Set BA Scale factor
        FMscaleFactor = float(1.0)                                                  # Set FM Scale factor
        x=0
        for county_masked in shapes:
            county_fip = COUNTY_FIPS[x]
            #af.maskByShapefileAndStore(FMFiles[i],FMqualityFiles[i], BAFileName, BAQAFileName, county_masked)
            af.maskByShapefileAndStore(FMFiles[i],FMqualityFiles[i], county_masked)
            ###--------------------------------------------------------------------------###
            ###    OPEN ALL 4 temporary files created get Quality data and mask by BA    ###
            ###--------------------------------------------------------------------------###
            ##--------------------------------------------------------------------------
            os.chdir(af.out_dir)                                                    # out_dir is where output from last step is
            FM         = gdal.Open(af.FM_temp)                                      # Read FM temporary file for current county in the loop
            FMBand     = FM.GetRasterBand(1)                                        # Read the band (layer)
            FMData     = FMBand.ReadAsArray().astype('float')                       # Import band as an array with type float
            ##--------------------------------------------------------------------------
            FMquality     = gdal.Open(af.FMQA_temp)                                 # Open temporary FM quality file
            FMqualityData = FMquality.GetRasterBand(1).ReadAsArray()                # Read in as an array
            FMquality     = None 
            ##--------------------------------------------------------------------------
            #BA          = gdal.Open(af.BA_temp)                                     # Read BA temporary file for current county in the loop
            #BABand      = BA.GetRasterBand(1)                                       # Read the band (layer)
            #BAData      = BABand.ReadAsArray().astype('float')                      # Import band as an array with type float
            ##--------------------------------------------------------------------------
            #BAquality     = gdal.Open(af.BAQA_temp)                                 # Open temporary BA quality file
            #BAqualityData = BAquality.GetRasterBand(1).ReadAsArray()                # Read in as an array
            #BAquality     = None 
            #--------------------------------------------------------------------------
            #BAScaled    = af.get_scaled_df(BABand,BAData,BAscaleFactor)             # Apply the scale factor using simple multiplication
            #BA          = None                                                      # Close the GeoTIFF file
            FMScaled    = af.get_scaled_df(FMBand,FMData,FMscaleFactor)              # Apply the scale factor using simple multiplication
            FM          = None                                                       # Close the GeoTIFF file
 
            #----- MASK AND GET MEAN VALUE -----#
            #BA_masked   = np.ma.MaskedArray(BAScaled, np.in1d(BAqualityData, BAgoodQuality, invert = True))         # Apply QA mask to the BA data
            FM_masked   = np.ma.MaskedArray(FMScaled, np.in1d(FMqualityData, FMgoodQuality, invert = True))         # Apply QA mask to the FM data

            #BA_resampled = scipy.ndimage.zoom(BA_masked,0.5, order=0)                                               # Resample by a factor of 2 with nearest neighbor interpolation
            #if (FM_masked.shape[1] != BA_resampled.shape[1]):                                                       # Remove estra column if exists
            #    FM_masked = np.delete(FM_masked,-1, axis=1)
            #if (FM_masked.shape[0] != BA_resampled.shape[0]):                                                       # Remove extra row if exists
            #    FM_masked = np.delete(FM_masked,0, 0)

            #FM_BA       = np.ma.MaskedArray(FM_masked, np.in1d(BA_resampled, BAVal, invert = True))                 # Mask array, include only BurnArea
            FM_Max      = FM_masked.max()                                                                               # Get FM Max value of the Burn Area

            #----- STORE IT IN RESULT DATAFRAME -----#
            FM_result.append([FMdate,FM_Max, county_fip])
            x = x+1    

        #print running time    
        currentTime = timer() - start                                                                               # calculate current running time
        print('index: {}  --- FileName: {}   ---- Time Elapsed: {}  seconds'.format(i, FMFiles[i], round(currentTime,1)))

    # add header to output dataframe
    result_df = pd.DataFrame(FM_result, columns=["Date","FM","County_FIP"])
    
    #fill null values with mean
    #result_df['FM'].fillna(0, inplace=True)
    
    #sort values by county fip, then by date
    result_df = result_df.sort_values(["County_FIP", "Date"], ascending=(True, True))

    #change to output directory
    os.chdir(af.out_dir)

    # Export statistics to CSV
    result_df.to_csv('FM2019_2020.csv', index=False)  


if __name__ == "__main__":
    # execute only if run as a script
    main()