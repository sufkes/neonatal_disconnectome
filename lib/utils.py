"""Util functions

These are util functions used by the main program

This file contains the following functions:

    * createControlSpaceDirectory - creates the sub folder structure for the control space subdirectory to store lesion and visitation data
    * createTemplateSpaceDirectory - creates the sub folder structure for the template space subdirectory to store warps from first step
    * createDisconnectomeDirectory - creates the sub folder structure for the disconnectome subdirectory to store disconnectome and warped lesion mask
    * getRoundedAge - given a subjects age it rounds and makes sure is between 28 and 44
    * deleteImagefiles - deletes old image files from previous runs
"""

from decimal import Decimal
import logging
import os
import json
import platform
import subprocess
import numpy as np

from lib.constants import (
    CONTROL_SPACE,
    CONTROLS_DIR,
    DISCONNECTOME,
    TEMPLATE_SPACE,
    THUMBNAILS,
)

logger = logging.getLogger("disconnectome")


SETTINGS_FILE = "user_settings.json"


def update_settings(**kwargs):
    settings = load_settings()
    settings.update(kwargs)  # Update only the keys passed
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    return None


def createImageThumbnailDirectory(subject: str, runs_dir: str):
    """creates the sub folder structure for the image thumbnail subdirectory based on subject ID

    Parameters
    ----------
    subject : str
        The subject ID used to create the directory structure for current run
    runs_dir : str
        The full path of the runs directory
    """

    path = os.path.join(runs_dir, subject, THUMBNAILS)
    try:
        os.makedirs(path, exist_ok=True)
    except FileExistsError:
        logger.warning("folder already exists")
    else:
        logger.info("Image thumbnail directory created")


def createControlSpaceDirectory(subject: str, runs_dir: str):
    """creates the sub folder structure for the control space subdirectory based on subject ID

    Parameters
    ----------
    subject : str
        The subject ID used to create the directory structure for current run
    runs_dir : str
        The full path of the runs directory
    """

    createImageThumbnailDirectory(subject, runs_dir)

    # get a list of subdirectories names from controls folder
    dir_list = [f.name for f in os.scandir(CONTROLS_DIR) if f.is_dir()]
    for d in dir_list:
        sub_dir_list = [
            f.name for f in os.scandir(os.path.join(CONTROLS_DIR, d)) if f.is_dir()
        ]
        sub_name = d + "_" + sub_dir_list[0]
        path = os.path.join(runs_dir, subject, CONTROL_SPACE, sub_name)
        try:
            os.makedirs(path, exist_ok=True)
        except FileExistsError:
            logger.warning("folder already exists")
        else:
            logger.info(f"Control space sub folders created: {path}")


def createTemplateSpaceDirectory(age, runs_dir, subject):
    """creates the sub folder structure for the template space subdirectory based on subject ID and subject age

    Parameters
    ----------
    age : str
        The age of the subject
    runs_dir : str
        The full path of the runs directory
    subject : str
        The subject ID used to create the directory structure for current run

    Returns
    -------
    str
        The full path of newly created template space directory
    """

    age_dir = age + "W"
    out_dir = os.path.join(runs_dir, subject, TEMPLATE_SPACE, age_dir)
    try:
        os.makedirs(out_dir, exist_ok=False)
    except FileExistsError:
        logger.warning("folder already exists")
    else:
        logger.info("template space sub folder created: %s", out_dir)

    return out_dir


def createDisconnectomeDirectory(runs_dir, subject):
    """creates the sub folder structure for the disconnectome subdirectory based on subject ID

    Parameters
    ----------
    runs_dir : str
        The full path of the runs directory
    subject : str
        The subject ID used to create the directory structure for current run

    Returns
    -------
    str
        The full path of newly created disconnectome directory
    """
    runs_path = os.path.join(runs_dir, subject)
    disconnectome_out_dir = os.path.join(runs_path, DISCONNECTOME)
    try:
        os.makedirs(disconnectome_out_dir, exist_ok=False)
    except FileExistsError:
        logger.warning("folder already exists")
    else:
        logger.info("disconnectome directory created: %s", disconnectome_out_dir)

    return disconnectome_out_dir


def getRoundedAge(age):
    """Rounds the age

    Parameters
    ----------
    age : str
        The age of the subject

    Returns
    -------
    str
        The age of the subject rounded and between 28 <= roundedAge <= 44
    """
    roundedAge = round(Decimal(age))
    if roundedAge < 28:
        return "28"
    if roundedAge > 44:
        return "44"

    return str(roundedAge)


def open_in_file_browser(path):
    if not os.path.exists(path):
        logger.info(f"Path does not exist: {path}")
        return

    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["explorer", "/select,", path])
        elif system == "Darwin":  # macOS
            subprocess.run(["open", "-R", path])
        else:  # Linux
            subprocess.run(["xdg-open", os.path.dirname(path)])
    except Exception as e:
        logger.error(f"Error opening path {path}: {e}")


# TODO add function for volume adjustment
def estimateBrainVolume(age):
    volume_estimate = (
        24480.9 * float(age) - 491404.5
    )  # linear function fit to volumes of dHCP template brain masks (ranging from 28-44 weeks)
    volume_estimate = max(
        193462.50, volume_estimate
    )  # force estimate to be >= volume of 28w dHCP template brain mask
    volume_estimate = min(
        576915.25, volume_estimate
    )  # force estimate to be <= volume of 44w dHCP template brain mask
    return volume_estimate


def thresholdWarpedLesion(
    lesion_image, lesion_in_control_image_space, lesion_age, control_age
):
    # Estimate the volume of the lesion and control subjects' brains.
    lesion_brain_volume = estimateBrainVolume(lesion_age)
    control_brain_volume = estimateBrainVolume(control_age)

    scaling_factor = (
        control_brain_volume / lesion_brain_volume
    )  # factor by which the lesion should be scaled going from the lesion -> control spaces, in order to account for changes in brain/lesion volume with age.

    original_lesion_volume_per_voxel_mm3 = np.product(lesion_image.spacing)
    original_lesion_volume_voxels = np.count_nonzero(lesion_image.numpy())
    original_lesion_volume_mm3 = (
        original_lesion_volume_voxels * original_lesion_volume_per_voxel_mm3
    )

    warped_lesion_target_volume_mm3 = original_lesion_volume_mm3 * scaling_factor
    warped_lesion_volume_per_voxel_mm3 = np.product(
        lesion_in_control_image_space.spacing
    )
    warped_lesion_target_volume_voxels = (
        warped_lesion_target_volume_mm3 / warped_lesion_volume_per_voxel_mm3
    )

    warped_lesion_space_total_voxels = np.product(
        lesion_in_control_image_space.numpy().shape
    )  # total number of voxels in the control image space (LxWxH).

    target_ratio_positive_voxels = (
        warped_lesion_target_volume_voxels / warped_lesion_space_total_voxels
    )  # what ratio of voxels in the output image will be positive
    target_percentile = np.percentile(
        lesion_in_control_image_space.numpy(), (1 - target_ratio_positive_voxels) * 100
    )
    lesion_in_control_image_space_thresholded_array = (
        lesion_in_control_image_space.numpy()
    )
    lesion_in_control_image_space_thresholded_array[
        lesion_in_control_image_space_thresholded_array < target_percentile
    ] = 0
    lesion_in_control_image_space_thresholded_array[
        lesion_in_control_image_space_thresholded_array > 0
    ] = 1  # binarize, so the lesion voxels are valued 0 or 1.

    # Raise exception if warped lesion has zero volume.
    if np.count_nonzero(lesion_in_control_image_space_thresholded_array) == 0:
        msg = "Warped lesion has zero volume"
        logger.exception(msg)
        raise Exception(msg)

    lesion_in_control_image_space_thresholded = (
        lesion_in_control_image_space.new_image_like(
            lesion_in_control_image_space_thresholded_array
        )
    )

    return lesion_in_control_image_space_thresholded
