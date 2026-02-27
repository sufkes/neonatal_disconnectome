import os
import sys
import tempfile
from pathlib import Path
import logging

# Setup basic logging for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_env_data_dir = os.environ.get("DISCONNECTOME_DATA_DIR")

if _env_data_dir:
    DATA_ROOT = Path(_env_data_dir)
    THUMBNAILS_DIR = DATA_ROOT.parent / "thumbnails"
    try:
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
        THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using data directory from DISCONNECTOME_DATA_DIR: {DATA_ROOT}")
    except PermissionError:
        logger.warning(
            f"Cannot create directory at {DATA_ROOT} due to permissions. "
            "Falling back to default."
        )
        _env_data_dir = None  # fall through to existing logic below

if not _env_data_dir:
    # Determine if running as bundled app or development
    if getattr(sys, "frozen", False):
        # Running as bundled app
        APPLICATION_PATH = Path(sys.executable).parent

        # Data should be in user's home directory
        if sys.platform == "darwin":  # macOS
            DATA_ROOT = (
                Path.home()
                / "Library"
                / "Application Support"
                / "Disconnectome"
                / "data"
            )
            THUMBNAILS_DIR = (
                Path.home() / "Library" / "Caches" / "Disconnectome" / "thumbnails"
            )
        elif sys.platform == "win32":  # Windows
            DATA_ROOT = Path(os.environ.get("APPDATA")) / "Disconnectome" / "data"
            THUMBNAILS_DIR = (
                Path(os.environ.get("LOCALAPPDATA")) / "Disconnectome" / "thumbnails"
            )
        else:  # Linux
            DATA_ROOT = Path.home() / ".local" / "share" / "Disconnectome" / "data"
            THUMBNAILS_DIR = Path.home() / ".cache" / "Disconnectome" / "thumbnails"

        # ✅ FIX: Add error handling with tempfile fallback
        try:
            DATA_ROOT.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using data directory: {DATA_ROOT}")
        except PermissionError:
            logger.warning(
                f"Cannot create data directory at {DATA_ROOT} due to permissions."
            )
            logger.warning("Falling back to temporary directory.")

            # Fallback to temp directory
            DATA_ROOT = Path(tempfile.gettempdir()) / "Disconnectome" / "data"
            DATA_ROOT.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using temporary data directory: {DATA_ROOT}")
            logger.warning(
                "Note: Data in temp directory may be deleted on system restart."
            )
        except Exception as e:
            logger.error(f"Unexpected error creating data directory: {e}")
            # Last resort fallback
            DATA_ROOT = Path(tempfile.gettempdir()) / "Disconnectome" / "data"
            DATA_ROOT.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using fallback temporary directory: {DATA_ROOT}")

    else:
        # Running in development - check for local data first
        PROJECT_ROOT = Path(__file__).parent.parent
        THUMBNAILS_DIR = PROJECT_ROOT / "thumbnails"
        LOCAL_DATA = PROJECT_ROOT / "data"

        # Use local data if it exists and has controls, otherwise use system location
        if LOCAL_DATA.exists() and (LOCAL_DATA / "controls").exists():
            DATA_ROOT = LOCAL_DATA
            logger.info(f"[DEV MODE] Using local data directory: {DATA_ROOT}")
        else:
            # Fall back to system location
            if sys.platform == "darwin":  # macOS
                DATA_ROOT = (
                    Path.home()
                    / "Library"
                    / "Application Support"
                    / "Disconnectome"
                    / "data"
                )
            elif sys.platform == "win32":  # Windows
                DATA_ROOT = Path(os.environ.get("APPDATA")) / "Disconnectome" / "data"
            else:  # Linux
                DATA_ROOT = Path.home() / ".local" / "share" / "Disconnectome" / "data"

            logger.info(f"[DEV MODE] No local data found, will use: {DATA_ROOT}")

            # ✅ FIX: Also add error handling in dev mode
            try:
                if not DATA_ROOT.exists():
                    DATA_ROOT.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                logger.warning(f"Cannot create {DATA_ROOT}, using temp directory")
                DATA_ROOT = Path(tempfile.gettempdir()) / "Disconnectome" / "data"
                DATA_ROOT.mkdir(parents=True, exist_ok=True)

# Project root (one level up from this file's directory)
DATA_DIR = str(DATA_ROOT)
TEMPLATE_DIR = DATA_ROOT / "template"
TEMPLATE_TEMPLATES_DIR = TEMPLATE_DIR / "templates"
TEMPLATE_WARPS_DIR = TEMPLATE_DIR / "warps-ants"
CONTROLS_DIR = DATA_ROOT / "controls"

THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
logger.info(f"Thumbnails directory: {THUMBNAILS_DIR}")

# Constants for runs directory structure
THUMBNAILS = "thumbnails"
CONTROL_SPACE = "control_space"
DISCONNECTOME = "disconnectome"
TEMPLATE_SPACE = "template_space"
VISITATION_MAPS_40W = "visitation_maps_40w"

# Thumbnail filenames
THUMBNAIL_BRAIN_IMAGE = "brain_image_thumbnail.png"
THUMBNAIL_ALIGNED_PAIR = "plot_aligned_image_pair.png"
THUMBNAIL_LESION_ORIGINAL = "lesion_on_original.png"
THUMBNAIL_LESION_TEMPLATE = "lesion_on_age_matched_template_clusters.png"
THUMBNAIL_DISCONNECTOME = "disconnectome_at_lesion_centroids_0.png"

# Version information — updated automatically by bump_version.py
__version__ = "1.0.6"
__build_date__ = "2026-02-27"
__author__ = "Steven Ufkes"

# Log final data directory location
logger.info(f"Data directory configured: {DATA_ROOT}")
logger.info(f"Application version: {__version__}")
