# Beat the Heat
is a computer science senior design project that uses machine learning to predict fire incidents based on sattelite data and past fire records. This is an accompanying repository to the main repo https://github.com/KayleePham/Beat-the-Heat--Machine-Learning, where one can find all of the code related to machine learning and various aspects of the project not related to preprocessing the datasets. 

# The purpose
of this repo is to include all that's needed to process our datasets including the geotiff images. Some features in this repo that you won't find in the origional are methods that break down geotiff images of California into counties before processing, which was done in hopes to increase accuracy of ML models. Counties were selected over finer spatial resolution areas such as per 500m/1km grid cells because in the final dataset because the data is being classified into fire or no fire categories via CA fire incident record of which the smallest spatial resolution was at the county level (see combining_datasets/mapdataall.csv for more details).

## Dependancies/Running instructions
MacOS users may not be able to download dependant software such as GDAL or Rasterio as there are known issues. Windows 10 and Anaconda package manager was used by all members in the project. There are a number of dependancies in this project related to interpretering and analyzing sattelite image files. Anaconda and Pip may be used to install the libaries, however if that does not work as was the case for many of us, we recommend downloading the windows binary version of each library (https://www.lfd.uci.edu/~gohlke/pythonlibs/) and installed using Anaconda Powershell as described in this helpful video (https://www.youtube.com/watch?v=LNPETGKAe0c).

 The project is dependant on the following software: 
* Python 3.8.3
* GDAL
* Rasterio
* Fiona



#### The senior design project is for California State University Northridge (CSUN). Group members include: Kaylee Pham, David Shin, Saulo Rubio, Tyler Poplawski, Sergio Ramirez, and David Macoto Ward.
