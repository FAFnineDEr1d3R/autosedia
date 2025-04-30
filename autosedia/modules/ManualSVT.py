from skimage.measure import regionprops_table, label, regionprops
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np
import math


class ManualSVT():
	def manual_img_label(self, thresh1, intensity_image, directory):

		img_binary = thresh1.copy()
		img_binary[img_binary <= 0] = 0 
		img_binary[img_binary > 0] = 1

		img_label = label(img_binary)
		#img_label = morphology.remove_small_objects(img_label, 5)

		return img_label, img_binary
	
	def mask(self, mask_raw, mask_binary, bgs, sigma, directory, idd):

		labeled, img_binary = self.manual_img_label(mask_binary, mask_raw, directory)

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

		targetlabeled, img_binary = self.manual_img_label(target_binary, target_raw, directory)

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

		data["target_log_intensity"] = np.log(data.target_intensity.values)

		data['SBR'] = regionprops_table(label_image=labelmask,
					intensity_image=target_raw, properties=('label', 'mean_intensity'))["mean_intensity"]

		data["size_fraction"] = regionprops_table(label_image=labelmask,
					intensity_image=img_binary, properties=('label', 'mean_intensity'))["mean_intensity"]

		data["expressed"] = data.size_fraction.values > thresh
		expressed_sum = sum((data['expressed'] == True))

		expressed_target = pd.DataFrame(data.loc[data['expressed'] == True])
		unexpressed_target = pd.DataFrame(data.loc[data['expressed'] == False])

		#mu1 = np.mean(expressed_target.target_log_intensity.values)
		mu2 = np.mean(unexpressed_target.target_log_intensity.values)
		min_value = data['target_log_intensity'].min()
		expressed_target["normalized_target_log_intensity"] = (expressed_target["target_log_intensity"] / min_value) -1
		unexpressed_target["normalized_target_log_intensity"] = (unexpressed_target["target_log_intensity"] / mu2) -1

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
		
		num_bins = np.linspace(0, math.ceil(max(max(expressed_target['normalized_target_log_intensity']),max(unexpressed_target['normalized_target_log_intensity']))), 
				round(num_markers))#/10)*10) # round number objects to nearths tens and right interval up to nearest int

		num_bins = np.linspace(0,10,50)

		fig, ax = plt.subplots(figsize=(15,10))

		# Histogram of the data
		n, bins, patches = ax.hist((expressed_target['normalized_target_log_intensity']), num_bins, density=False)

		n2, bins2, patches2 = ax.hist((unexpressed_target['normalized_target_log_intensity']), num_bins, density=False, alpha = 0.5)


		ax.spines['top'].set_visible(False)
		ax.spines['right'].set_visible(False)

		ax.set_xlabel("Log Intensity",fontsize=35, labelpad=20)
		ax.set_ylabel("Density",fontsize=35,labelpad=20)

		plt.xticks(fontsize=30)
		plt.yticks(fontsize=30)
		plt.minorticks_on()

		# Tweak spacing to prevent clipping of ylabel
		plt.tight_layout()
		fig.savefig(directory + '/histo' + str(idd) + '.jpg')
		plt.close()