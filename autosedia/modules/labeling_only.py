# This software was created as a general purpose automatic image
# analysis tool and is currently being deveopled. 
# At this moment, it's sole function is to overlay 
# two images, segment the features, and caculate the area overlap.
# See the images included in 'Images' directory for an example
# of the type of images this script will work on.

"""
Auto-processor for dual images.\n
How to run script:
Place your images in the 'Images' directory.
Make sure the file format is as follows: mask01.tiff, target01.tiff
for one set, mask02.tiff, target02.tiff for the second set, etc...
use option -I #_OF_IMAGES for total number of images you want 
to run and analyze at one time. See --help for more options.
"""

__version__ = "0.1.0"

__author__ = ["Mitchell Taylor"]


import os
import sys
import math
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import numpy.fft as fft
from scipy.ndimage import fourier_gaussian, laplace, distance_transform_edt, maximum_filter
import pandas as pd
from skimage.measure import regionprops_table, label, regionprops
from skimage import morphology
import cv2
import matplotlib.patches as mpatches
from skimage.segmentation import clear_border, watershed
from skimage.morphology import area_closing
from skimage.feature import peak_local_max
from scipy import signal
import torch
from scipy import ndimage as ndi # for remove_large_objects function
from datetime import datetime # for naming outputfiles directory with current time/date


def img_label(thresh1, intensity_image, directory):

	img_binary = thresh1.copy()
	img_binary[img_binary <= 0] = 0 
	img_binary[img_binary > 0] = 1

	img_label = label(img_binary)
	#img_label = morphology.remove_small_objects(img_label, 5)

	return img_label, img_binary


class SVT():
	def mask(self, mask_raw, mask_binary, bgs, sigma, directory, idd):

		labeled, img_binary = img_label(mask_binary, mask_raw, directory)

		# Creating plots 
		px = 1/plt.rcParams['figure.dpi']  # pixel in inches
		fig, ax = plt.subplots(figsize=(2070*px, 1548*px))
		ax.imshow(mask_raw, cmap='gray') #fig dpi = 96
		for region in regionprops(labeled):
		#take regions with large enough areas
			if region.area <= 20000:
				#draw rectangle around segmented blobs
				minr, minc, maxr, maxc = region.bbox
				rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
										fill=False, edgecolor='red', linewidth=2)
				ax.add_patch(rect)

		ax.set_axis_off()
		plt.tight_layout()
		plt.savefig(directory+'/mask0'+str(idd)+'_Overlay.png')
		plt.close()
		return labeled, img_binary

	def target(self, target_raw, target_binary, bgs, sigma, directory, idd):

		targetlabeled, img_binary = img_label(target_binary, target_raw, directory)

		# Creating plots
		px = 1/plt.rcParams['figure.dpi']  # pixel in inches
		fig, ax = plt.subplots(figsize=(2070*px, 1548*px))
		ax.imshow(target_raw, cmap='gray') #fig dpi = 96

		for region in regionprops(targetlabeled):
		#take regions with large enough areas
			if region.area <= 20000:
				#draw rectangle around segmented blobs
				minr, minc, maxr, maxc = region.bbox
				rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
										fill=False, edgecolor='yellow', linewidth=2)
				ax.add_patch(rect)

		ax.set_axis_off()
		plt.tight_layout()
		plt.savefig(directory+'/target0'+str(idd)+'_Overlay.png')
		plt.close()
		return targetlabeled, img_binary


	def overlay(self, target_raw, masklabeled, targetlabeled, directory, idd):
		#Overlay of mask and target labels
		px = 1/plt.rcParams['figure.dpi']  # pixel in inches
		fig, ax = plt.subplots(figsize=(1920*px, 1460*px))
		ax.imshow(target_raw, cmap='gray') #fig dpi = 96

		for region in regionprops(masklabeled):
			# take regions with large enough areas
			if region.area <= 8000:
				# draw rectangle around segmented blobs
				minr, minc, maxr, maxc = region.bbox
				rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
									  fill=False, edgecolor='red', linewidth=2)
				ax.add_patch(rect)

		for region in regionprops(targetlabeled):
			# take regions with large enough areas
			if region.area <= 8000:
				# draw rectangle around segmented blobs
				minr, minc, maxr, maxc = region.bbox
				rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
									  fill=False, edgecolor='yellow', linewidth=2)
				ax.add_patch(rect)	

		ax.set_axis_off()
		plt.tight_layout()
		plt.savefig(directory+'/Pair0'+str(idd)+'_Overlay.png')
		plt.close()

	def data(self, mask_raw, target_raw, labelmask, labeltarget, img_binary, directory, idd, thresh = 0.05):
		# Create datafiles
		maskdata = pd.DataFrame(regionprops_table(label_image=labelmask,
					intensity_image=mask_raw, properties=('label', 'area', 'mean_intensity', 'weighted_centroid')))

		maskdata['SBR'] = regionprops_table(label_image=labelmask,
					intensity_image=mask_raw, properties=('label', 'mean_intensity'))["mean_intensity"]

		targetdata = pd.DataFrame(regionprops_table(label_image=labeltarget,
					intensity_image=target_raw, properties=('label', 'area', 'mean_intensity', 'weighted_centroid')))

		targetdata['SBR'] = regionprops_table(label_image=labeltarget,
					intensity_image=target_raw, properties=('label', 'mean_intensity'))["mean_intensity"]


		data = pd.DataFrame(regionprops_table(label_image=labelmask,
					intensity_image=mask_raw, properties=('label', 'area', 'mean_intensity', 'weighted_centroid')))

		data["target_intensity"] = regionprops_table(label_image=labelmask,
					intensity_image=target_raw, properties=('label', 'mean_intensity'))["mean_intensity"]

		data['SBR'] = regionprops_table(label_image=labelmask,
					intensity_image=target_raw, properties=('label', 'mean_intensity'))["mean_intensity"]

		data["size_fraction"] = regionprops_table(label_image=labelmask,
					intensity_image=img_binary, properties=('label', 'mean_intensity'))["mean_intensity"]

		data["expressed"] = data.size_fraction.values > thresh
		expressed_sum = sum((data['expressed'] == True))

		expressed_target = data.loc[data['expressed'] == True]
		unexpressed_target = data.loc[data['expressed'] == False]

		maskdata.to_csv(directory + "/maskdata0"+str(idd)+".csv")
		targetdata.to_csv(directory + "/targetdata0"+str(idd)+".csv")
		data.to_csv(directory + "/data0"+str(idd)+".csv")

		self.data = data
		self.maskdata = maskdata
		self.targetdata = targetdata
		self.expressed_sum = expressed_sum
		self.expressed_target = expressed_target
		self.unexpressed_target = unexpressed_target

		return self.data, self.maskdata, self.targetdata, self.expressed_sum, self.expressed_target, self.unexpressed_target


	def histo(self, expressed_target, unexpressed_target, num_markers, directory, idd):
		# Create histograms
		if idd == 10:
			idd = 'Final'

		sigma = np.std(expressed_target)
		mu = np.mean(expressed_target)

		sigma2 = (np.std(unexpressed_target))
		mu2 = np.mean(unexpressed_target)
		
		num_bins = np.linspace(1, math.ceil(max(max(expressed_target['SBR']),max(unexpressed_target['SBR']))), 
				round(num_markers))#/10)*10) # round number objects to nearths tens and right interval up to nearest int

		#num_bins = np.linspace(1,10,50)

		fig, ax = plt.subplots(figsize=(15,10))

		# Histogram of the data
		n, bins, patches = ax.hist((expressed_target['SBR']), num_bins, density=True)

		n2, bins2, patches2 = ax.hist((unexpressed_target['SBR']), num_bins, density=True, alpha = 0.5)


		ax.spines['top'].set_visible(False)
		ax.spines['right'].set_visible(False)

		ax.set_xlabel("SBR Intensity",fontsize=35, labelpad=20)
		ax.set_ylabel("Density",fontsize=35,labelpad=20)

		plt.xticks(fontsize=30)
		plt.yticks(fontsize=30)
		plt.minorticks_on()

		# Tweak spacing to prevent clipping of ylabel
		plt.tight_layout()
		fig.savefig(directory + '/histo' + str(idd) + '.jpg')
		plt.close()

def main():
	import argparse
	from argparse import RawTextHelpFormatter

	directory = os.getcwd()
	current_datetime = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
	binary_directory = directory + '/data/Preprocessed_Images'
	image_directory = directory+'/data/PreProcessed_Raw_Images'
	num_images = int(len([entry for entry in os.listdir(image_directory) if os.path.isfile(os.path.join(image_directory, entry))])/2) # counts number of images
	output_parentDirectory = directory+'/data/OutputFiles'
	output_childDirectory = directory+'/data/OutputFiles/'+str(current_datetime)

	try:
		os.mkdir(output_childDirectory)
	except FileExistsError:
		print("\n The OutputFiles directory already exists! Please move it so overwritting",
		"does not occur\n")
		sys.exit(1)

	ap = argparse.ArgumentParser(
		description=__doc__, formatter_class=RawTextHelpFormatter
	)

	ap.add_argument(
		"--img_dir",
		default=image_directory,
		help="Directory where images are located",
		)
	ap.add_argument(
		"-V",
		"--version",
		action="version",
		version="%(prog)s {}".format(__version__),
		help="Prints the version, then exits script",
		)
	ap.add_argument(
		"-DS",
		"--dsigma",
		type=int,
		default=5,
		help="Specifies sigma value for dark-field fourier-gaussian filter - default=5"
		)
	ap.add_argument(
		"-FS",
		"--fsigma",
		type=int,
		default=5,
		help="Specifies sigma value for fluorescence fourier-gaussian filter - default=5"
		)
	ap.add_argument(
		"-DB",
		"--targetbackground",
		type=int,
		default=5,
		help="Specifies sigma value for dark-field background - default=5"
		)
	ap.add_argument(
		"-FB",
		"--maskbackground",
		type=int,
		default=5,
		help="Specifies sigma value for fluorescence background - default=5"
		)
	ap.add_argument(
		"-I",
		"--images",
		type=int,
		default=num_images,
		help="Number of image PAIRS to analyze - default=1"
		)
	ap.add_argument(
		"-M",
		"--manual",
		action='store_true',
		help="Enter each argument manually for each image pair"
		)

	cmd = ap.parse_args()

	print("\n[+] Analysis Starting...\n")

	results_complete = None
	expressed_target_combined = None
	unexpressed_target_combined = None
	for i in range(cmd.images):
		output_directory = output_childDirectory+'/ImageSet'+str(i+1)
		os.mkdir(output_directory)
		if cmd.manual == True and cmd.images >= 2:
			end = 0
			while end == 0:
				print('\nImage Set #'+str(i+1))
				try:
					userInput = int(input('select a number for which option you want to set:\n'
						'1) FB\n2) FS\n3) DB\n4) DS\n5) accept and continue '))
					if userInput == 1:
						fb_input = int(input('Enter a integer between 1 and 50 '))
						cmd.maskbackground = fb_input
					elif userInput == 2:
						fs_input = int(input('Enter a integer between 1 and 50 '))
						cmd.fsigma = fs_input
					elif userInput == 3:
						db_input = int(input('Enter a integer between 1 and 50 '))
						cmd.targetbackground = db_input
					elif userInput == 4:
						ds_input = int(input('Enter a integer between 1 and 50 '))
						cmd.dsigma = ds_input
					elif userInput == 5:
						print('\n\nNow analyzing Image Set #'+str(i+1)+'...')
						end = 1
				except ValueError:
					print("\n\nNOT A VALID INPUT.\nPlease enter an integer between 1 and 50")
					pass

		elif cmd.manual == True and cmd.images == 1:
			print('(There is no need to use the manual option with only one image pair. Simply set the arguments,',
			'from the command line when running script).\n\n',
			'Continuing script...')

		idd = i + 1 

		image_params = [cmd.maskbackground, cmd.targetbackground, cmd.fsigma, cmd.dsigma]
		image_params = pd.DataFrame(np.array(image_params)).T
		image_params.columns = ['mask Background', 'target Background', 'mask Sigma', 'target Sigma']
		image_params.to_csv(output_directory + "/image_params0"+str(idd)+".csv")

		svt = SVT()
		mask_image = np.asarray(Image.open(image_directory+'/mask0' + str(idd) + '.tif'))
		mask_binary = np.asarray(Image.open(binary_directory+'/maskbinary0' + str(idd) + '.tif'))
		labelmask, img_binarymask = svt.mask(mask_image, mask_binary, cmd.maskbackground, cmd.fsigma, output_directory, idd)

		target_image = np.asarray(Image.open(image_directory+'/target0' + str(idd) + '.tif'))
		target_binary = np.asarray(Image.open(binary_directory+'/targetbinary0' + str(idd) + '.tif'))
		labeltarget, img_binarytarget = svt.target(target_image, target_binary, cmd.targetbackground, cmd.dsigma, output_directory, idd)

		svt.overlay(target_image, labelmask, labeltarget, output_directory, idd)
		svt.data(mask_image, target_image, labelmask, labeltarget, img_binarytarget, output_directory, idd)

		n_vesicles = svt.maskdata.shape[0]
		n_markers = svt.targetdata.shape[0]
		expressed_total = svt.expressed_sum
		frac_positive = expressed_total/n_vesicles
		n_false_markers = n_markers - expressed_total

		hist = svt.histo(svt.expressed_target, svt.unexpressed_target, n_markers,  output_directory, idd)

		results = pd.DataFrame(np.array([n_vesicles, n_markers, expressed_total, frac_positive, n_false_markers])).T
		results.columns = ['n_vesicles', 'n_markers', 'expressed_total', '%total_positive', 'n_false_markers']


		# final results
		if isinstance(results_complete, pd.DataFrame):
			results_complete = pd.concat([results_complete, results])
		else:
			results_complete = results

		# final histogram expressed_target data
		if isinstance(expressed_target_combined, pd.DataFrame):
			expressed_target_combined = pd.concat([expressed_target_combined, svt.expressed_target])
		else:
			expressed_target_combined = svt.expressed_target

		# final histogram unexpressed_target data
		if isinstance(unexpressed_target_combined, pd.DataFrame):
			unexpressed_target_combined = pd.concat([unexpressed_target_combined, svt.unexpressed_target])
		else:
			unexpressed_target_combined = svt.unexpressed_target

		print('\n[+] Image Set #'+str(idd), 'done.\n')

	results_complete = results_complete.reset_index()
	results_complete.to_csv(output_directory + "/results.csv")

	total_expressed = sum(results_complete['expressed_total'].values)\
									/sum(results_complete['n_vesicles'].values)*100

	final_hist = svt.histo(expressed_target_combined, unexpressed_target_combined, 
									sum(results_complete['n_vesicles'].values),  output_directory, 10)


	print("\n[+] Results:")
	print(f"	Total # of vesicles = {sum(results_complete['n_vesicles'].values)}\n"
		f"	Total # of markers = {sum(results_complete['n_markers'].values)}\n"
		f"	Total # of marker positive vesicles (expressed) = {sum(results_complete['expressed_total'].values)}\n"
		f"	Total % of expressed vesicles = {round(total_expressed,3)}%\n")


if __name__ == '__main__':
	import time
	start = time.perf_counter()
	time.sleep(1)
	main()
	end = time.perf_counter()
	print(f"\n[+] Analysis complete. Main function execution time: {end-start:.03f} seconds",
	   '\n\n[+] See output directory for output files',
	   '\n\n[+] Please report any errors seen while running script to the maintainer!\n')
