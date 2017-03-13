import scipy.io
from scipy.io import savemat
from scipy.sparse import csr_matrix
import numpy as np
from osgeo import gdal, osr, ogr, gdalnumeric
import argparse
import json
import re
from os import listdir

from label_functions2 import CreateClassSegmentation, CreateClassBoundaries, CreateClassCategoriesPresent, CreateInstanceSegmentation, CreateInstanceBoundaries, CreateInstanceCategories

parser = argparse.ArgumentParser()
parser.add_argument("raster_dir", help="directory for raster source")
parser.add_argument("vector_dir", help="directory for geojson source")
parser.add_argument("cls_dir", help="directory for cls files")
parser.add_argument("inst_dir", help="directory for inst files")

args = parser.parse_args()

my_raster_dir = args.raster_dir
my_vector_dir = args.vector_dir
my_cls_dir = args.cls_dir
my_inst_dir = args.inst_dir


#Loop through raster directory
for raster_file in listdir(my_raster_dir):

	#Print raster file name
	my_raster_source = raster_file
	print("Raster directory : ",my_raster_dir+'/'+my_raster_source)

	#Get image number
	image_number_search = re.search('(?<=img)\w+', raster_file)
	image_number = image_number_search.group(0)

	
	my_vector_source = 'Geo_AOI_1_RIO_img'+str(image_number)+'.geojson'
	print("Vector directory : ",my_vector_dir+'/'+my_vector_source)

	
	#Call main functions to create label datafor cls
	my_cls_segmentation = CreateClassSegmentation(my_raster_dir+'/'+my_raster_source, my_vector_dir+'/'+my_vector_source, npDistFileName='', units='pixels')
	my_cls_boundaries =  CreateClassBoundaries(my_raster_dir+'/'+my_raster_source, my_vector_dir+'/'+my_vector_source, npDistFileName='', units='pixels')
	my_cls_categories = CreateClassCategoriesPresent(my_vector_dir+'/'+my_vector_source)

	#Call main functions to create label datafor inst
	my_inst_segmentation = CreateInstanceSegmentation(my_raster_dir+'/'+my_raster_source, my_vector_dir+'/'+my_vector_source)
	my_inst_boundaries = CreateInstanceBoundaries(my_raster_dir+'/'+my_raster_source, my_vector_dir+'/'+my_vector_source)
	my_inst_categories = CreateInstanceCategories(my_vector_dir+'/'+my_vector_source)

	#Wraps for cls struct
	cls_boundaries_wrap = np.array([my_cls_boundaries])
	cls_categories_wrap = my_cls_categories

	#Wraps for inst struct
	inst_boundaries_wrap = np.array([my_inst_boundaries])
	inst_categories_wrap = my_inst_categories

	#Create a class struct
	GTcls = {'Segmentation': my_cls_segmentation , 'Boundaries': cls_boundaries_wrap, 'CategoriesPresent': cls_categories_wrap}


	#Create the instance struct
	GTinst = {'Segmentation': my_inst_segmentation , 'Boundaries': inst_boundaries_wrap, 'Categories': inst_categories_wrap}

	#Save the files
	scipy.io.savemat(my_cls_dir+'/'+'3band_AOI_1_RIO_img'+str(image_number)+'.mat',{'GTcls': GTcls})
	scipy.io.savemat(my_inst_dir+'/'+'3band_AOI_1_RIO_img'+str(image_number)+'.mat',{'GTinst': GTinst})

	print("Done with "+str(image_number))

print("Done with directory!!")
