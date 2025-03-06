# dipy used here and its dependencies

import logging
import os

import nibabel as nib
from dipy.io.streamline import load_trk
from dipy.tracking.utils import target, density_map
from dipy.io.stateful_tractogram import StatefulTractogram, Space

from constants import CONTROL_SPACE, CONTROLS_DIR

logger = logging.getLogger(__name__)

def generateVisitationMap(runs_dir, subject):
  try:
    runs_path = os.path.join(runs_dir, subject)
    runs_control_space_path = os.path.join(runs_path, CONTROL_SPACE)

    dir_list = [
      f.name for f in os.scandir(runs_control_space_path) if f.is_dir()
    ]

    for d in dir_list:
      sub_name = d
      path = os.path.join(runs_control_space_path, sub_name)
      lesion_path = os.path.join(path, 'lesion.nii.gz')
      sub_name_split = sub_name.split('_')
      trk_dir = os.path.join(CONTROLS_DIR,sub_name_split[0],sub_name_split[1],'trk')
      tract_path = os.path.join(trk_dir, sub_name + '_hardi.trk' )

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
      visitation_map_out_path = os.path.join(out_visitation_prefix, 'visitation.nii.gz')
      nib.save(visitation_map_img, visitation_map_out_path) # save NIFTI
  except Exception as e:
     logger.exception("Generate visitiation map step failed")
     raise e
  else:
     return True


