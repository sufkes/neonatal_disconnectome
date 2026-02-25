import click
import re
import sys

from backend.logic import (
    step1_from_state,
    step2_from_state,
    process_warped_lesion_from_state,
)
from lib.state_management import ProcessingState, AppConfig
from lib.data_downloader import DataDownloader


@click.group()
def cli():
    """CLI tool for brain image processing."""
    pass


# ============================================================================
# VALIDATION HELPERS
# ============================================================================


def validate_subjectid(subjectid):
    if not re.match(r"^[A-Za-z0-9_-]+$", subjectid):
        click.secho(
            f"Error: Invalid subject ID '{subjectid}'. Only letters, numbers, underscore, and dash are allowed.",
            fg="red",
            err=True,
        )
        raise click.Abort()
    return subjectid


def clamp_gestational_age(age):
    if age < 28.0:
        click.secho(
            f"Warning: Provided gestational age {age} is below 28. Resetting to 28.",
            fg="yellow",
            err=True,
        )
        return 28.0
    elif age > 44.0:
        click.secho(
            f"Warning: Provided gestational age {age} is above 44. Resetting to 44.",
            fg="yellow",
            err=True,
        )
        return 44.0
    return age


# ============================================================================
# DATA MANAGEMENT
# ============================================================================


def check_and_download_data(data_dir=None, auto_download=False):
    """
    Check that required data files are present.
    If missing, prompt the user to download them (or download automatically
    if --auto-download was passed).
    """
    downloader = DataDownloader(data_dir=data_dir)

    if downloader.is_fully_installed():
        click.secho(f"✓ Data files found at: {downloader.data_dir}", fg="green")
        return

    missing = downloader.get_missing_packages()
    info = downloader.get_download_info()

    click.secho("\nRequired data files are not installed.", fg="yellow")
    click.echo(f"  Missing packages : {', '.join(missing)}")
    click.echo(f"  Download size    : ~{info['total_size_mb']} MB")
    click.echo(f"  Install location : {downloader.data_dir}\n")

    if not auto_download:
        if not sys.stdin.isatty():
            click.secho(
                "Non-interactive session detected and data is missing. "
                "Re-run with --auto-download to download automatically.",
                fg="red",
                err=True,
            )
            raise click.Abort()

        if not click.confirm("Download required data now?"):
            click.secho(
                "Cannot proceed without data files. Exiting.", fg="red", err=True
            )
            raise click.Abort()

    def _progress(filename, done, total):
        if total > 0:
            pct = int(done / total * 100)
            bar_len = 30
            filled = int(bar_len * done / total)
            bar = "█" * filled + "░" * (bar_len - filled)
            click.echo(f"\r  [{bar}] {pct:3d}%  {filename}", nl=False)

    click.secho("Downloading data files…", fg="blue")
    success = downloader.download_all_required(progress_callback=_progress)
    click.echo()

    if not success:
        click.secho(
            "Download failed. Check your network connection and try again.",
            fg="red",
            err=True,
        )
        raise click.Abort()

    click.secho("✓ Data files downloaded successfully.\n", fg="green")


# ============================================================================
# SHARED OPTIONS
# ============================================================================


def data_options(f):
    """Decorator that adds --data-dir and --auto-download to any command."""
    f = click.option(
        "--auto-download",
        is_flag=True,
        default=False,
        help="Download required data without prompting (useful for scripted/HPC use).",
    )(f)
    f = click.option(
        "--data-dir",
        type=click.Path(file_okay=False, dir_okay=True),
        default=None,
        help=(
            "Override the default data directory. "
            "Useful on shared systems where data already exists on a network mount."
        ),
    )(f)
    return f


# ============================================================================
# COMMANDS
# ============================================================================


@cli.command()
@click.option(
    "--runsfolder",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=True,
    help="Path to the runs folder.",
)
@click.option(
    "--warped/--not-warped",
    default=False,
    help="Specify whether the lesion mask is already warped to a dHCP template.",
)
@click.option(
    "--subjectid",
    type=str,
    required=True,
    help="Subject identifier (letters, numbers, underscore, dash only).",
)
@click.option(
    "--gestational-age",
    type=float,
    required=True,
    help="Gestational age in weeks (decimal allowed, will be clamped to 28–44).",
)
@click.option(
    "--brain-image-type",
    type=click.Choice(["T1w", "T2w"], case_sensitive=False),
    required=True,
    help="Type of brain image (T1w or T2w).",
)
@click.option(
    "--subject-brain-image",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default=None,
    help="Path to the subject brain image file. Required when --not-warped.",
)
@click.option(
    "--lesion-mask",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    required=True,
    help="Path to the lesion mask file.",
)
@data_options
def start(
    runsfolder,
    warped,
    subjectid,
    gestational_age,
    brain_image_type,
    subject_brain_image,
    lesion_mask,
    data_dir,
    auto_download,
):
    """
    Process brain imaging data.

    Use --not-warped (default) for a full pipeline starting from the raw
    subject brain image. Use --warped when the lesion mask has already been
    registered to a dHCP template and you want to skip straight to
    disconnectome generation.
    """
    # ---- data check first ----
    check_and_download_data(data_dir=data_dir, auto_download=auto_download)

    # ---- input validation ----
    subjectid = validate_subjectid(subjectid)
    gestational_age = clamp_gestational_age(gestational_age)

    if not warped and subject_brain_image is None:
        click.secho(
            "Error: --subject-brain-image is required when running --not-warped.",
            fg="red",
            err=True,
        )
        raise click.Abort()

    # ---- build state objects (backend interface) ----
    config = AppConfig(runs_folder=runsfolder)

    processing = ProcessingState(
        subject_id=subjectid,
        brain_type=brain_image_type,
        lesion_mask_path=lesion_mask,
        lesion_already_warped=warped,
    )

    if warped:
        # template_age is what process_warped_lesion_from_state uses
        processing.template_age = str(gestational_age)
    else:
        processing.gestational_age = str(gestational_age)
        processing.brain_image_path = subject_brain_image

    click.echo("Parameters:")
    click.echo(f"  Runs folder        : {runsfolder}")
    click.echo(f"  Warped             : {warped}")
    click.echo(f"  Subject ID         : {subjectid}")
    click.echo(f"  Gestational Age    : {gestational_age} weeks")
    click.echo(f"  Brain Image Type   : {brain_image_type}")
    click.echo(f"  Subject Brain Image: {subject_brain_image}")
    click.echo(f"  Lesion Mask        : {lesion_mask}")

    # ---- dispatch to backend ----
    if warped:
        click.secho("Running warped-lesion pipeline…", fg="blue")
        success = process_warped_lesion_from_state(
            processing,
            config,
            progress_callback=lambda p, m: click.echo(f"  [{int(p * 100):3d}%] {m}"),
        )
    else:
        click.secho(
            "Running full pipeline (step 1: warp to age-matched template)…", fg="blue"
        )
        success = step1_from_state(
            processing,
            config,
            progress_callback=lambda p, m: click.echo(f"  [{int(p * 100):3d}%] {m}"),
        )

    if not success:
        click.secho("Processing failed. Check logs for details.", fg="red", err=True)
        raise SystemExit(1)

    click.secho("Processing complete.", fg="green")


@cli.command()
@click.option(
    "--runsfolder",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=True,
    help="Path to the runs folder.",
)
@click.option(
    "--gestational-age",
    type=float,
    required=True,
    help="Gestational age in weeks (decimal allowed, clamped to 28–44).",
)
@click.option(
    "--subjectid",
    type=str,
    required=True,
    help="Subject identifier (letters, numbers, underscore, dash only).",
)
@click.option(
    "--brain-image-type",
    type=click.Choice(["T1w", "T2w"], case_sensitive=False),
    required=True,
    help="Type of brain image (T1w or T2w).",
)
@click.option(
    "--lesion-mask",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    required=True,
    help="Path to the lesion mask file.",
)
@data_options
def generate_disconnectome(
    runsfolder,
    gestational_age,
    subjectid,
    brain_image_type,
    lesion_mask,
    data_dir,
    auto_download,
):
    """
    Generate disconnectome from an already-warped runs folder.

    Assumes step 1 (warp to age-matched template) has already been completed
    and its outputs are present in --runsfolder.
    """
    # ---- data check first ----
    check_and_download_data(data_dir=data_dir, auto_download=auto_download)

    subjectid = validate_subjectid(subjectid)
    gestational_age = clamp_gestational_age(gestational_age)

    # ---- build state objects (backend interface) ----
    config = AppConfig(runs_folder=runsfolder)

    processing = ProcessingState(
        subject_id=subjectid,
        brain_type=brain_image_type,
        lesion_mask_path=lesion_mask,
        gestational_age=str(gestational_age),
        step1_completed=True,  # tell backend step 1 is already done
    )

    click.echo("Generating disconnectome with parameters:")
    click.echo(f"  Runs folder     : {runsfolder}")
    click.echo(f"  Gestational Age : {gestational_age}")
    click.echo(f"  Subject ID      : {subjectid}")
    click.echo(f"  Brain Image Type: {brain_image_type}")
    click.echo(f"  Lesion Mask     : {lesion_mask}")

    click.secho("Running disconnectome step (step 2)…", fg="blue")
    success = step2_from_state(
        processing,
        config,
        progress_callback=lambda p, m: click.echo(f"  [{int(p * 100):3d}%] {m}"),
    )

    if not success:
        click.secho(
            "Disconnectome generation failed. Check logs for details.",
            fg="red",
            err=True,
        )
        raise SystemExit(1)

    click.secho("Disconnectome generation complete.", fg="green")


@cli.command()
@data_options
def check_data(data_dir, auto_download):
    """
    Check whether required data files are installed, and optionally download them.

    Useful for verifying or pre-populating data on a new machine before
    submitting a batch job.
    """
    downloader = DataDownloader(data_dir=data_dir)
    status = downloader.check_installation()

    click.echo(f"\nData directory: {downloader.data_dir}\n")
    click.echo("Package status:")
    for package, installed in status.items():
        config = downloader.DATA_SOURCES[package]
        indicator = (
            click.style("✓ installed", fg="green")
            if installed
            else click.style("✗ missing", fg="red")
        )
        click.echo(f"  {package:<12} ({config['size_mb']} MB)  {indicator}")
        click.echo(f"               {config['description']}")

    click.echo()

    if not downloader.is_fully_installed():
        check_and_download_data(data_dir=data_dir, auto_download=auto_download)
    else:
        click.secho("All required data is installed.", fg="green")


if __name__ == "__main__":
    cli()
