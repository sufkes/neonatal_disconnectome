import os
import sys
from pathlib import Path

# Determine if running as bundled app or development
if getattr(sys, "frozen", False):
    # Running as bundled app
    APPLICATION_PATH = Path(sys.executable).parent

    # Data should be in user's home directory
    if sys.platform == "darwin":  # macOS
        DATA_ROOT = (
            Path.home() / "Library" / "Application Support" / "Disconnectome" / "data"
        )
    elif sys.platform == "win32":  # Windows
        DATA_ROOT = Path(os.environ.get("APPDATA")) / "Disconnectome" / "data"
    else:  # Linux
        DATA_ROOT = Path.home() / ".local" / "share" / "Disconnectome" / "data"
else:
    # Running in development - check for local data first
    PROJECT_ROOT = Path(__file__).parent.parent
    LOCAL_DATA = PROJECT_ROOT / "data"

    # Use local data if it exists and has controls, otherwise use system location
    if LOCAL_DATA.exists() and (LOCAL_DATA / "controls").exists():
        DATA_ROOT = LOCAL_DATA
        print(f"[DEV MODE] Using local data directory: {DATA_ROOT}")
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
        print(f"[DEV MODE] No local data found, will use: {DATA_ROOT}")

# Project root (one level up from this file's directory)
DATA_DIR = str(DATA_ROOT)
TEMPLATE_DIR = DATA_ROOT / "template"
TEMPLATE_TEMPLATES_DIR = TEMPLATE_DIR / "templates"
TEMPLATE_WARPS_DIR = TEMPLATE_DIR / "warps-ants"
CONTROLS_DIR = DATA_ROOT / "controls"

THUMBNAILS_DIR = os.path.join(PROJECT_ROOT, "thumbnails")

# constants for runs directory structure
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


# Create directories if they don't exist (only for system locations)
if not getattr(sys, "frozen", False):
    # In dev mode with local data, don't create system dirs
    if not (Path(__file__).parent.parent / "data").exists():
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
else:
    # In bundled mode, always create system dirs
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
