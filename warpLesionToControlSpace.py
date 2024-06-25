# importing os module
from pathlib import Path
import os
import ants

def warpLesionToControlSpace(subject, moving_image, lesion_image, age):
  # looping through every subject sub folder in the controls folder
  # file uploaded is what will be used
  cwd = Path.cwd()
  age_dir = age + "W"
  template_warps_dir = cwd / 'template' / 'warps-ants'
  runs_path = cwd / 'runs' / subject
  runs_template_space_path = runs_path / 'template_space' / age_dir
  runs_control_space_path = runs_path / 'control_space'

  # Path to lesion mask corresponding to the "moving" image.
  in_dir = cwd / 'example_input_data' / subject
  lesion_path = os.path.join(in_dir, lesion_image)
  print(f"lesion_path: {lesion_path}")

  # Filepath prefix for transformation files.
  out_prefix = moving_image.split('.')[0] + '_' + age + '-week-template-space-'
  print(f"out_prefix: {out_prefix}")
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
    path = controls_dir / d / sub_dir_list[0] / 'xfm-ants'
    print(f"path is: {path}")

    # 40w template to control image warp NIFTI path (transform 4, precomputed)
    dwi_mode_path = os.path.join(path, sub_name + '_from-extdhcp40wk_to-dwi_mode-image.nii.gz')
    print(f"dwi_mode_path: {dwi_mode_path}")
    transformlist = []
    transformlist += [dwi_mode_path]

    # age-matched template to 40w template warp NIFTI path (transform 3, precomputed)
    # If age is equal to 40 can skip this step
    template_path = os.path.join(template_warps_dir, 'week-' + age + '_to_week-40_warp.nii.gz')
    print(f"template_path: {template_path}")
    transformlist += [template_path]

    # lesion mask to age-matched template warp NIFTI path (transform 2, computed in previous step)
    lesion_mask_path = os.path.join(runs_template_space_path, out_prefix + '1Warp.nii.gz')
    print(f"legion_path: {lesion_mask_path}")
    transformlist += [lesion_mask_path]

    # lesion mask to age-matched template affine path (transform 1, computed in previous step)
    affine_path =os.path.join(runs_template_space_path, out_prefix + '0GenericAffine.mat')
    print(f"affine_path: {affine_path}")
    transformlist += [affine_path]

    print(f"transformlist: {transformlist}")

    # (2) Apply the combined transformation to the lesion mask
    controls_path = controls_dir / d / sub_dir_list[0] / 'dwi'
    fixed_image = os.path.join(controls_path, sub_name + '_desc-brain_mask.nii.gz')
    print(f"fixed_image: {fixed_image}")
    lesion_in_control_image_space = ants.apply_transforms(fixed=fixed_image, moving=lesion_path, transformlist=transformlist, verbose=True)

    print(type(lesion_in_control_image_space))

    # (3) Save the lesion mask in control image space:
    out_path = os.path.join(runs_control_space_path, sub_name)
    print(f"out_path: {out_path}")
    ants.image_write(lesion_in_control_image_space, out_path)
