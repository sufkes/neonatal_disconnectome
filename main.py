import logging
from pathlib import Path
import os
import platform
import sys
from constants import WEB_IMG_DIR
import eel

from tkinter import *
import tkinter.filedialog as fdialog

from logger import configure_logging
from makeThumbnails import plotThreeView
from step1WarpSubjectToAgeMatchedTemplate import warpSubjectToAgeMatchedTemplate
from step2ApplySubjectLesionToControlImageWarp import applySubjectLesionToControlImageWarp
from step3GenerateVisitationMap import generateVisitationMap
from step4WarpVisitationMapTo40wTemplate import warpVisitationMap
from step5MakeDisconnectomeMap import generateDisconnectome
from utils import createControlSpaceDirectory, createTemplateSpaceDirectory, deleteImagefiles, getRoundedAge

configure_logging()

logger = logging.getLogger(__name__)

eel.init(str(Path(__file__).parent / "web"),
        allowed_extensions=[".html", ".js", ".css", ".woff", ".svg", ".svgz", ".png"])
        # Give folder containing web files

saved_folder = ""  # global variable to store folder path

root = Tk()
root.withdraw()

@eel.expose
def getFolder():
  global saved_folder

  try:
    # Make sure the root window is on top and focused
    root.attributes('-topmost', True)
    root.update()  # Update to apply the '-topmost' attribute
    root.update_idletasks()  # Process all idle tasks
    root.lift()              # Bring root window to front
    folder = fdialog.askdirectory(parent=root, title="Select a runs directory")
  finally:
    root.withdraw()    # stop event loop if running
    root.update()  # process any leftover events
    if folder:
      saved_folder = folder
  return folder


@eel.expose
def get_saved_folder():
  return saved_folder

@eel.expose
def getFile(generateThumbnail = False, filename = 'brain_image_thumbnail.png'):
  #root = Tk()
  #root.withdraw()
  # Make sure the root window is on top and focused
  try:
    root.deiconify()
    root.attributes('-topmost', True)
    root.update()  # Update to apply the '-topmost' attribute
    root.update_idletasks()  # Process all idle tasks
    root.lift()              # Bring root window to front
    file = None
    file = fdialog.askopenfile(parent=root, title='Select a file', mode='r')
  finally:
    root.withdraw()    # stop event loop if running
    root.update()  # process any leftover events
    filepath = ""
    if file:
      filepath = os.path.abspath(file.name)
      if(generateThumbnail):
        # Generate Thumbnail image to preview original brain image
        plotThreeView(filepath, os.path.join(WEB_IMG_DIR,filename))
  return filepath


@eel.expose
def deleteImageFiles():
  # Delete all the old image files
  deleteImagefiles()
  return True

@eel.expose
def step1(runs_dir, subject, image_type, moving_image, lesion_image, age, filenameHash):
  try:
    createControlSpaceDirectory(subject, runs_dir)
    roundedAge = getRoundedAge(age)
    warpSubjectToAgeMatchedTemplate(runs_dir, subject, image_type, moving_image, lesion_image, roundedAge, filenameHash)
  except Exception as e:
    logger.exception("First step failed", e)
    return False
  else:
    return True

@eel.expose
def step1A(runs_dir, subject, lesion_image, age, filenameHash, image_type="T1w", threshold = 0):
  try:
    roundedAge = getRoundedAge(age)
    createControlSpaceDirectory(subject, runs_dir)
    createTemplateSpaceDirectory(roundedAge, runs_dir, subject)

#       nibabel.load(<nifti image path>).get_fdata().shape

#       Check that this matches for the lesion image and the template image

# In the case where a user inputs a lesion mask already warped to a template image, we can check that the lesion image has the same dimensions of the template image:

# nibabel.load(<lesion image path>).get_fdata().shape == (196, 238, 197)

    applySubjectLesionToControlImageWarp(runs_dir, subject, lesion_image, roundedAge, skip=True)
    generateVisitationMap(runs_dir, subject)
    warpVisitationMap(runs_dir, subject, image_type)
    generateDisconnectome(runs_dir, subject, image_type, filenameHash, threshold)
  except Exception as e:
    logger.exception("generate disconnectome failed", e)
    return False
  else:
    return True

@eel.expose
def step2(runs_dir, subject, lesion_image, age, filenameHash, threshold = 0, image_type="T1w"):
  try:
    roundedAge = getRoundedAge(age)
    applySubjectLesionToControlImageWarp(runs_dir, subject, lesion_image, roundedAge)
    generateVisitationMap(runs_dir, subject)
    warpVisitationMap(runs_dir, subject, image_type)
    generateDisconnectome(runs_dir, subject, image_type, filenameHash, threshold)
  except Exception as e:
    logger.exception("generate disconnectome failed", e)
    return False
  else:
    return True

if sys.platform in ['win32', 'win64'] and int(platform.release()) >= 10:
  eel.start('main.html', port=0, host="0.0.0.0", mode="edge")    # Start
else:
  eel.start('main.html', port=0, host="0.0.0.0", mode="chrome-app")
