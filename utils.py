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
from pathlib import Path
import shutil

from constants import (
    CONTROL_SPACE,
    CONTROLS_DIR,
    DISCONNECTOME,
    TEMPLATE_SPACE,
    THUMBNAILS,
    WEB_IMG_DIR,
)

logger = logging.getLogger("disconnectome")


def get_theme_names_from_folder(folder_path="themes"):
    theme_files = []
    if os.path.isdir(folder_path):
        for f in os.listdir(folder_path):
            if f.endswith(".json"):
                # Add theme name without ".json"
                theme_files.append(f[:-5])
    return theme_files


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


def deleteImagefiles():
    """delete all image files from previous runs. This function is called everytime a new run is started"""
    for imageFile in os.listdir(WEB_IMG_DIR):
        root, ext = os.path.splitext(imageFile)
        if (
            root.startswith("brain_image_thumbnail")
            or root.startswith("plot_aligned_image_pair")
            or root.startswith("lesion_on_age_matched_template_clusters")
            or root.startswith("lesion_on_original")
            or root.startswith("disconnectome_at_lesion_centroids")
        ) and ext == ".png":
            try:
                os.remove(os.path.join(WEB_IMG_DIR, imageFile))
            except OSError as e:
                # If it fails, inform the user.
                logger.exception("failed to delete image files")


def copyImageFiles(runs_dir: str, subject: str):
    """Copy generated thumbnails from web/img folder to thumbnails folder in the runs directory for given subject

    Parameters
    ----------
    runs_dir : str
        The full path of the runs directory
    subject : str
        The subject ID used to create the directory structure for current run
    """
    logger.info("WEB_IMG_DIR: %s", WEB_IMG_DIR)
    src_files = os.listdir(WEB_IMG_DIR)
    thumbnail_dir = os.path.join(runs_dir, subject, THUMBNAILS)
    logger.debug("the thumbnail dir path is: %s", thumbnail_dir)
    if len(thumbnail_dir) != 0:
        [f.unlink() for f in Path(thumbnail_dir).glob("*") if f.is_file()]

    for file_name in src_files:
        full_file_name = os.path.join(WEB_IMG_DIR, file_name)
        logger.debug("file name is:  %s", full_file_name)
        if os.path.isfile(full_file_name) and file_name != "logo.png":
            shutil.copy(full_file_name, thumbnail_dir)


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
