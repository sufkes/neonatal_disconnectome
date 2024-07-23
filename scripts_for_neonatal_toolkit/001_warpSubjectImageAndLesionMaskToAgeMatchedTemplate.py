#!/usr/bin/env python3

import os
import ants

## Set file paths.
# Path to input subject anatomical image (T1 or T2) which needs to be warped (the "moving" image)
moving_path = 'sub-CC00097XX16_ses-33701_run-07_T2w.nii.gz'
# Path to lesion mask corresponding to the "moving" image.
lesion_path = 'sub-CC00097XX16_ses-33701_run-07_lesion_mask.nii.gz'
# Path to age-matched template image (the "fixed" image).
fixed_path = 'week43_T2w.nii.gz'

# Output directory
out_dir = 'warp-antspy' # set this to a better location in the Toolbox.
os.makedirs(out_dir, exist_ok=True)
# Filepath prefix for transformation files.
out_prefix = os.path.join(out_dir, 'sub-CC00097XX16_ses-33701_run-07_T2w-43_week_template_space-')
# Path to moving image warped to fixed image space.
out_image_path = out_prefix + 'Warped.nii.gz'
# Path to lesion mask warped to fixed image space.
out_lesion_path = os.path.join(out_dir, 'sub-CC00097XX16_ses-33701_run-07_lesion_mask-43_week_template_space-Warped.nii.gz')

## Open the NIFTI files as ANTsImage objects.
moving_img = ants.image_read(moving_path)
fixed_img = ants.image_read(fixed_path)
lesion_img = ants.image_read(lesion_path)

## Calculate the moving -> fixed transform.
# It would be nice if the user could customize the options of this registration command. Specifically, if they could change the type_of_transform argument, and maybe a few others.
registration = ants.registration(fixed=fixed_img, moving=moving_img, type_of_transform='SyN', outprefix=out_prefix)

# This will create the following files:
#<out_prefix>1Warp.nii.gz - The nonlinear part of the moving -> fixed transform
#<out_prefix>0GenericAffine.mat - The affine part of the moving -> fixed transform
#<out_prefix>1InverseWarp - The nonlinear part of the fixed -> moving transform (we don't need this)

# To performm the moving -> fixed transform, we must apply the affine part first, then the nonlinear part.
# For the following command (ants.apply_transforms), we input a list of transforms in the reverse order in which they should be applied. I.e. we define a list:
# transformlist = [<path to last transform>, ..., <path to 2nd transform>, <path to 1st transform>]

# In our case, this transform list will be:
# transformlist = [<out_prefix>1Warp.nii.gz, <out_prefix>0GenericAffine.mat]
# This list of transforms has already been calculated in the previous command, so we can simply access it using:
# transformlist = registration['fwdtransforms']

## Apply the transform to the moving image, and its corresponding lesion mask.
# Note: We apply the first transformation here, so that the user can inspect the transformation quality (which could be bad). However, for generation of the disconnectome, we will combine this warp with subsequent warps, and perform the combined operation:
# (lesion mask) -> (age-matched template) -> (40w template) ->  (control image) 
# in a single operation.
# This simply requires building up the 'transformlist' list with all of the warps in the chain (in reverse order).
warped_image = ants.apply_transforms(fixed=fixed_img, moving=moving_img, transformlist=registration['fwdtransforms'])
warped_lesion = ants.apply_transforms(fixed=fixed_img, moving=lesion_img, transformlist=registration['fwdtransforms'])

## Save the warped image to NIFTI.
ants.image_write(warped_image, out_image_path)
ants.image_write(warped_lesion, out_lesion_path)
