from pathlib import Path
import os
import json
import eel

from tkinter import *
import tkinter.filedialog as fdialog

from step1WarpSubjectToAgeMatchedTemplate import warpSubjectToAgeMatchedTemplate
from step2ApplySubjectLesionToControlImageWarp import applySubjectLesionToControlImageWarp
from step3GenerateVisitationMap import generateVisitationMap
from step4WarpVisitationMapTo40wTemplate import warpVisitationMap
from step5MakeDisconnectomeMap import main
from utils import createRunsDirectory, createTemplateSpaceDirectory, getRoundedAge, path_to_dict


eel.init(str(Path(__file__).parent / "web"),
        allowed_extensions=[".html", ".js", ".css", ".woff", ".svg", ".svgz", ".png"])
        # Give folder containing web files

@eel.expose
def getFolder():
  root = Tk()
  root.withdraw()
  root.wm_attributes('-topmost', 1)
  folder = fdialog.askdirectory()
  return folder

@eel.expose
def getFile():
  root = Tk()
  root.withdraw()
  root.wm_attributes('-topmost', 1)
  file = fdialog.askopenfile(mode='r', filetypes=[('NIFTI Files', '*.nii.gz')])
  print(file)
  filepath = ""
  if file:
    filepath = os.path.abspath(file.name)
  return filepath

@eel.expose
def showFiles(runs_dir):
    print(runs_dir)
    return json.dumps(path_to_dict(runs_dir))

@eel.expose
def step1(runs_dir, subject, image_type, moving_image, lesion_image, age):
    try:
      createRunsDirectory(subject, runs_dir)
      roundedAge = getRoundedAge(age)
      warpSubjectToAgeMatchedTemplate(runs_dir, subject, image_type, moving_image, lesion_image, roundedAge)
    except Exception as e:
      print("step1 failed: ", e)
      return e
    else:
      return True

@eel.expose
def step1A(runs_dir, subject, lesion_image, age, image_type="T1w", threshold = 0):
    try:
      createRunsDirectory(subject, runs_dir)
      createTemplateSpaceDirectory(age, runs_dir, subject)
      roundedAge = getRoundedAge(age)
      applySubjectLesionToControlImageWarp(runs_dir, subject, lesion_image, roundedAge, skip=True)
      generateVisitationMap(runs_dir, subject)
      warpVisitationMap(runs_dir, subject, image_type)
      main(runs_dir, subject, threshold)
    except Exception as e:
      print("step1A failed: ", e)
      return e
    else:
      return True

@eel.expose
def step2(runs_dir, subject, lesion_image, age, threshold = 0, image_type="T1w"):
    try:
      print(age)
      print(type(age))
      roundedAge = getRoundedAge(age)
      applySubjectLesionToControlImageWarp(runs_dir, subject, lesion_image, roundedAge)
      generateVisitationMap(runs_dir, subject)
      warpVisitationMap(runs_dir, subject, image_type)
      main(runs_dir, subject, threshold)
    except Exception as e:
      print("step2 failed: ", e)
      return e
    else:
      return True

eel.start('templates/main.html', size=(300, 200), jinja_templates='templates', mode='chrome-app', port=8080, cmdline_args=['--start-fullscreen', '--browser-startup-dialog'], host="0.0.0.0")    # Start
