#!/usr/bin/env python3

import os
import ants


# Here, we combine all of the warps that will bring the input lesion mask to each of the control image spaces. The chain of warps will be combined in a single step.
# The chain of warps will conist of the following:
# (subject lesion) -> (age-matched template) -> (40w template) -> (control image space)

# I still need to write this example, but here is the outline of steps:
# (1) Build up the chain of transformations, and store them in a list. They must appear in *reverse* order of application.
# transformlist = [<40w template to control image warp NIFTI path>, <age-matched template to 40w template warp NIFTI path>, <lesion mask to age-matched template warp NIFTI path>, <lesion mask to age-matched template affine path>]
# Note: Each of the transforms is stored in a single NIFTI file, except for the lesion mask -> age-matched template file, which involves an affine transformation (.mat file) followed by a nonlinear transformation (NIFTI file).

# Example for one lesion subject (e.g. CC00064XX07, whose age at scan is 38.86 weeks) and one control image (e.g. sub-CC00073XX08): 
transformlist = []
transformlist += ['<toolkit directory>/controls/sub-CC00073XX08/ses-27800/xfm-ants/sub-CC00073XX08_ses-27800_from-extdhcp40wk_to-dwi_mode-image.nii.gz'] # 40w template to control image warp NIFTI path (transform 4, precomputed)
transformlist += ['<toolkit directory>/template/warps-ants/week-39_to_week-40_warp.nii.gz'] # age-matched template to 40w template warp NIFTI path (transform 3, precomputed)
transformlist += ['<toolkit directory>/runs/CC00064XX07/template_space/39w/<prefix>-1Warp.nii.gz'] # lesion mask to age-matched template warp NIFTI path (transform 2, computed in previous step)
transformlist += ['<toolkit directory>/runs/CC00064XX07/template_space/39w/<prefix>-0GenericAffine.mat'] # lesion mask to age-matched template affine path (transform 1, computed in previous step)


# (2) Apply the combined transformation to the lesion mask
# lesion_in_control_image_space = ants.apply_transforms(fixed=<control image path>, moving=<lesion mask path>, transformlist=transformlist)

# (3) Save the lesion mask in control image space:
# ants.image_write(lesion_in_control_image_space, <out_path>)

