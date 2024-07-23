#!/usr/bin/env python3

## Here, we warp the visition maps in each of the control image spaces back into the 40W template space. This requires only a single transform which is precomputed (included in the toolkit).

## Pseudo code
# for visitation map in each control image space:
#   fixed_path = <path to 40W template>
#   moving_path = <path to visitation map in control image space>
#   out_path = <output path for visitation map corresponding to the input lesion map and a specific control image, now in 40W template space> # e.g. 'runs/bc040045_wmi/visitation_maps_40w/sub-CC00217XX11_ses-73700/visitation_map.nii.gz'
#   transformlist = [<path to control-to-40W_template warp file in ANTs format>] # e.g. ['controls/sub-CC00425XX13/ses-129800/xfm-ants/sub-CC00425XX13_ses-129800_from-dwi_to-extdhcp40wk_mode-image.nii.gz']
#
#   # Open the image as an ANTS object
#   fixed_img = ants.read_image(fixed_path)
#   moving_img = ants.read_image(moving_path)
#
#   # Apply the transform and save the image.
#   lesion_in_40w_template_space = ants.apply_transforms(fixed=fixed_img, moving=moving_img, transformlist=transformlist)
#   ants.image_write(lesion_in_40W_template_space, <out_path>)
