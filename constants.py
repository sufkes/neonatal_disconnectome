from pathlib import Path

cwd = Path.cwd()

TEMPLATE_DIR = cwd / 'template'
TEMPLATE_MASK_DIR = TEMPLATE_DIR / 'mask'
TEMPLATE_TEMPLATES_DIR = TEMPLATE_DIR / 'templates'
TEMPLATE_WARPS_DIR = TEMPLATE_DIR / 'warps-ants'

RUNS_DIR = cwd / 'runs'

CONTROLS_DIR = cwd / 'controls'
