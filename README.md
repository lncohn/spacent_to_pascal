This is a GitHub repository containing python scripts to convert labels for the 1st SpaceNet competition to labels in the the Pascal VOC SMD format.

Run the command:

python spacenet_labels_dir_to_voc_labels_dir.py raster_dir vector_dir cls_dir inst_dir 

in a directory containing a subdirectory of raster tif files, a subdirectory of vector geojson files, an empty class labels subdirectory, and another empty instance labels subdirectory.

The corresponding Pascal VOC labels will be processed and placed in the two empty class and instance directories.  This allows for segmentation algorithms developed for the Pascal VOC competition to be applied to the SpaceNet data.
