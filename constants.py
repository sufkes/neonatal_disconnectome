import os

CWD = os.getcwd()

TEMPLATE_DIR = os.path.join(CWD,'template')
TEMPLATE_MASK_DIR = os.path.join(TEMPLATE_DIR,'mask')
TEMPLATE_TEMPLATES_DIR = os.path.join(TEMPLATE_DIR,'templates')
TEMPLATE_WARPS_DIR = os.path.join(TEMPLATE_DIR,'warps-ants')


CONTROLS_DIR = os.path.join(CWD,'controls')

# constants for runs directory structure
CONTROL_SPACE = "control_space"
DISCONNECTOME = "disconnectome"
TEMPLATE_SPACE = "template_space"
VISITATION_MAPS_40W = "visitation_maps_40w"
