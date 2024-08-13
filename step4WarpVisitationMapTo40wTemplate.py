import os
import ants

from constants import CONTROL_SPACE, TEMPLATE_TEMPLATES_DIR, CONTROLS_DIR, VISITATION_MAPS_40W

def warpVisitationMap(runs_dir, subject, image_type="T1w"):
  try:
    runs_path = os.path.join(runs_dir, subject)
    runs_control_space_path = os.path.join(runs_path, CONTROL_SPACE)
    runs_visitation_maps_40w_path = os.path.join(runs_path, VISITATION_MAPS_40W)

    print(f"runs_control_space_path is: {runs_control_space_path}")
    print(f"runs_visitation_maps_40w_path is: {runs_visitation_maps_40w_path}")

    # looping through every subject sub folder in the controls folder
    # file uploaded is what will be used
    dir_list = [
      f.name for f in os.scandir(CONTROLS_DIR) if f.is_dir()
    ]
    for d in dir_list:
      print(f"directory is: {d}")
      sub_dir_list = [
        f.name for f in os.scandir(os.path.join(CONTROLS_DIR,d)) if f.is_dir()
      ]
      print(f"sub_dir_list is: {sub_dir_list}")
      sub_name = d + '_' + sub_dir_list[0]
      path = os.path.join(CONTROLS_DIR,d,sub_dir_list[0],'xfm-ants')
      print(f"path is: {path}")

      # path to control-to-40W_template warp file in ANTs format
      dwi_mode_path = os.path.join(path, sub_name + '_from-dwi_to-extdhcp40wk_mode-image.nii.gz')
      print(f"dwi_mode_path: {dwi_mode_path}")
      transformlist = []
      transformlist += [dwi_mode_path]

      print(f"transformlist: {transformlist}")

      # Fixed path
      fixed_path = os.path.join(TEMPLATE_TEMPLATES_DIR, 'week40_' + image_type + '.nii.gz')
      print(f"fixed_path: {fixed_path}")

      # moving path
      controls_path = os.path.join(runs_control_space_path, sub_name)
      moving_path = os.path.join(controls_path, 'visitation.nii.gz')
      print(f"moving_path: {moving_path}")

      ## 4. Open the NIFTI files as ANTsImage objects.
      try:
        fixed_ants_img = ants.image_read(fixed_path)
        moving_ants_img = ants.image_read(moving_path)
      except ValueError as err:
        print(err)
      else:
        print("ANTsImage Objects read successfully")

      lesion_in_40w_template_space = ants.apply_transforms(fixed=fixed_ants_img, moving=moving_ants_img, transformlist=transformlist, verbose=True)

      print(type(lesion_in_40w_template_space))

      # (3) Save the lesion in 40w template space:
      out_image_prefix = os.path.join(runs_visitation_maps_40w_path, sub_name)
      print(f"out_image_prefix: {out_image_prefix}")
      out_image_path = os.path.join(out_image_prefix, 'visitation_map.nii.gz')
      print(f"out_image_path: {out_image_path}")

      try:
        new_dir = out_image_prefix
        os.makedirs(new_dir, exist_ok=False)
      except FileExistsError:
          print("Folder is already there")
      else:
          print("Folder was created")

      ants.image_write(lesion_in_40w_template_space, out_image_path)
  except Exception as e:
     print("warpVisitationMap failed: ", e)
     raise e
  else:
     return True

