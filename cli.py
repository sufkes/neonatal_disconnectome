import click
import re

from step1WarpSubjectToAgeMatchedTemplate import warpSubjectToAgeMatchedTemplate
from step2ApplySubjectLesionToControlImageWarp import applySubjectLesionToControlImageWarp
from step3GenerateVisitationMap import generateVisitationMap
from step4WarpVisitationMapTo40wTemplate import warpVisitationMap
from step5MakeDisconnectomeMap import generateDisconnectome

from utils import createControlSpaceDirectory, createTemplateSpaceDirectory, deleteImagefiles, getRoundedAge

@click.group()
def cli():
  """CLI tool for brain image processing."""
  pass

def validate_subjectid(subjectid):
  if not re.match(r'^[A-Za-z0-9_-]+$', subjectid):
    click.secho(
        f"Error: Invalid subject ID '{subjectid}'. Only letters, numbers, underscore, and dash are allowed.",
        fg="red",
        err=True
    )
    raise click.Abort()
  return subjectid.upper()

def clamp_gestational_age(age):
  if age < 28.0:
    click.secho(f"Warning: Provided gestational age {age} is below 28. Resetting to 28.", fg="yellow", err=True)
    return 28.0
  elif age > 44.0:
    click.secho(f"Warning: Provided gestational age {age} is above 44. Resetting to 44.", fg="yellow", err=True)
    return 44.0
  return age

@cli.command()
@click.option("--runsfolder", type=click.Path(exists=True, file_okay=False, dir_okay=True), required=True,
              help="Path to the runs folder.")
@click.option("--warped/--not-warped", default=False,
              help="Specify whether the image data is warped.")
@click.option("--subjectid", type=str, required=True,
              help="Subject identifier (letters, numbers, underscore, dash only).")
@click.option("--gestational-age", type=float, required=True,
              help="Gestational age in weeks (decimal allowed, will be clamped to 28–44).")
@click.option("--brain-image-type", type=click.Choice(["T1w", "T2w"], case_sensitive=False), required=True,
              help="Type of brain image (T1w or T2w).")
@click.option("--subject-brain-image", type=click.Path(exists=True, file_okay=True, dir_okay=False), required=True,
              help="Path to the subject brain image file.")
@click.option("--lesion-mask", type=click.Path(exists=True, file_okay=True, dir_okay=False), required=True,
              help="Path to the lesion mask file.")
def start(runsfolder, warped, subjectid, gestational_age, brain_image_type, subject_brain_image, lesion_mask):
  """
  Process brain imaging data, with conditional arguments based on warped flag.
  """
  subjectid = validate_subjectid(subjectid)
  gestational_age = clamp_gestational_age(gestational_age)

  # Conditional validation based on warped flag
  if warped:
    # Only subjectid, lesion_mask, and gestational_age required - already checked lesion_mask required by decorator
    if any([runsfolder, brain_image_type, subject_brain_image]):
      click.secho("Warning: When --warped is set, other options except --subjectid, --lesion-mask, and --gestational-age are ignored.", fg="yellow", err=True)
  else:
    # Not warped, brain_image_type, runsfolder, subject_brain_image required
    missing = []
    if runsfolder is None:
      missing.append("--runsfolder")
    if brain_image_type is None:
      missing.append("--brain-image-type")
    if subject_brain_image is None:
      missing.append("--subject-brain-image")
    if missing:
      click.secho(f"Error: Missing required options for not warped run: {', '.join(missing)}", fg="red", err=True)
      raise click.Abort()

  click.echo("Received arguments:")
  click.echo(f"Runs folder: {runsfolder}")
  click.echo(f"Warped: {warped}")
  click.echo(f"Subject ID: {subjectid}")
  click.echo(f"Gestational Age: {gestational_age} weeks")
  click.echo(f"Brain Image Type: {brain_image_type}")
  click.echo(f"Subject Brain Image: {subject_brain_image}")
  click.echo(f"Lesion Mask: {lesion_mask}")

  deleteImagefiles()
  roundedAge = getRoundedAge(gestational_age)
  createControlSpaceDirectory(subjectid, runsfolder)

  if warped:
    click.secho("Generating disconnectome.", fg="blue")
    createTemplateSpaceDirectory(roundedAge, runsfolder, subjectid)
    applySubjectLesionToControlImageWarp(runsfolder, subjectid, lesion_mask, roundedAge, skip=True)
    generateVisitationMap(runsfolder, subjectid)
    warpVisitationMap(runsfolder, subjectid, brain_image_type)
    generateDisconnectome(runsfolder, subjectid, brain_image_type, None, 0)
  else:
    click.secho("Warping subject to age matched template.", fg="blue")
    warpSubjectToAgeMatchedTemplate(runsfolder, subjectid, brain_image_type, subject_brain_image, lesion_mask, roundedAge, None)

  click.secho("Processing complete.", fg="green")

@cli.command()
@click.option("--runsfolder", type=click.Path(exists=True, file_okay=False, dir_okay=True), required=True,
              help="Path to the runs folder.")
@click.option("--gestational-age", type=float, required=True,
              help="Gestational age in weeks (decimal allowed, clamped to 28–44).")
@click.option("--subjectid", type=str, required=True,
              help="Subject identifier (letters, numbers, underscore, dash only; auto-converted to uppercase).")
@click.option("--brain-image-type", type=click.Choice(["T1w", "T2w"], case_sensitive=False), required=True,
              help="Type of brain image (T1w or T2w).")
@click.option("--lesion-mask", type=click.Path(exists=True, file_okay=True, dir_okay=False), required=True,
              help="Path to the lesion mask file.")
def generate_disconnectome(runsfolder, gestational_age, subjectid, brain_image_type, lesion_mask):
  """
  Generate disconnectome from runs folder, subject id, age, image type, and lesion mask.
  """
  subjectid = validate_subjectid(subjectid)
  gestational_age = clamp_gestational_age(gestational_age)

  roundedAge = getRoundedAge(gestational_age)

  click.echo("Generating disconnectome with parameters:")
  click.echo(f"Runs folder: {runsfolder}")
  click.echo(f"Gestational Age: {gestational_age}")
  click.echo(f"Subject ID: {subjectid}")
  click.echo(f"Brain Image Type: {brain_image_type}")
  click.echo(f"Lesion Mask: {lesion_mask}")

  applySubjectLesionToControlImageWarp(runsfolder, subjectid, lesion_mask, roundedAge)
  generateVisitationMap(runsfolder, subjectid)
  warpVisitationMap(runsfolder, subjectid, brain_image_type)
  generateDisconnectome(runsfolder, subjectid, brain_image_type, None, 0)

  # Placeholder for your disconnectome generation logic
  click.secho("Disconnectome generation complete.", fg="green")

if __name__ == "__main__":
  cli()
