import os
import re
import sys
from pathlib import Path

import click

# ============================================================================
# IMPORTANT: backend modules are imported lazily via _load_backend() so that
# DISCONNECTOME_DATA_DIR is written to the environment BEFORE constants.py is
# first evaluated.  Do NOT add top-level "from backend..." or "from lib..."
# imports here — they would lock in the data directory before any --data-dir
# flag has been parsed.
# ============================================================================


def _load_backend():
    """
    Import backend modules on first call; subsequent calls are free (Python
    module cache).  Always call this after _apply_data_dir().
    """
    from types import SimpleNamespace
    from backend.logic import (
        step1_from_state,
        step2_from_state,
        process_warped_lesion_from_state,
    )
    from lib.state_management import ProcessingState, AppConfig
    from lib.data_downloader import DataDownloader

    return SimpleNamespace(
        step1_from_state=step1_from_state,
        step2_from_state=step2_from_state,
        process_warped_lesion_from_state=process_warped_lesion_from_state,
        ProcessingState=ProcessingState,
        AppConfig=AppConfig,
        DataDownloader=DataDownloader,
    )


def _apply_data_dir(data_dir):
    """
    Persist --data-dir into the environment so constants.py picks it up on
    its first import.  Must be called before _load_backend().
    """
    if data_dir:
        os.environ["DISCONNECTOME_DATA_DIR"] = str(Path(data_dir).resolve())


# ============================================================================
# VALIDATION HELPERS
# ============================================================================


def validate_subjectid(subjectid):
    if not re.match(r"^[A-Za-z0-9_-]+$", subjectid):
        click.secho(
            f"Error: Invalid subject ID '{subjectid}'. Only letters, numbers, "
            "underscore, and dash are allowed.",
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
# INTERACTIVE PROMPT HELPERS
# ============================================================================


def prompt_path(label, default=None, must_exist=True):
    """
    Prompt for a file/folder path with Tab autocomplete, re-prompting until
    it exists (if must_exist).

    Autocomplete is provided by readline on macOS/Linux. On Windows it requires
    pyreadline3 (pip install pyreadline3); if neither is available the prompt
    falls back gracefully to plain input.
    """
    import glob

    # ---- set up readline tab completion ----
    _readline_available = False
    try:
        import readline

        def _path_completer(text, state):
            """Complete file/directory paths, expanding ~ and env vars."""
            expanded = os.path.expandvars(os.path.expanduser(text))
            pattern = expanded + "*"
            matches = glob.glob(pattern)
            # Append os.sep to directories so the user can keep tabbing deeper
            matches = [(m + os.sep if os.path.isdir(m) else m) for m in matches]
            # Preserve the original prefix (e.g. ~/) in the returned match
            if text != expanded:
                prefix_len = len(expanded) - len(text)
                matches = [m[prefix_len:] for m in matches]
            try:
                return matches[state]
            except IndexError:
                return None

        readline.set_completer(_path_completer)
        # Prevent readline treating / and - as word delimiters
        readline.set_completer_delims(" \t\n;")
        if sys.platform == "darwin":
            readline.parse_and_bind("bind ^I rl_complete")  # macOS libedit
        else:
            readline.parse_and_bind("tab: complete")
        _readline_available = True
    except ImportError:
        pass  # Windows without pyreadline3 — plain prompt fallback

    hint = " [Tab to autocomplete]" if _readline_available else ""

    try:
        while True:
            value = click.prompt(f"{label}{hint}", default=default or "").strip()
            if not value:
                click.secho("  Path cannot be empty.", fg="yellow")
                continue
            value = os.path.expandvars(os.path.expanduser(value))
            if must_exist and not os.path.exists(value):
                click.secho(f"  Path not found: {value}", fg="yellow")
                continue
            return value
    finally:
        # Restore readline defaults so subsequent prompts are unaffected
        if _readline_available:
            readline.set_completer(None)
            readline.set_completer_delims(" \t\n")


def prompt_gestational_age(default=None):
    """Prompt for gestational age, re-prompting until valid."""
    while True:
        raw = click.prompt(
            "Gestational age in weeks (28-44)",
            default=str(default) if default is not None else "",
        ).strip()
        try:
            age = float(raw)
            return clamp_gestational_age(age)
        except ValueError:
            click.secho(
                "  Please enter a numeric value (e.g. 36 or 36.5).", fg="yellow"
            )


def prompt_brain_image_type(default=None):
    """Prompt for brain image type (T1w / T2w)."""
    choices = ["T1w", "T2w"]
    default_str = default if default in choices else "T2w"
    while True:
        value = click.prompt(
            f"Brain image type [{'/'.join(choices)}]",
            default=default_str,
        ).strip()
        if value in choices:
            return value
        click.secho(f"  Please enter one of: {', '.join(choices)}.", fg="yellow")


# ============================================================================
# DATA MANAGEMENT
# ============================================================================


def check_and_download_data(data_dir=None, auto_download=False):
    """
    Check that required data files are present.
    If missing, prompt the user to download them (or download automatically
    if --auto-download was passed).

    NOTE: _apply_data_dir() and _load_backend() must have been called before
    this function so that DataDownloader resolves the correct directory.
    """
    from lib.data_downloader import DataDownloader

    downloader = DataDownloader(data_dir=data_dir)

    if downloader.is_fully_installed():
        click.secho(f"Data files found at: {downloader.data_dir}", fg="green")
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
            bar = "#" * filled + "." * (bar_len - filled)
            click.echo(f"\r  [{bar}] {pct:3d}%  {filename}", nl=False)

    click.secho("Downloading data files...", fg="blue")
    success = downloader.download_all_required(progress_callback=_progress)
    click.echo()

    if not success:
        click.secho(
            "Download failed. Check your network connection and try again.",
            fg="red",
            err=True,
        )
        raise click.Abort()

    click.secho("Data files downloaded successfully.\n", fg="green")


# ============================================================================
# SHARED OPTIONS
# ============================================================================


def data_options(f):
    """Decorator that adds --data-dir and --auto-download to any command."""
    f = click.option(
        "--auto-download",
        "-a",
        is_flag=True,
        default=False,
        help="Download required data without prompting (useful for scripted/HPC use).",
    )(f)
    f = click.option(
        "--data-dir",
        "-d",
        type=click.Path(file_okay=False, dir_okay=True),
        default=None,
        envvar="DISCONNECTOME_DATA_DIR",
        help=(
            "Override the default data directory. "
            "Can also be set via the DISCONNECTOME_DATA_DIR environment variable. "
            "Useful on shared systems where data already exists on a network mount."
        ),
    )(f)
    return f


# ============================================================================
# COMMANDS
# ============================================================================


@click.group()
def cli():
    """CLI tool for brain image processing."""
    pass


@cli.command()
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    default=False,
    help="Prompt for any inputs not supplied as flags.",
)
@click.option(
    "--runsfolder",
    "-r",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=None,
    help="Path to the runs folder.",
)
@click.option(
    "--warped/--not-warped",
    "-w/-W",
    default=None,
    help="Specify whether the lesion mask is already warped to a dHCP template.",
)
@click.option(
    "--subjectid",
    "-s",
    type=str,
    default=None,
    help="Subject identifier (letters, numbers, underscore, dash only).",
)
@click.option(
    "--gestational-age",
    "-g",
    type=float,
    default=None,
    help="Gestational age in weeks (decimal allowed, will be clamped to 28-44).",
)
@click.option(
    "--brain-image-type",
    "-t",
    type=click.Choice(["T1w", "T2w"], case_sensitive=False),
    default=None,
    help="Type of brain image (T1w or T2w).",
)
@click.option(
    "--subject-brain-image",
    "-b",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default=None,
    help="Path to the subject brain image file. Required when --not-warped.",
)
@click.option(
    "--lesion-mask",
    "-l",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default=None,
    help="Path to the lesion mask file.",
)
@data_options
def start(
    interactive,
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

    Pass -i / --interactive to be prompted for any inputs not already supplied
    as flags. Flags always take precedence over prompts.
    """
    # ---- apply data dir FIRST, before any backend import ----
    _apply_data_dir(data_dir)
    backend = _load_backend()

    # ---- interactive prompts for missing values ----
    if interactive:
        click.secho("\n-- Start: interactive mode --", fg="cyan", bold=True)
        click.echo("  (Press Enter to accept a default; supplied flags are kept.)\n")

        if runsfolder is None:
            runsfolder = prompt_path("Runs folder (directory)", must_exist=True)

        if warped is None:
            warped = click.confirm(
                "Is the lesion mask already warped to a dHCP template?", default=False
            )

        if subjectid is None:
            while True:
                subjectid = click.prompt("Subject ID").strip()
                if re.match(r"^[A-Za-z0-9_-]+$", subjectid):
                    break
                click.secho(
                    "  Only letters, numbers, underscore, and dash are allowed.",
                    fg="yellow",
                )

        if gestational_age is None:
            gestational_age = prompt_gestational_age()

        if brain_image_type is None:
            brain_image_type = prompt_brain_image_type()

        if not warped and subject_brain_image is None:
            subject_brain_image = prompt_path(
                "Subject brain image file", must_exist=True
            )

        if lesion_mask is None:
            lesion_mask = prompt_path("Lesion mask file", must_exist=True)

        click.echo()

    # ---- non-interactive validation: require all flags ----
    else:
        missing = []
        if runsfolder is None:
            missing.append("--runsfolder")
        if warped is None:
            warped = False  # default to --not-warped when non-interactive
        if subjectid is None:
            missing.append("--subjectid")
        if gestational_age is None:
            missing.append("--gestational-age")
        if brain_image_type is None:
            missing.append("--brain-image-type")
        if lesion_mask is None:
            missing.append("--lesion-mask")
        if not warped and subject_brain_image is None:
            missing.append("--subject-brain-image")

        if missing:
            click.secho(
                f"Error: Missing required option(s): {', '.join(missing)}.\n"
                "       Re-run with -i / --interactive to be prompted instead.",
                fg="red",
                err=True,
            )
            raise SystemExit(1)

    # ---- data check ----
    check_and_download_data(data_dir=data_dir, auto_download=auto_download)

    # ---- shared validation ----
    subjectid = validate_subjectid(subjectid)
    gestational_age = clamp_gestational_age(gestational_age)

    if not warped and subject_brain_image is None:
        click.secho(
            "Error: --subject-brain-image is required when running --not-warped.",
            fg="red",
            err=True,
        )
        raise click.Abort()

    # ---- build state objects ----
    config = backend.AppConfig(runs_folder=runsfolder)

    processing = backend.ProcessingState(
        subject_id=subjectid,
        brain_type=brain_image_type,
        lesion_mask_path=lesion_mask,
        lesion_already_warped=warped,
    )

    if warped:
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
        click.secho("Running warped-lesion pipeline...", fg="blue")
        success = backend.process_warped_lesion_from_state(
            processing,
            config,
            progress_callback=lambda p, m: click.echo(f"  [{int(p * 100):3d}%] {m}"),
        )
    else:
        click.secho(
            "Running full pipeline (step 1: warp to age-matched template)...", fg="blue"
        )
        success = backend.step1_from_state(
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
    "--interactive",
    "-i",
    is_flag=True,
    default=False,
    help="Prompt for any inputs not supplied as flags.",
)
@click.option(
    "--runsfolder",
    "-r",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=None,
    help="Path to the runs folder.",
)
@click.option(
    "--gestational-age",
    "-g",
    type=float,
    default=None,
    help="Gestational age in weeks (decimal allowed, clamped to 28-44).",
)
@click.option(
    "--subjectid",
    "-s",
    type=str,
    default=None,
    help="Subject identifier (letters, numbers, underscore, dash only).",
)
@click.option(
    "--brain-image-type",
    "-t",
    type=click.Choice(["T1w", "T2w"], case_sensitive=False),
    default=None,
    help="Type of brain image (T1w or T2w).",
)
@click.option(
    "--lesion-mask",
    "-l",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default=None,
    help="Path to the lesion mask file.",
)
@data_options
def generate_disconnectome(
    interactive,
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

    Pass -i / --interactive to be prompted for any inputs not already supplied
    as flags. Flags always take precedence over prompts.
    """
    # ---- apply data dir FIRST, before any backend import ----
    _apply_data_dir(data_dir)
    backend = _load_backend()

    # ---- interactive prompts for missing values ----
    if interactive:
        click.secho(
            "\n-- Generate Disconnectome: interactive mode --", fg="cyan", bold=True
        )
        click.echo("  (Press Enter to accept a default; supplied flags are kept.)\n")

        if runsfolder is None:
            runsfolder = prompt_path(
                "Runs folder (directory, must contain step 1 outputs)", must_exist=True
            )

        if subjectid is None:
            while True:
                subjectid = click.prompt("Subject ID").strip()
                if re.match(r"^[A-Za-z0-9_-]+$", subjectid):
                    break
                click.secho(
                    "  Only letters, numbers, underscore, and dash are allowed.",
                    fg="yellow",
                )

        if gestational_age is None:
            gestational_age = prompt_gestational_age()

        if brain_image_type is None:
            brain_image_type = prompt_brain_image_type()

        if lesion_mask is None:
            lesion_mask = prompt_path("Lesion mask file", must_exist=True)

        click.echo()

    # ---- non-interactive validation ----
    else:
        missing = []
        if runsfolder is None:
            missing.append("--runsfolder")
        if subjectid is None:
            missing.append("--subjectid")
        if gestational_age is None:
            missing.append("--gestational-age")
        if brain_image_type is None:
            missing.append("--brain-image-type")
        if lesion_mask is None:
            missing.append("--lesion-mask")

        if missing:
            click.secho(
                f"Error: Missing required option(s): {', '.join(missing)}.\n"
                "       Re-run with -i / --interactive to be prompted instead.",
                fg="red",
                err=True,
            )
            raise SystemExit(1)

    # ---- data check ----
    check_and_download_data(data_dir=data_dir, auto_download=auto_download)

    subjectid = validate_subjectid(subjectid)
    gestational_age = clamp_gestational_age(gestational_age)

    # ---- build state objects ----
    config = backend.AppConfig(runs_folder=runsfolder)

    processing = backend.ProcessingState(
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

    click.secho("Running disconnectome step (step 2)...", fg="blue")
    success = backend.step2_from_state(
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
    # ---- apply data dir FIRST, before any backend import ----
    _apply_data_dir(data_dir)
    _load_backend()  # warm the module cache

    from lib.data_downloader import DataDownloader

    downloader = DataDownloader(data_dir=data_dir)
    status = downloader.check_installation()

    click.echo(f"\nData directory: {downloader.data_dir}\n")
    click.echo("Package status:")
    for package, installed in status.items():
        config = downloader.DATA_SOURCES[package]
        indicator = (
            click.style("installed", fg="green")
            if installed
            else click.style("missing", fg="red")
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
