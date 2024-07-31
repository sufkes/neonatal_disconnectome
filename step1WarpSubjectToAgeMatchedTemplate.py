import os
import ants

from constants import CONTROLS_DIR, TEMPLATE_TEMPLATES_DIR

# Age between 28-44 discrete

def createRunsDirectory(subject, runs_dir):
  ## 1. Create the runs directory structure
  dir_list = [
    f.name for f in os.scandir(CONTROLS_DIR) if f.is_dir()
  ]
  for d in dir_list:
    sub_dir_list = [
      f.name for f in os.scandir(CONTROLS_DIR / d) if f.is_dir()
    ]
    sub_name = d + '_' + sub_dir_list[0]
    path = os.path.join(runs_dir, subject, 'control_space', sub_name)
    try:
      os.makedirs(path, exist_ok=True)
    except FileExistsError:
        print("Folder is already there")
    else:
        print("Folder was created")

def warpSubjectToAgeMatchedTemplate(runs_dir, subject, image_type, moving_image, lesion_image, age):

  try:
    ## 1. Create the template space runs directory structure to store result
    print(f"age is: {age}")
    age_dir = age + "W"
    out_dir = os.path.join(runs_dir, subject, 'template_space', age_dir)
    print(f"path is: {out_dir}")
    try:
      os.makedirs(out_dir, exist_ok=False)
    except FileExistsError:
        print("Folder is already there")
    else:
        print(f"created template space: {out_dir}")



    ## 2. Set file paths for inputs

    # Path to age-matched template image (the "fixed" image).
    fixed_path = os.path.join(TEMPLATE_TEMPLATES_DIR, 'week' + age + '_' + image_type + '.nii.gz')
    print(f"fixed_path: {fixed_path}")

    ## 3. Set file paths for outputs

    # Filepath prefix for transformation files.
    out_prefix = os.path.join(out_dir, 'brain_img' + '_' + age + '-week-template-space-')
    print(f"out_prefix: {out_prefix}")
    # Path to moving image warped to fixed image space.
    out_image_path = out_prefix + 'warped.nii.gz'
    # Path to lesion mask warped to fixed image space.
    out_lesion_path = os.path.join(out_dir, 'lesion_mask' + '_' + age + '-week-template-space-warped.nii.gz')
    print(f"out_lesion_path: {out_lesion_path}")

    ## 4. Open the NIFTI files as ANTsImage objects.
    try:
      moving_ants_img = ants.image_read(moving_image)
      fixed_ants_img = ants.image_read(fixed_path)
      lesion_ants_img = ants.image_read(lesion_image)
    except ValueError as err:
      print("Opening NIFTI files as ANTSImage objects failed: ", err)
      return err
    else:
      print("ANTsImage Objects read successfully")

    ## 5. Calculate the moving -> fixed transform.
    registration = ants.registration(fixed=fixed_ants_img, moving=moving_ants_img, type_of_transform='SyN', outprefix=out_prefix, verbose=True)

    '''
      This will create the following files:
      <out_prefix>1Warp.nii.gz - The nonlinear part of the moving -> fixed transform
      <out_prefix>0GenericAffine.mat - The affine part of the moving -> fixed transform
      <out_prefix>1InverseWarp - The nonlinear part of the fixed -> moving transform (we don't need this)

      To perform the moving -> fixed transform, we must apply the affine part first, then the nonlinear part.
      For the following command (ants.apply_transforms), we input a list of transforms in the reverse order in which they should be applied. I.e. we define a list:
      transformlist = [<path to last transform>, ..., <path to 2nd transform>, <path to 1st transform>]

      In our case, this transform list will be:
      transformlist = [<out_prefix>1Warp.nii.gz, <out_prefix>0GenericAffine.mat]
      This list of transforms has already been calculated in the previous command, so we can simply access it using: transformlist = registration['fwdtransforms']
    '''

    ## 6. Apply the transform to the moving image, and its corresponding lesion mask.

    # Note: We apply the first transformation here, so that the user can inspect the transformation quality (which could be bad). However, for generation of the disconnectome, we will combine this warp with subsequent warps, and perform the combined operation:
    # (lesion mask) -> (age-matched template) -> (40w template) ->  (control image)
    # in a single operation.
    # This simply requires building up the 'transformlist' list with all of the warps in the chain (in reverse order).
    warped_image = ants.apply_transforms(fixed=fixed_ants_img, moving=moving_ants_img, transformlist=registration['fwdtransforms'],verbose=True)
    warped_lesion = ants.apply_transforms(fixed=fixed_ants_img, moving=lesion_ants_img, transformlist=registration['fwdtransforms'],verbose=True)

    ## 7. Save the warped image to NIFTI.
    ants.image_write(warped_image, out_image_path)
    ants.image_write(warped_lesion, out_lesion_path)
  except Exception as e:
     print("warpSubjectToAgeMatchedTemplate failed: ", e)
     raise e
  else:
     return True
