from pathlib import Path
import eel

from step1WarpSubjectToAgeMatchedTemplate import warpSubjectToAgeMatchedTemplate, createRunsDirectory
from step2ApplySubjectLesionToControlImageWarp import applySubjectLesionToControlImageWarp
from step3GenerateVisitationMap import generateVisitationMap
from step4WarpVisitationMapTo40wTemplate import warpVisitationMap
from step5MakeDisconnectomeMap import main



eel.init(str(Path(__file__).parent / "web"),
        allowed_extensions=[".html", ".js", ".css", ".woff", ".svg", ".svgz", ".png"])                     # Give folder containing web files

@eel.expose
def step1(subject, image_type, moving_image, lesion_image, age):
    createRunsDirectory(subject)
    warpSubjectToAgeMatchedTemplate(subject, image_type, moving_image, lesion_image, age)

@eel.expose
def step2(subject, moving_image, lesion_image, age):
    applySubjectLesionToControlImageWarp(subject, moving_image, lesion_image, age)

@eel.expose
def step3(subject):
    generateVisitationMap(subject)

@eel.expose
def step4(subject, image_type):
    warpVisitationMap(subject, image_type)

@eel.expose
def step5(subject, threshold):
    main(subject, threshold)

eel.start('templates/main.html', size=(300, 200), jinja_templates='templates', mode=None, host="0.0.0.0")    # Start
