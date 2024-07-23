#!/usr/bin/env python3

# Here, we start with the lesion mask warped into each of the control image spaces. For each control image, we have a tractogram file (.trk) precomputed. We take the tractogram file, and filter it to include only streamlines which pass through the lesion mask. This filtered tractogram is then converted to a "visitation map". A visitation map is a NIFTI file in the same space as the control image, in which the value of each voxel represents the number of streamlines passing through the voxel which also pass through a lesion voxel. 

# The following code generates a visitation map for a single (lesion mask, control image) pair. For each lesion mask, this procedure needs to be performed for each of the control images. I.e. the real code will need to loop over all the control images, get the lesion mask warped to the control image space, get the control subject tractogram, then save a visitation map specific to that (lesion mask, control image) pair. 

import os
import sys
import argparse

import nibabel as nib
from dipy.io.streamline import load_trk, save_trk
from dipy.tracking.streamline import Streamlines
from dipy.tracking.utils import target, density_map
#import numpy as np

from dipy.io.stateful_tractogram import StatefulTractogram, Space

lesion_path='/arc/burst/st-smiller6-1/users/sufkes/disconnectome_dhcp/test/filter_tractogram/lesion-bc040068_both-sub-CC00073XX08_ses-27800.nii.gz'
tract_path='/arc/burst/st-smiller6-1/users/sufkes/disconnectome_dhcp/test/filter_tractogram/sub-CC00073XX08_ses-27800_hardi.trk'
visitation_map_out_path='/arc/burst/st-smiller6-1/users/sufkes/disconnectome_dhcp/test/filter_tractogram/visitation_map-bc040068_both-sub-CC00073XX08_ses-27800-dipy.nii.gz'

# Load tractogram
tractogram_file = tract_path
tractogram = load_trk(tractogram_file, reference='same')  # 'same' ensures the affine of the tractogram is used
streamlines = tractogram.streamlines

# Load lesion ROI
roi_file = lesion_path
roi_img = nib.load(roi_file)
roi_data = roi_img.get_fdata()
roi_affine = roi_img.affine

# Filter the streamlines to include only those streamlines passing through the lesion ROI.
filtered_streamlines_generator = target(streamlines, affine=roi_affine, target_mask=roi_data) # this is a streamlines generator, and putting it directly into dipy.tracking.utils.density_map is bugged. 
filtered_stateful_tractogram = StatefulTractogram(filtered_streamlines_generator, roi_img, Space.RASMM) # this step should not be necessary but is a quick solution to the generator bug. 
filtered_streamlines = filtered_stateful_tractogram.streamlines # same type as the unfiltered streamlines; no bugs

# Create visitation map
visitation_map_array = density_map(filtered_streamlines, affine=roi_affine, vol_dims=roi_img.shape)
visitation_map_array = visitation_map_array.astype(float) # nibabel doesn't like integers, so convert to floats. This is likely the issue underlying the bug which prevents filtered_streamlines_generator from being passed directly into dipy.tracking.utils.density_map
visitation_map_img = nib.Nifti1Image(visitation_map_array, roi_affine)
nib.save(visitation_map_img, visitation_map_out_path) # save NIFTI
