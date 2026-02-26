import logging
import os
import threading
from typing import Callable, Optional
import ants

from lib.constants import (
    CONTROL_SPACE,
    CONTROLS_DIR,
    TEMPLATE_SPACE,
    TEMPLATE_TEMPLATES_DIR,
    TEMPLATE_WARPS_DIR,
)
from lib.utils import createDisconnectomeDirectory, thresholdWarpedLesion

logger = logging.getLogger(__name__)


def applySubjectLesionToControlImageWarp(
    runs_dir,
    subject,
    lesion_image,
    age,
    skip=False,
    cancel_event: Optional[threading.Event] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None,
):
    def check_cancelled():
        return cancel_event and cancel_event.is_set()

    def update_progress(progress: float, message: str):
        if progress_callback:
            progress_callback(progress, message)

    try:
        update_progress(0.0, "Setting up transform list")

        age_dir = age + "W"
        runs_path = os.path.join(runs_dir, subject)
        runs_template_space_path = os.path.join(runs_path, TEMPLATE_SPACE, age_dir)
        runs_control_space_path = os.path.join(runs_path, CONTROL_SPACE)

        # Filepath prefix for transformation files.
        out_prefix = "brain_img" + "_" + age + "-week-template-space-"

        dir_list = [f.name for f in os.scandir(CONTROLS_DIR) if f.is_dir()]
        total = len(dir_list)

        if check_cancelled():
            logger.info("Warp cancelled during setup")
            return False

        # looping through every subject sub folder in the controls folder
        for i, d in enumerate(dir_list):
            update_progress(i / total, f"Warping lesion to control {i + 1}/{total}")
            sub_dir_list = [
                f.name for f in os.scandir(os.path.join(CONTROLS_DIR, d)) if f.is_dir()
            ]
            sub_name = d + "_" + sub_dir_list[0]
            path = os.path.join(CONTROLS_DIR, d, sub_dir_list[0], "xfm-ants")

            # 40w template to control image warp NIFTI path (transform 4, precomputed)
            dwi_mode_path = os.path.join(
                path, sub_name + "_from-extdhcp40wk_to-dwi_mode-image.nii.gz"
            )
            update_progress(
                0.1,
                f"Adding 40w template to control image warp({dwi_mode_path}) to transform list",
            )
            transformlist = []
            transformlist += [dwi_mode_path]

            if check_cancelled():
                logger.info(f"Adding {dwi_mode_path} cancelled")
                return False

            # age-matched template to 40w template warp NIFTI path (transform 3, precomputed)
            # If age is equal to 40 can skip this step
            if age != "40":
                template_path = os.path.join(
                    TEMPLATE_WARPS_DIR, "week-" + age + "_to_week-40_warp.nii.gz"
                )
                update_progress(
                    0.2,
                    f"Adding age-matched template to 40w template warp({template_path}) to transform list",
                )
                transformlist += [template_path]
                if check_cancelled():
                    logger.info(f"Adding {template_path} cancelled")
                    return False

            if not skip:
                # lesion mask to age-matched template warp NIFTI path (transform 2, computed in previous step)
                lesion_mask_path = os.path.join(
                    runs_template_space_path, out_prefix + "1Warp.nii.gz"
                )
                update_progress(
                    0.3,
                    f"Adding lesion mask to age-matched template warp({lesion_mask_path}) to transform list",
                )
                transformlist += [lesion_mask_path]
                if check_cancelled():
                    logger.info(f"Adding {lesion_mask_path} cancelled")
                    return False
                # lesion mask to age-matched template affine path (transform 1, computed in previous step)
                affine_path = os.path.join(
                    runs_template_space_path, out_prefix + "0GenericAffine.mat"
                )
                update_progress(
                    0.4,
                    f"Adding lesion mask to age-matched template affine({affine_path}) to transform list",
                )
                transformlist += [affine_path]
                if check_cancelled():
                    logger.info(f"Adding {affine_path} cancelled")
                    return False
            # (2) Apply the combined transformation to the lesion mask
            controls_path = os.path.join(CONTROLS_DIR, d, sub_dir_list[0], "dwi")
            fixed_image = os.path.join(
                controls_path, sub_name + "_desc-brain_mask.nii.gz"
            )

            ## 4. Open the NIFTI files as ANTsImage objects.
            try:
                fixed_ants_img = ants.image_read(fixed_image)
                lesion_ants_img = ants.image_read(lesion_image)
            except ValueError as err:
                logger.exception("Opening NIFTI files as ANTSImage objects failed")
                raise err
            else:
                logger.info("ANTsImage Objects read successfully")

            if check_cancelled():
                logger.info("Warp cancelled after loading images")
                return False

            update_progress(0.5, "Applying transformation to brain image")
            lesion_in_control_image_space = ants.apply_transforms(
                fixed=fixed_ants_img,
                moving=lesion_ants_img,
                transformlist=transformlist,
                verbose=False,
            )

            if check_cancelled():
                logger.info("Warp cancelled after brain transform")
                return False

            # TODO
            ## Steve update: When the lesion is warped from native to control space, the lesion gets "smeared out" by resampling/interpolation. The warped lesion in control space will typically have greater volume than the original lesion. To fix this, we threshold the warped lesion such that its volume is the same as the original lesion, but multiplied by some factor to account for the differences in brain volumes between the lesion and control subjects. Since we do not know the brain volumes of the lesion or control subjects, we estimate using a linear function of brain volume vs. gestational age.
            control_age_path = os.path.join(
                CONTROLS_DIR, d, sub_dir_list[0], "scan_age.txt"
            )
            with open(control_age_path) as handle:
                control_age = handle.read()

            update_progress(
                0.6,
                "Applying threshold to warped legion to account for brain volume difference",
            )
            lesion_in_control_image_space = thresholdWarpedLesion(
                lesion_ants_img, lesion_in_control_image_space, age, control_age
            )
            if check_cancelled():
                logger.info("Warp cancelled after applying threshold")
                return False

            # (3) Save the lesion mask in control image space:
            out_image_prefix = os.path.join(runs_control_space_path, sub_name)
            out_image_path = os.path.join(out_image_prefix, "lesion.nii.gz")
            ants.image_write(lesion_in_control_image_space, out_image_path)

        # (4) Save lesion mask warped to 40 week in disconnectome folder
        fixed_path = os.path.join(TEMPLATE_TEMPLATES_DIR, "week40_T1w.nii.gz")
        try:
            fixed_ants_img = ants.image_read(fixed_path)
        except ValueError as err:
            logger.exception("Opening NIFTI files as ANTSImage objects failed")
            raise err
        else:
            logger.info("ANTsImage Objects read successfully")

        update_progress(0.7, "Applying transformation to brain image")
        lesion_warped_to_40_week = ants.apply_transforms(
            fixed=fixed_ants_img,
            moving=lesion_ants_img,
            transformlist=transformlist[1:],
            verbose=False,
        )
        lesion_warped_to_40_week = thresholdWarpedLesion(
            lesion_ants_img, lesion_warped_to_40_week, age, 40
        )

        update_progress(0.8, "Creating Disconnectome directory")
        disconnectome_out_dir = createDisconnectomeDirectory(runs_dir, subject)

        out_lesion_path = os.path.join(
            disconnectome_out_dir, "lesion_mask_40-week-template-space-warped.nii.gz"
        )
        ants.image_write(lesion_warped_to_40_week, out_lesion_path)
    except Exception as e:
        logger.exception("Apply subject lesion to control image warp step failed")
        raise e
    else:
        return True
