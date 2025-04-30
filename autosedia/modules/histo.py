#
# This code is part of the AutoSEDIA software suite
# used for single vesicle image analysis
#

"""
Histogram creation for total IgG signal
versus total marker positive signal
"""


def histo(self, expressed_target, unexpressed_target, num_markers, directory, idd):
	# Create histograms
	if idd == 10:
		idd = 'Final'

	#sigma = np.std(expressed_target)
	#mu = np.mean(expressed_target.target_log_intensity.values)

	#sigma2 = (np.std(unexpressed_target))
	mu2 = np.mean(unexpressed_target.target_log_intensity.values)
	
	num_bins = np.linspace(0, math.ceil(max(max(expressed_target['normalized_target_log_intensity']),max(unexpressed_target['normalized_target_log_intensity']))), 
			round(num_markers))#/10)*10) # round number objects to nearths tens and right interval up to nearest int

	#num_bins = np.linspace(1,10,50)

	fig, ax = plt.subplots(figsize=(15,10))

	# Histogram of the data
	n, bins, patches = ax.hist((expressed_target['normalized_target_log_intensity']), num_bins, density=True)

	n2, bins2, patches2 = ax.hist((unexpressed_target['normalized_target_log_intensity']), num_bins, density=True, alpha = 0.5)


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