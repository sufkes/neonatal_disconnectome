import os
import ants

from constants import CONTROLS_DIR, TEMPLATE_WARPS_DIR

def applySubjectLesionToControlImageWarp(runs_dir, subject, lesion_image, age):
  try:

    age_dir = age + "W"
    runs_path = os.path.join(runs_dir, subject)
    runs_template_space_path = os.path.join(runs_path, 'template_space', age_dir)
    runs_control_space_path = os.path.join(runs_path, 'control_space')


    # Filepath prefix for transformation files.
    out_prefix = 'brain_img' + '_' + age + '-week-template-space-'
    print(f"out_prefix: {out_prefix}")

    dir_list = [
      f.name for f in os.scandir(CONTROLS_DIR) if f.is_dir()
    ]

    print(f"runs_template_space_path is: {runs_template_space_path}")

    # looping through every subject sub folder in the controls folder
    for d in dir_list:

      print(f"directory is: {d}")
      sub_dir_list = [
        f.name for f in os.scandir(CONTROLS_DIR / d) if f.is_dir()
      ]
      print(f"sub_dir_list is: {sub_dir_list}")
      sub_name = d + '_' + sub_dir_list[0]
      path = CONTROLS_DIR / d / sub_dir_list[0] / 'xfm-ants'
      print(f"path is: {path}")

      # 40w template to control image warp NIFTI path (transform 4, precomputed)
      dwi_mode_path = os.path.join(path, sub_name + '_from-extdhcp40wk_to-dwi_mode-image.nii.gz')
      print(f"dwi_mode_path: {dwi_mode_path}")
      transformlist = []
      transformlist += [dwi_mode_path]

      # age-matched template to 40w template warp NIFTI path (transform 3, precomputed)
      # If age is equal to 40 can skip this step
      # if age is 40 skip this
      if(age != "40"):
        template_path = os.path.join(TEMPLATE_WARPS_DIR, 'week-' + age + '_to_week-40_warp.nii.gz')
        print(f"template_path: {template_path}")
        transformlist += [template_path]


      # lesion mask to age-matched template warp NIFTI path (transform 2, computed in previous step)
      lesion_mask_path = os.path.join(runs_template_space_path, out_prefix + '1Warp.nii.gz')
      print(f"lesion_mask_path: {lesion_mask_path}")
      transformlist += [lesion_mask_path]

      # lesion mask to age-matched template affine path (transform 1, computed in previous step)
      affine_path = os.path.join(runs_template_space_path, out_prefix + '0GenericAffine.mat')
      print(f"affine_path: {affine_path}")
      transformlist += [affine_path]

      print(f"transformlist: {transformlist}")

      # (2) Apply the combined transformation to the lesion mask
      controls_path = CONTROLS_DIR / d / sub_dir_list[0] / 'dwi'
      fixed_image = os.path.join(controls_path, sub_name + '_desc-brain_mask.nii.gz')
      print(f"fixed_image: {fixed_image}")

      ## 4. Open the NIFTI files as ANTsImage objects.
      try:
        fixed_ants_img = ants.image_read(fixed_image)
        lesion_ants_img = ants.image_read(lesion_image)
      except ValueError as err:
        raise err
      else:
        print("ANTsImage Objects read successfully")

      lesion_in_control_image_space = ants.apply_transforms(fixed=fixed_ants_img, moving=lesion_ants_img, transformlist=transformlist, verbose=True)

      print(type(lesion_in_control_image_space))

      # (3) Save the lesion mask in control image space:
      out_image_prefix = os.path.join(runs_control_space_path, sub_name)
      print(f"out_image_prefix: {out_image_prefix}")
      out_image_path = os.path.join(out_image_prefix, 'lesion.nii.gz')
      print(f"out_image_path: {out_image_path}")
      ants.image_write(lesion_in_control_image_space, out_image_path)
  except Exception as e:
     print("applySubjectLesionToControlImageWarp failed: ", e)
     raise e
  else:
     return True
