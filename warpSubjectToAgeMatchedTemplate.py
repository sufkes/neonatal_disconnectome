# importing os module
from pathlib import Path
import os
import ants

# Age between 28-44 discrete

def createRunsDirectory(subject):
  ## 1. Create the runs directory structure
  cwd = Path.cwd()
  controls_dir = cwd / 'controls'
  dir_list = [
    f.name for f in os.scandir(controls_dir) if f.is_dir()
  ]

  for d in dir_list:
    print(f"directory is: {d}")
    sub_dir_list = [
      f.name for f in os.scandir(controls_dir / d) if f.is_dir()
    ]
    print(f"sub_dir_list is: {sub_dir_list}")
    sub_name = d + '_' + sub_dir_list[0]
    path = cwd / 'runs' / subject / 'control_space' / sub_name
    print(f"path is: {path}")
    try:
      path.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print("Folder is already there")
    else:
        print("Folder was created")

def warpSubjectToAgeMatchedTemplate(subject, image_type, moving_image, lesion_image, age):
  # looping through every subject sub folder in the controls folder
  # file uploaded is what will be used
  cwd = Path.cwd()

  session = moving_image.split("_")[1]
  print(f"session is: {session}")

  ## 1. Create the template space out directory to store result
  age_dir = age + "W"
  out_dir = cwd / 'runs' / subject / 'template_space' / age_dir
  print(f"path is: {out_dir}")
  try:
    out_dir.mkdir(parents=True, exist_ok=False)
  except FileExistsError:
      print("Folder is already there")
  else:
      print(f"created template space: {out_dir}")



  ## 2. Set file paths for inputs

  # Path to input subject anatomical image (T1 or T2) which needs to be warped (the "moving" image)
  in_dir = cwd / 'example_input_data' / subject
  template_dir = cwd / 'template' / 'templates'
  moving_path = os.path.join(in_dir, moving_image)
  print(f"moving_path: {moving_path}")
  # Path to lesion mask corresponding to the "moving" image.
  lesion_path = os.path.join(in_dir, lesion_image)
  print(f"lesion_path: {lesion_path}")
  # Path to age-matched template image (the "fixed" image).
  fixed_path = os.path.join(template_dir, 'week' + age + '_' + image_type + '.nii.gz')
  print(f"fixed_path: {fixed_path}")

  ## 3. Set file paths for outputs

  # Filepath prefix for transformation files.
  out_prefix = os.path.join(out_dir, moving_image.split('.')[0] + '_' + age + '-week-template-space-')
  print(f"out_prefix: {out_prefix}")
  # Path to moving image warped to fixed image space.
  out_image_path = out_prefix + 'warped.nii.gz'
  # Path to lesion mask warped to fixed image space.
  out_lesion_path = os.path.join(out_dir, lesion_image.split('.')[0] + '_' + age + '-week-template-space-warped.nii.gz')
  print(f"out_lesion_path: {out_lesion_path}")

  ## 4. Open the NIFTI files as ANTsImage objects.
  try:
    moving_img = ants.image_read(moving_path)
    fixed_img = ants.image_read(fixed_path)
    lesion_img = ants.image_read(lesion_path)
  except ValueError as err:
    print(err)
  else:
    print("ANTsImage Objects read successfully")

  ## 5. Calculate the moving -> fixed transform.

  # It would be nice if the user could customize the options of this registration command. Specifically, if they could change the type_of_transform argument, and maybe a few others.
  #type_of_transform='antsRegistrationSyNQuick[s]'
  registration = ants.registration(fixed=fixed_img, moving=moving_img, type_of_transform='SyN', outprefix=out_prefix, verbose=True)

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

  ## 6. Apply the transform to the moving image, and its corresponding lesion mask.

  # Note: We apply the first transformation here, so that the user can inspect the transformation quality (which could be bad). However, for generation of the disconnectome, we will combine this warp with subsequent warps, and perform the combined operation:
  # (lesion mask) -> (age-matched template) -> (40w template) ->  (control image)
  # in a single operation.
  # This simply requires building up the 'transformlist' list with all of the warps in the chain (in reverse order).
  warped_image = ants.apply_transforms(fixed=fixed_img, moving=moving_img, transformlist=registration['fwdtransforms'],verbose=True)
  warped_lesion = ants.apply_transforms(fixed=fixed_img, moving=lesion_img, transformlist=registration['fwdtransforms'],verbose=True)

  ## Save the warped image to NIFTI.
  ants.image_write(warped_image, out_image_path)
  ants.image_write(warped_lesion, out_lesion_path)
