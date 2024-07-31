from decimal import Decimal
from pathlib import Path
import os
import json
import eel

from tkinter import *
import tkinter.filedialog as fdialog

from step1WarpSubjectToAgeMatchedTemplate import warpSubjectToAgeMatchedTemplate, createRunsDirectory
from step2ApplySubjectLesionToControlImageWarp import applySubjectLesionToControlImageWarp
from step3GenerateVisitationMap import generateVisitationMap
from step4WarpVisitationMapTo40wTemplate import warpVisitationMap
from step5MakeDisconnectomeMap import main


eel.init(str(Path(__file__).parent / "web"),
        allowed_extensions=[".html", ".js", ".css", ".woff", ".svg", ".svgz", ".png"])
        # Give folder containing web files

def path_to_dict(path):
    d = {'name': os.path.basename(path), 'path': os.path.abspath(path)}
    if os.path.isdir(path):
        d['type'] = "directory"
        d['children'] = [path_to_dict(os.path.join(path,x)) for x in os.listdir\
(path)]
    else:
        d['type'] = "file"
    return d

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
    print(json.dumps(path_to_dict(runs_dir)))
    files = [os.path.join(dirpath,f) for (dirpath, dirnames, filenames) in os.walk(runs_dir) for f in filenames]
    print(files)
    return json.dumps(path_to_dict(runs_dir))

@eel.expose
def step1(runs_dir, subject, image_type, moving_image, lesion_image, age):
    try:
      createRunsDirectory(subject, runs_dir)
      roundedAge = str(round(Decimal(age)))
      warpSubjectToAgeMatchedTemplate(runs_dir, subject, image_type, moving_image, lesion_image, roundedAge)
    except Exception as e:
      print("step1 failed: ", e)
      return e
    else:
      return True

@eel.expose
def step2(runs_dir, subject, image_type, lesion_image, age, threshold = 0):
    try:
      roundedAge = str(round(Decimal(age)))
      applySubjectLesionToControlImageWarp(runs_dir, subject, lesion_image, roundedAge)
      generateVisitationMap(runs_dir, subject)
      warpVisitationMap(runs_dir, subject, image_type)
      main(runs_dir, subject, threshold)
    except Exception as e:
      return e
    else:
      return True

@eel.expose
def step3(runs_dir, subject):
    result = generateVisitationMap(runs_dir, subject)
    return result

@eel.expose
def step4(runs_dir, subject, image_type):
    result = warpVisitationMap(runs_dir, subject, image_type)
    return result

@eel.expose
def step5(runs_dir, subject, threshold):
    result = main(runs_dir, subject, threshold)
    return result

eel.start('templates/main.html', size=(300, 200), jinja_templates='templates', mode=None, host="0.0.0.0")    # Start
