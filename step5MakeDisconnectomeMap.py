#!/usr/bin/env python

## Generate the "disconnetome map". To generate it, we take each of the visitation maps in 40-week template space, binarize them, then compute the average. Finally, we threshold this average image to obtain the final disconnectome map.

import os
import nibabel as nib

from constants import DISCONNECTOME, VISITATION_MAPS_40W


def makeDisconnectomeMap(in_paths, out_path, threshold):
  try:
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
  except Exception as e:
     raise e
  else:
     return True

def main(runs_dir, subject, threshold = 0):
  try:
    runs_path = os.path.join(runs_dir, subject)
    runs_visitation_maps_40w_path = os.path.join(runs_path, VISITATION_MAPS_40W)

    dir_list = [
      f.name for f in os.scandir(runs_visitation_maps_40w_path) if f.is_dir()
    ]
    print(f"dir_list is: {dir_list}")

    in_paths = []

    for d in dir_list:
      print(f"directory is: {d}")
      path = os.path.join(runs_visitation_maps_40w_path, d)
      in_paths += [os.path.join(path, 'visitation_map.nii.gz')]

    print(f"in_paths is: {in_paths}")
    try:
      disconnectome_out_dir = os.path.join(runs_path, DISCONNECTOME)
      os.makedirs(disconnectome_out_dir, exist_ok=False)
    except FileExistsError:
        print("Folder is already there")
    else:
        print("Folder was created")

    out_path = os.path.join(disconnectome_out_dir, 'disconnectome-threshold_' + str(threshold) + '.nii.gz')
    print(f"out_path is: {out_path}")
    makeDisconnectomeMap(in_paths, out_path, 0)
  except Exception as e:
     print("makeDisconnectomeMap failed: ", e)
     return False
  else:
     return True
