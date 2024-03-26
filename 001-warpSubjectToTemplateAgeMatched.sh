# This is a placeholder for a script that has not been written, because initial tests used an alternative warping method.

# In this first step, the subject's raw 3D brain image is warped to an age-matched template.

## Inputs:
# Supplied by user:
# - A 3D brain image, in NIFTI format (.nii or .nii.gz)
# - Subject's gestational age, in weeks.
# Supplied by toolkit:
# - Age-matched template image, in NIFTI format.

## Outputs: 
# - The output transformation (the mapping from the subject -> template image) comes in three pieces 
#   - An affine tranform (the "linear" part of the transformation), in binary ITK transform format (filename ends with "_0GenericAffine.mat")
#   - An ANTS warp file (the nonlinear part of the transformation), in NIFTI format (filename ends with "_1Warp.nii.gz")
#   - An ANTS warp file for the inverse of the nonlinear transformation, in NIFTI format (filename ends with "_1InverseWarp.nii.gz")
# - The subject's image warped to the template space, in NIFTI format (filename ends with "_Warped.nii.gz")
# - The template image warped to the subject's image space (obtained using the inverse transformation), in NIFTI format (filename ends with "_InverseWarped.nii.gz")

## Psuedo-code
# - Determine which template has the closest age to the input subject. The template ages are 28, 29, ..., 44, in weeks.
# - Warp subject brain image to the age-matched template, using ANTS. The command will look like:
# $ antsRegistrationSyN.sh -d 3 -t s -m <path to subject brain image> -f <path to age-matched template> -o <output file path prefix>

