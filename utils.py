from decimal import Decimal
import os

from constants import CONTROL_SPACE, CONTROLS_DIR, TEMPLATE_SPACE

def createRunsDirectory(subject, runs_dir):
  ## 1. Create the runs directory structure
  dir_list = [
    f.name for f in os.scandir(CONTROLS_DIR) if f.is_dir()
  ]
  for d in dir_list:
    sub_dir_list = [
      f.name for f in os.scandir(os.path.join(CONTROLS_DIR,d)) if f.is_dir()
    ]
    sub_name = d + '_' + sub_dir_list[0]
    path = os.path.join(runs_dir, subject, CONTROL_SPACE, sub_name)
    try:
      os.makedirs(path, exist_ok=True)
    except FileExistsError:
        print("Folder is already there")
    else:
        print("Folder was created")

def createTemplateSpaceDirectory(age, runs_dir, subject):
  ## 1. Create the template space runs directory structure to store result
  age_dir = age + "W"
  out_dir = os.path.join(runs_dir, subject, TEMPLATE_SPACE, age_dir)
  try:
    os.makedirs(out_dir, exist_ok=False)
  except FileExistsError:
      print("Folder is already there")
  else:
      print(f"created template space: {out_dir}")

  return out_dir


def path_to_dict(path):
    d = {'name': os.path.basename(path), 'path': os.path.abspath(path)}
    if os.path.isdir(path):
        d['type'] = "directory"
        d['children'] = [path_to_dict(os.path.join(path,x)) for x in os.listdir\
(path)]
    else:
        d['type'] = "file"
    return d


def getRoundedAge(age):
   roundedAge = round(Decimal(age))
   if(roundedAge < 28):
      return "28"
   if(roundedAge > 44):
      return "44"

   return str(roundedAge)
