import scipy.io
from scipy.io import savemat
from scipy.sparse import csr_matrix
import numpy as np
from osgeo import gdal, osr, ogr, gdalnumeric
import ogr
import argparse
import json


#David Lindenbaums distance transform
def DistanceTransform(rasterSrc, vectorSrc, npDistFileName='', units='pixels'):

    ## open source vector file that truth data
    source_ds = ogr.Open(vectorSrc)
    source_layer = source_ds.GetLayer()

    ## extract data from src Raster File to be emulated
    ## open raster file that is to be emulated
    srcRas_ds = gdal.Open(rasterSrc)
    cols = srcRas_ds.RasterXSize
    rows = srcRas_ds.RasterYSize
    noDataValue = 0

    if units=='meters':
        geoTrans, poly, ulX, ulY, lrX, lrY = gT.getRasterExtent(srcRas_ds)
        transform_WGS84_To_UTM, transform_UTM_To_WGS84, utm_cs = gT.createUTMTransform(poly)
        line = ogr.Geometry(ogr.wkbLineString)
        line.AddPoint(geoTrans[0], geoTrans[3])
        line.AddPoint(geoTrans[0]+geoTrans[1], geoTrans[3])

        line.Transform(transform_WGS84_To_UTM)
        metersIndex = line.Length()
    else:
        metersIndex = 1

    ## create First raster memory layer
    memdrv = gdal.GetDriverByName('MEM')
    dst_ds = memdrv.Create('', cols, rows, 1, gdal.GDT_Byte)
    dst_ds.SetGeoTransform(srcRas_ds.GetGeoTransform())
    dst_ds.SetProjection(srcRas_ds.GetProjection())
    band = dst_ds.GetRasterBand(1)
    band.SetNoDataValue(noDataValue)

    gdal.RasterizeLayer(dst_ds, [1], source_layer, burn_values=[255])
    srcBand = dst_ds.GetRasterBand(1)

    memdrv2 = gdal.GetDriverByName('MEM')
    prox_ds = memdrv2.Create('', cols, rows, 1, gdal.GDT_Int16)
    prox_ds.SetGeoTransform(srcRas_ds.GetGeoTransform())
    prox_ds.SetProjection(srcRas_ds.GetProjection())
    proxBand = prox_ds.GetRasterBand(1)
    proxBand.SetNoDataValue(noDataValue)
    options = ['NODATA=0']
    
    ##compute distance to non-zero pixel values and scrBand and store in proxBand
    gdal.ComputeProximity(srcBand, proxBand, options)

    memdrv3 = gdal.GetDriverByName('MEM')
    proxIn_ds = memdrv3.Create('', cols, rows, 1, gdal.GDT_Int16)
    proxIn_ds.SetGeoTransform(srcRas_ds.GetGeoTransform())
    proxIn_ds.SetProjection(srcRas_ds.GetProjection())
    proxInBand = proxIn_ds.GetRasterBand(1)
    proxInBand.SetNoDataValue(noDataValue)
    options = ['NODATA=0', 'VALUES=0']
    
    ##compute distance to zero pixel values and scrBand and store in proxInBand
    gdal.ComputeProximity(srcBand, proxInBand, options)

    proxIn = gdalnumeric.BandReadAsArray(proxInBand)
    proxOut = gdalnumeric.BandReadAsArray(proxBand)
 
    ##distance tranform is the distance to zero pixel values minus distance to non-zero pixel values
    proxTotal = proxIn.astype(float) - proxOut.astype(float)
    proxTotal = proxTotal*metersIndex

    if npDistFileName != '':
        np.save(npDistFileName, proxTotal)

    return proxTotal


def CreateClassSegmentation(rasterSrc, vectorSrc, npDistFileName='', units='pixels'):
    dist_trans = DistanceTransform(rasterSrc, vectorSrc, npDistFileName='', units='pixels')
    dist_trans[dist_trans > 0] = 1
    dist_trans[dist_trans < 0] = 0
    return dist_trans


def CreateClassBoundaries(rasterSrc, vectorSrc, npDistFileName='', units='pixels'):
    dist_trans = DistanceTransform(rasterSrc, vectorSrc, npDistFileName='', units='pixels')
    #From distance transform to boundary
    dist_trans[dist_trans > 1.0] = 255
    dist_trans[dist_trans < -1.0] = 255
    dist_trans[dist_trans != 255] = 1
    dist_trans[dist_trans == 255] = 0
    sparse_total = csr_matrix(dist_trans)
    return sparse_total.astype(np.uint8)


def CreateClassCategoriesPresent(vectorSrc):
    with open(vectorSrc) as my_file:
        data = json.load(my_file)
    if(len(data['features']) == 0):
       return np.array([],dtype=np.uint8)
    else:
       return np.array([1],dtype=np.uint8)

def DistanceTransformByFeatureIndex(feature_index, rasterSrc, vectorSrc, npDistFileName='', units='pixels'):
    ## open source vector file that truth data
    source_ds = ogr.Open(vectorSrc)
    source_layer = source_ds.GetLayer()
    
    #Define feature
    my_feature = source_layer[feature_index]
    
    #Spatial Reference
    srs = source_layer.GetSpatialRef()
    
    #Create feature Layer
    outDriver = ogr.GetDriverByName('MEMORY')
    outDataSource = outDriver.CreateDataSource('memData')
    Feature_Layer = outDataSource.CreateLayer("this_feature", srs, geom_type=ogr.wkbPolygon)
    
    #Add feature to layer
    Feature_Layer.CreateFeature(my_feature)
    

    ## extract data from src Raster File to be emulated
    ## open raster file that is to be emulated
    srcRas_ds = gdal.Open(rasterSrc)
    cols = srcRas_ds.RasterXSize
    rows = srcRas_ds.RasterYSize
    noDataValue = 0
    metersIndex = 1

    ## create First raster memory layer
    memdrv = gdal.GetDriverByName('MEM')
    dst_ds = memdrv.Create('', cols, rows, 1, gdal.GDT_Byte)
    dst_ds.SetGeoTransform(srcRas_ds.GetGeoTransform())
    dst_ds.SetProjection(srcRas_ds.GetProjection())
    band = dst_ds.GetRasterBand(1)
    band.SetNoDataValue(noDataValue)

    gdal.RasterizeLayer(dst_ds, [1], Feature_Layer, burn_values=[255])
    srcBand = dst_ds.GetRasterBand(1)

    memdrv2 = gdal.GetDriverByName('MEM')
    prox_ds = memdrv2.Create('', cols, rows, 1, gdal.GDT_Int16)
    prox_ds.SetGeoTransform(srcRas_ds.GetGeoTransform())
    prox_ds.SetProjection(srcRas_ds.GetProjection())
    proxBand = prox_ds.GetRasterBand(1)
    proxBand.SetNoDataValue(noDataValue)

    options = ['NODATA=0']

    gdal.ComputeProximity(srcBand, proxBand, options)

    memdrv3 = gdal.GetDriverByName('MEM')
    proxIn_ds = memdrv3.Create('', cols, rows, 1, gdal.GDT_Int16)
    proxIn_ds.SetGeoTransform(srcRas_ds.GetGeoTransform())
    proxIn_ds.SetProjection(srcRas_ds.GetProjection())
    proxInBand = proxIn_ds.GetRasterBand(1)
    proxInBand.SetNoDataValue(noDataValue)
    options = ['NODATA=0', 'VALUES=0']
    gdal.ComputeProximity(srcBand, proxInBand, options)

    proxIn = gdalnumeric.BandReadAsArray(proxInBand)
    proxOut = gdalnumeric.BandReadAsArray(proxBand)

    proxTotal = proxIn.astype(float) - proxOut.astype(float)
    proxTotal = proxTotal*metersIndex

    if npDistFileName != '':
        np.save(npDistFileName, proxTotal)
        
    return proxTotal

def CreateSegmentationByFeatureIndex(feature_index, rasterSrc, vectorSrc, npDistFileName='', units='pixels'):
    dist_trans_by_feature = DistanceTransformByFeatureIndex(feature_index, rasterSrc, vectorSrc, npDistFileName='', units='pixels')
    dist_trans_by_feature[dist_trans_by_feature > 0] = feature_index + 1
    dist_trans_by_feature[dist_trans_by_feature < 0] = 0  
    return dist_trans_by_feature.astype(np.uint8)

def CreateInstanceSegmentation(rasterSrc, vectorSrc):
    json_data = open(vectorSrc)
    data = json.load(json_data)
    num_features = len(data['features'])
    
    cell_array = np.zeros((num_features,), dtype=np.object)
    for i in range(num_features):
        cell_array[i] = CreateSegmentationByFeatureIndex(i, rasterSrc, vectorSrc, npDistFileName='', units='pixels')
    return cell_array

def CreateBoundariesByFeatureIndex(feature_index, rasterSrc, vectorSrc, npDistFileName='', units='pixels'):
    dist_trans_by_feature = DistanceTransformByFeatureIndex(feature_index, rasterSrc, vectorSrc, npDistFileName='', units='pixels')
    dist_trans_by_feature[dist_trans_by_feature > 1.0] = 255
    dist_trans_by_feature[dist_trans_by_feature < -1.0] = 255
    dist_trans_by_feature[dist_trans_by_feature != 255] = 1
    dist_trans_by_feature[dist_trans_by_feature == 255] = 0
    return dist_trans_by_feature.astype(np.uint8)

def CreateInstanceBoundaries(rasterSrc, vectorSrc):
    json_data = open(vectorSrc)
    data = json.load(json_data)
    num_features = len(data['features'])
    
    cell_array = np.zeros((num_features,), dtype=np.object)
    for i in range(num_features):
        full_boundary_matrix = CreateBoundariesByFeatureIndex(i, rasterSrc, vectorSrc, npDistFileName='', units='pixels')
        cell_array[i] = csr_matrix(full_boundary_matrix)
    return cell_array

def CreateInstanceCategories(vectorSrc):
    with open(vectorSrc) as my_file:
        data = json.load(my_file)
    if(len(data['features']) == 0):
       return np.array([],dtype=np.uint8)
    else:
       return np.ones(len(data['features']),dtype=np.uint8).reshape((len(data['features']), 1))

