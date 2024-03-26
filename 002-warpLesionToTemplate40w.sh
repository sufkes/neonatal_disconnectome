# This is a placeholder for a script that has not been written, because initial tests used an alternative warping method.

# Here, we apply the subject -> age-matched template transformation to the subject lesion map. Then, we apply the age-matched template -> 40w template transformation (precomputed). The 40w template is the "standard" template age, where much of the work will be done. These two steps bring the subject lesion map into the space of the 40w template image.

## Inputs:
# Supplied by user:
# - Lesion map in space of subject brain image, in NIFTI format
# From previous steps or included in toolkit:
# - Subject -> age-matched template affine transform file, in binary ITK format
# - Subject -> age-matched template nonlinear transform ("warp") file, in NIFTI format (an ANTS warp file)
# - Age-matched template, in NIFTI format
# - 40w template (the "standard" template), in NIFTI format
# - Age-matched template -> 40w template transformation - an FSL warp file, in NIFTI format. *Note that we must deal with both FSL and ANTS warp files, which are both NIFTI files, but are structured differently and incompatible between FSL and ANTS.

## Outputs:
# - The lesion map in age-matched template space
# - The lesion map in 40w template space

## Psuedo-codo
# - Apply the lesion map -> age-matched template warp. This is an ANTS transformation with affine & nonlinear components. Command will be:
# $ antsApplyTransforms -d 3 -n NearestNeighbor -i <path to lesion map in subject space> -r <path to age-matched template> -o <output prefix> -t <path to subject-to-age-matched template warp> <path to subject-to-age-matched template affine>
# - Warp the lesion map from the age-matched template space to the 40w template space. This is an FSL warp file. Note that if the age-matched template happens to be the 40w template itself, nothing needs to be done here except copying/linking the files. The command will be:
# $ 
