# dipy used here and its dependencies

import os
from pathlib import Path

import nibabel as nib
from dipy.io.streamline import load_trk, save_trk
from dipy.tracking.streamline import Streamlines
from dipy.tracking.utils import target, density_map
#import numpy as np

from dipy.io.stateful_tractogram import StatefulTractogram, Space

def generateVisitationMap(subject):
  cwd = Path.cwd()
  runs_path = cwd / 'runs' / subject
  runs_control_space_path = runs_path / 'control_space'
  print(f"runs_control_space_path is: {runs_control_space_path}")

  dir_list = [
    f.name for f in os.scandir(runs_control_space_path) if f.is_dir()
  ]
  print(f"subject is: {subject}")
  print(f"dir_list is: {dir_list}")
  controls_dir = cwd / 'controls'
  for d in dir_list:
    sub_name = d
    path = runs_control_space_path / sub_name
    print(f"path is: {path}")
    lesion_path = os.path.join(path, 'lesion.nii.gz')
    print(f"lesion_path is: {lesion_path}")
    blah = sub_name.split('_')
    foo = controls_dir / blah[0] / blah[1] / 'trk'

    tract_path = os.path.join(foo, sub_name + '_hardi.trk' )
    print(f"tract_path is: {tract_path}")
    # Load tractogram
    tractogram_file = tract_path
    tractogram = load_trk(tractogram_file, reference='same')  # 'same' ensures the affine of the tractogram is used
    streamlines = tractogram.streamlines

    # Load lesion ROI
    roi_file = lesion_path
    roi_img = nib.load(roi_file)
    roi_data = roi_img.get_fdata()
    roi_affine = roi_img.affine

    # Filter the streamlines to include only those streamlines passing through the lesion ROI.
    filtered_streamlines_generator = target(streamlines, affine=roi_affine, target_mask=roi_data) # this is a streamlines generator, and putting it directly into dipy.tracking.utils.density_map is bugged.
    filtered_stateful_tractogram = StatefulTractogram(filtered_streamlines_generator, roi_img, Space.RASMM) # this step should not be necessary but is a quick solution to the generator bug.
    filtered_streamlines = filtered_stateful_tractogram.streamlines # same type as the unfiltered streamlines; no bugs

    # Create visitation map
    visitation_map_array = density_map(filtered_streamlines, affine=roi_affine, vol_dims=roi_img.shape)
    visitation_map_array = visitation_map_array.astype(float) # nibabel doesn't like integers, so convert to floats. This is likely the issue underlying the bug which prevents filtered_streamlines_generator from being passed directly into dipy.tracking.utils.density_map
    visitation_map_img = nib.Nifti1Image(visitation_map_array, roi_affine)

    out_visitation_prefix = os.path.join(runs_control_space_path, sub_name)
    print(f"out_visitation_prefix: {out_visitation_prefix}")
    visitation_map_out_path = os.path.join(out_visitation_prefix, 'visitation.nii.gz')
    print(f"visitation_map_out_path: {visitation_map_out_path}")
    nib.save(visitation_map_img, visitation_map_out_path) # save NIFTI
  return True


