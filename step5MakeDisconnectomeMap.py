#!/usr/bin/env python

## Generate the "disconnetome map". To generate it, we take each of the visitation maps in 40-week template space, binarize them, then compute the average. Finally, we threshold this average image to obtain the final disconnectome map.

import os
import sys
import argparse

import numpy as np
import nibabel as nib

from constants import RUNS_DIR

def makeDisconnectomeMap(in_paths, out_path, threshold):

    first_iteration = True
    for in_path in in_paths:
        vis_nii = nib.load(in_path) # load visitation map NIFTI file
        vis_arr = vis_nii.get_fdata()  # load visition map array data

        vis_arr[vis_arr > 0] = 1 # binarize the visitation map (set all positive values to 1)

        # Compute the sum of the binarized visitation maps.
        if first_iteration:
            dis_arr = vis_arr.copy()
            dis_affine = vis_nii.affine # record the NIFTI affine from one of the visitation maps, which we will need to build the output disconnectome NIFTI file.
            dis_header = vis_nii.header # record the NIFTI header from one of the visitation maps, which we will need to build the output disconnectome NIFTI file.
            first_iteration = False
        else:
            dis_arr += vis_arr


    # Convert the sum of visitations to the frequency of visitations (i.e. the average of the binarized visitation maps)
    num_controls = len(in_paths)
    dis_arr = dis_arr/num_controls

    # Threshold the disconnectome map.
    dis_arr[dis_arr < threshold] = 0

    # Convert disconnectome array to a NIFTI object.
    dis_nii = nib.nifti1.Nifti1Image(dis_arr, dis_affine, header=dis_header)

    # Save the disconnectome map.
    nib.save(dis_nii, out_path)

    return

def main(subject, threshold = 0):
  runs_path = RUNS_DIR / subject
  runs_visitation_maps_40w_path = runs_path / 'visitation_maps_40w'

  dir_list = [
    f.name for f in os.scandir(runs_visitation_maps_40w_path) if f.is_dir()
  ]
  print(f"dir_list is: {dir_list}")

  in_paths = []

  for d in dir_list:
    print(f"directory is: {d}")
    path = runs_visitation_maps_40w_path / d
    in_paths += [os.path.join(path, 'visitation_map.nii.gz')]

  print(f"in_paths is: {in_paths}")
  try:
    disconnectome_out_dir = runs_path / 'disconnectome'
    disconnectome_out_dir.mkdir(parents=True, exist_ok=False)
  except FileExistsError:
      print("Folder is already there")
  else:
      print("Folder was created")

  out_path = os.path.join(disconnectome_out_dir, 'disconnectome-threshold_' + str(threshold) + '.nii.gz')
  print(f"out_path is: {out_path}")
  makeDisconnectomeMap(in_paths, out_path, 0)


## Pseudo code
# Generate a list of the visitation maps for each control image warped into the 40 week template space.
#in_paths = [visitiation map for control 1, visitation map for control 2, ...]

# Set path to output disconnectome image.
#out_path = < ... > # e.g. 'runs/bc040031_wmi/disconnectome/disconnectome.nii.gz'

# Choose a threshold. Values below this threshold will be set to zero in the output disconnectome image. For now, we can just set this value to 0, meaning that the thresholding operation will do nothing. Later, we may want to allow the threshold value to be selected by the user, or perhaps hard-code it to some specific values (e.g. 0, 0.5).
#threshold = 0

# Run the function.
#makeDisconnectomeMap(in_paths, out_path, threshold)
