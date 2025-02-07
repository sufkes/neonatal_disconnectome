from decimal import Decimal
import os

from constants import CONTROL_SPACE, CONTROLS_DIR, DISCONNECTOME, TEMPLATE_SPACE

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

def createDisconnectomeDirectory(runs_dir, subject):
  runs_path = os.path.join(runs_dir, subject)
  disconnectome_out_dir = os.path.join(runs_path, DISCONNECTOME)
  try:
    os.makedirs(disconnectome_out_dir, exist_ok=False)
  except FileExistsError:
      print("Folder is already there")
  else:
      print(f"created disconnectome directory: {disconnectome_out_dir}")

  return disconnectome_out_dir


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


def deleteImagefiles():
  for imageFile in os.listdir("web/img/"):
    root, ext = os.path.splitext(imageFile)
    if (root.startswith('brain_image_thumbnail')
        or
        root.startswith('plot_aligned_image_pair')
        or
        root.startswith('lesion_on_age_matched_template_clusters')
        or
        root.startswith('lesion_on_original')
        or
        root.startswith('disconnectome_at_lesion_centroids')) and ext == '.png':
      try:
        os.remove("web/img/"+imageFile)
      except OSError as e:
        # If it fails, inform the user.
        print("Error: %s - %s." % (e.filename, e.strerror))
