import os

# Project root (one level up from this file's directory)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(PROJECT_ROOT, "data")

TEMPLATE_DIR = os.path.join(DATA_DIR, "template")
TEMPLATE_MASK_DIR = os.path.join(TEMPLATE_DIR, "mask")
TEMPLATE_TEMPLATES_DIR = os.path.join(TEMPLATE_DIR, "templates")
TEMPLATE_WARPS_DIR = os.path.join(TEMPLATE_DIR, "warps-ants")

CONTROLS_DIR = os.path.join(DATA_DIR, "controls")

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
