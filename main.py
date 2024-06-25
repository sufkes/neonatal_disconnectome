from pathlib import Path
from warpSubjectToAgeMatchedTemplate import warpSubjectToAgeMatchedTemplate, createRunsDirectory
from warpLesionToControlSpace import warpLesionToControlSpace

import eel

eel.init(str(Path(__file__).parent / "web"),
        allowed_extensions=[".html", ".js", ".css", ".woff", ".svg", ".svgz", ".png"])                     # Give folder containing web files

@eel.expose
def step1(subject, image_type, moving_image, lesion_image, age):
    createRunsDirectory(subject)
    warpSubjectToAgeMatchedTemplate(subject, image_type, moving_image, lesion_image, age)

@eel.expose
def step2(subject, moving_image, lesion_image, age):
    warpLesionToControlSpace(subject, moving_image, lesion_image, age)

eel.start('templates/main.html', size=(300, 200), jinja_templates='templates', mode=None, host="0.0.0.0")    # Start
