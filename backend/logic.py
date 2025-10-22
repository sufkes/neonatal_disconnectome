import logging
from utils import createControlSpaceDirectory, getRoundedAge
from .step1WarpSubjectToAgeMatchedTemplate import warpSubjectToAgeMatchedTemplate
from .step2ApplySubjectLesionToControlImageWarp import applySubjectLesionToControlImageWarp
from .step3GenerateVisitationMap import generateVisitationMap
from .step4WarpVisitationMapTo40wTemplate import warpVisitationMap
from .step5MakeDisconnectomeMap import generateDisconnectome

# Get the same logger used by the app's GUI logging setup
logger = logging.getLogger(__name__)

def step1(runs_dir, subject, image_type, moving_image, lesion_image, age):
  try:
    logger.debug(f"Starting step1 with subject={subject}, age={age}")
    createControlSpaceDirectory(subject, runs_dir)
    roundedAge = getRoundedAge(age)
    warpSubjectToAgeMatchedTemplate(runs_dir, subject, image_type, moving_image, lesion_image, roundedAge)
    logger.info(f"Step1 completed successfully for subject={subject}")
  except Exception as e:
    logger.error(f"Step1 failed for subject={subject}: {e}", exc_info=True)
    return False

  return True

def step2(runs_dir, subject, lesion_image, age, threshold = 0, image_type="T1w"):
  try:
    logger.debug(f"Starting step2 with subject={subject}, age={age}")
    roundedAge = getRoundedAge(age)
    applySubjectLesionToControlImageWarp(runs_dir, subject, lesion_image, roundedAge)
    generateVisitationMap(runs_dir, subject)
    warpVisitationMap(runs_dir, subject, image_type)
    generateDisconnectome(runs_dir, subject, image_type, threshold)
  except Exception as e:
    logger.exception("generate disconnectome failed", e)
    return False
  else:
    return True
