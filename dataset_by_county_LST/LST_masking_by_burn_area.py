# NOTES: this runs without errors for me (Makoto). Haven't done checking except until line 38

# Directory setup notes: in the same dir as this .py file, there should be
# the PreprocessingAuxiliaryFunctions.py, and 2 data folders: 
# input_data_files (all the NDVI images) and burn_area_files. Within the burn_are_files
# there should be 2 essential folders, burn_date and QA. If all is correct, you shouldn't
# need to reconfigure anything because of the function that uses relative paths 
# (af.create_abs_path_from_relative('rel_path')). If you have questions or want to verify the setup
# Please send me a message on discord

# Import libraries
import os
import glob
from osgeo import gdal
import numpy as np
import matplotlib.pyplot as plt
import scipy.ndimage
import pandas as pd
import datetime as dt
from timeit import default_timer as timer
from PreprocessingAuxiliaryFunctions import PreprocessingAuxiliaryFunctions as auxFuncts  # helper functions

def main():
    start = timer()
    af = auxFuncts()  # helper function object

    # Get County Shapes
    CA_counties_geodf = af.read_geojson_geodf()
    shapes = af.extract_shapes_from_county_geometry(CA_counties_geodf)
    COUNTY_FIPS = CA_counties_geodf['COUNTY_FIPS']

    # changing working directory
    out_dir = os.path.normpath(os.path.split(af.BA_burn_date_dir)[0] + os.sep + 'output') + '\\'            # Create and set output directory
    if not os.path.exists(out_dir): os.makedirs(out_dir)

    # create references to files And extract good quality values from look up table
    os.chdir(af.img_files_dir)                                                                              # Change to working directory
    LSTFiles     = glob.glob('MOD11A1.006_LST_Day_1km**.tif')                                               # Search for and create a list of LST files
    os.chdir(af.img_QA_dir)
    qualityFiles = glob.glob('MOD11A1.006_QC_Day**.tif')                                                    # Search the directory for the associated Quality Tiffs
    os.chdir(af.Support)
    lut          = glob.glob('MOD11A1-006-QC-Day-lookup.csv')                                               # Search for look up table   
    img_QA_lut = pd.read_csv(lut[0])                                                                        # Read Look up table
    img_good_quality = af.extracting_good_quality_vals_from_lut_LST(img_QA_lut)                             # Extracting good quality values

    # create references to Burn Area files And extract good quality values from look up table
   # os.chdir(af.BA_burn_date_dir)                                                                           # Change to working directory
   # BAFiles         = glob.glob('MCD64A1.006_Burn_Date_**.tif')                                             # Search for and create a list of BA files
   # os.chdir(af.BA_QA_dir) 
   # BAqualityFiles  = glob.glob('MCD64A1.006_QA_**.tif')                                                    # Search the directory for the associated quality .tifs
   # BAlut           = glob.glob('MCD64A1-006-QA-lookup.csv')                                                # Search for BA look up table 
   # v6_BAQA_lut     = pd.read_csv(BAlut[0])                                                                 # Read in the lut
   # BAgoodQuality   = af.extracting_good_quality_vals_from_BA_lut(v6_BAQA_lut)                              # Retrieve list of possible QA pixel values from the quality dataframe
    #set masking burn area valid values (from 0 to 366) 
   # BAVal = tuple(range(0, 367, 1))
    #initialize result list
    LST_result = []
    for i in range(0, len(LSTFiles)):
        os.chdir(af.img_files_dir)
        LST = gdal.Open(LSTFiles[i])                                                                       # Read file in, starting with MOD13Q1 version 6 #* in dir input_files
        os.chdir(af.img_QA_dir)
        LSTquality = gdal.Open(qualityFiles[i])                                                            # Open the first quality file
        
        LSTdate     = af.getLST_Date_Year_Month(LSTFiles[i], "D")                                           # Get the Date of the file in format MM/DD/YYYY
        LST_year    = af.getLST_Date_Year_Month(LSTFiles[i], "Y")                                           # Get the year of the file 
        LST_month   = af.getLST_Date_Year_Month(LSTFiles[i], "M")                                           # Get the month of the file

        #os.chdir(af.BA_burn_date_dir)
        #BAFileName  = af.getBAFileName(BAFiles, LST_month, LST_year)                                         # Get BA filename for the current LST file
        #os.chdir(af.BA_QA_dir)
        #BAQAFileName= af.getBAFileName(BAqualityFiles, LST_month, LST_year)                                  # Get BA QA filename for the current LST file        

        #BAscaleFactor = float(1.0)                                                                         # Set BA Scale factor
        LSTscaleFactor = float(0.02)                                                                        # Set LST Scale factor
        x = 0                                                                                              # X value for index in county FIP
        ##INSERT FOR LOOP TO SELECT EACH COUNTY SHAPE
        for county_masked in shapes:
            county_fip = COUNTY_FIPS[x]
            #af.maskByShapefileAndStore(LSTFiles[i],qualityFiles[i], BAFileName, BAQAFileName, county_masked)
            af.maskByShapefileAndStore(LSTFiles[i],qualityFiles[i], county_masked)
            ###--------------------------------------------------------------------------###
            ###    OPEN ALL 4 temporary files created get Quality data and mask by BA    ###
            ###--------------------------------------------------------------------------###
            ##--------------------------------------------------------------------------
            os.chdir(af.out_dir)                                                    # out_dir is where output from last step is
            LST         = gdal.Open(af.LST_temp)                                      # Read LST temporary file for current county in the loop
            LSTBand     = LST.GetRasterBand(1)                                        # Read the band (layer)
            LSTData     = LSTBand.ReadAsArray().astype('float')                       # Import band as an array with type float
            ##--------------------------------------------------------------------------
            LSTquality     = gdal.Open(af.LSTQA_temp)                                 # Open temporary LST quality file
            LSTqualityData = LSTquality.GetRasterBand(1).ReadAsArray()                # Read in as an array
            LSTquality     = None 
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
            LSTScaled    = af.get_scaled_df(LSTBand,LSTData,LSTscaleFactor)              # Apply the scale factor using simple multiplication
            LST          = None                                                       # Close the GeoTIFF file
            #----- MASK AND GET MEAN VALUE -----#
        #    BA_masked   = np.ma.MaskedArray(BAScaled, np.in1d(BAqualityData, BAgoodQuality, invert = True))                 # Apply QA mask to the BA data
            LST_masked   = np.ma.MaskedArray(LSTScaled, np.in1d(LSTqualityData, img_good_quality, invert = True))           # Apply QA mask to the LST data
            
        #    BA_resampled = scipy.ndimage.zoom(BA_masked, 0.5, order=0)                                                      # Resample by a factor of 2 with nearest neighbor interpolation
            #print("BA_masked: {}    ---- LST_Masked: {} ".format(np.mean(BA_resampled.max()), np.mean(LST_masked.compressed())))
            
        #    if (LST_masked.shape[1] != BA_resampled.shape[1]):  # Remove extra column if exists
        #        LST_masked = np.delete(LST_masked, -1, axis=1)
        #    if (LST_masked.shape[0] != BA_resampled.shape[0]):  # Remove extra row if exists
        #        LST_masked = np.delete(LST_masked, 0, 0)
                
        #    LST_BA      = np.ma.MaskedArray(LST_masked, np.in1d(BA_resampled, BAVal, invert = True))                 # Mask array, include only BurnArea
        #    LST_mean    = np.mean(LST_BA.compressed())
            LST_mean    = np.mean(LST_masked.compressed())
            print("Date: {}    -   LST_Mean: {} ".format(LSTdate,LST_mean))
            LST_result.append([LSTdate,LST_mean, county_fip])
            x = x +1
 
        #print running time    
        currentTime = timer() - start                                                                               # calculate current running time
        print('index: {}  --- FileName: {}   ---- Time Elapsed: {}  seconds'.format(i, LSTFiles[i], round(currentTime,1)))

    # add header to output dataframe 
    result_df = pd.DataFrame(LST_result, columns=["Date","LST","County_FIP"])
    
    #reformat date
    result_df['Date'] = pd.to_datetime(result_df['Date'], format='%m/%d/%Y')

    #sort values by county fip, then by date
    result_df = result_df.sort_values(["County_FIP", "Date"], ascending=(True, True))

    #change to output directory
    os.chdir(af.out_dir)

    # Export statistics to CSV
    result_df.to_csv('LST2019_2020.csv', index = False)

# monthly
if __name__ == "__main__": # helps with "prototyping/forward declaring" functions
    # execute only if run as a script
    main()