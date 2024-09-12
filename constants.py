import os

BUNDLE_DIR = os.path.abspath(os.path.dirname(__file__))

CWD = os.getcwd()

TEMPLATE_DIR = os.path.join(BUNDLE_DIR,'template')
TEMPLATE_MASK_DIR = os.path.join(TEMPLATE_DIR,'mask')
TEMPLATE_TEMPLATES_DIR = os.path.join(TEMPLATE_DIR,'templates')
TEMPLATE_WARPS_DIR = os.path.join(TEMPLATE_DIR,'warps-ants')


CONTROLS_DIR = os.path.join(BUNDLE_DIR,'controls')

# constants for runs directory structure
CONTROL_SPACE = "control_space"
DISCONNECTOME = "disconnectome"
TEMPLATE_SPACE = "template_space"
VISITATION_MAPS_40W = "visitation_maps_40w"
