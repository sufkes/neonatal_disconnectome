import logging
from logging.handlers import RotatingFileHandler

def configure_logging():
  logging.basicConfig(
      level=logging.DEBUG,
      format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
      datefmt='%m-%d %H:%M'
  )

  # Create a rotating file handler
  file_handler = RotatingFileHandler('disconnectome.log', maxBytes=100000, backupCount=5)
  file_handler.setLevel(logging.DEBUG)

  # Define a Handler which writes INFO messages or higher to the sys.stderr
  console = logging.StreamHandler()
  console.setLevel(logging.INFO)

  # Set a format that is simpler for console use
  formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
  console.setFormatter(formatter)

  # Add the handler to the root logger
  logging.getLogger('').addHandler(console)
  logging.getLogger('').addHandler(file_handler)
