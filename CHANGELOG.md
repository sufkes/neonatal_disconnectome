# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [v1.0.6] — 2026-02-27

### Fixed

- Bug related to cli and validate, ci:  add changelog and version update actions

### Changed

- Bump version to 1.0.6
- Made sure version matches release

## [v1.0.5] — 2026-02-26

### Changed

- Fix bug with cli  bump version
- Update bibtext year
- Update placeholder email
- Update project structure in readme
- Changed from mermaid to just png generated from html
- Fix new line in mermaid diagram
- Update readme

## [v1.0.4] — 2026-02-26

### Changed

- Fixed bug with control space paths

## [v1.0.3] — 2026-02-26

### Changed

- Bump patch version number
- More minor bug fixes for mac build as well as improvement to threading and loading overlay

## [v1.0.2] — 2026-02-25

### Changed

- Update version
- Fix clickable command path when path has spaces
- Update version

## [v1.0.1] — 2026-02-25

### Changed

- Fix issue with certificate and ssl on macos

## [v1.0.0] — 2026-02-25

### Changed

- Fixed issue with log files path to write to user cache. added symlink for deb for cli
- Fix bug with appimage and file paths
- Fixed another type with windows release file name
- Fixed typo in spec file
- Update build step to include cli. fix cli to have download option
- Create LICENSE.txt
- Fixed typo in build file as well install fuse for linux
- Fix more bugs with build
- Fix workflow to release executables and update permisions for github action
- Fixed mistake in spec file
- Some fixes to get build script to work on github actions
- Upgrade GitHub Actions to latest versions
- Add GitHub Actions workflow for multi-platform builds
- Update version and date
- Fixed some minor issues with download functionality
- Made more fixes to threading
- Jaraco.text module not found fix
- Update to not include .tar.gz files
- Update docker ignore
- Update gitignore to remove data files
- More cleanup and fixes and updating of icon
- Update readme with detailed instructions
- Add build scripts as well as support for download data folder
- Fix for macos
- Fixed themeing and improved code as well as added build spec file
- Fixed and improved sidepanel and loading screen
- Added missing code from Steves changes
- Comment out filetypes
- Removed lib from gitignore
- Added statemanagement and cleaned up code
- New gui theme
- Trying tkinter full frontend
- Added lesion volume scaling
- Small minor gui fixes and changes
- Fixed copy command for the 4 images
- Fix issue with tkinter dialog window not showing up in foreground
- Fixed copy command. attempt to fix the file browser window
- Minor changes
- Updates based on feedback
- Fix disable file browse button to prevent multiple windows from opening
- Cleaned up how forms and form validation works
- Some fixed. updated and improved docker file
- Fixed issue with paths for image files
- Fixed issue with build
- More refactor cleanup and update of code
- Fixed final image generation
- Refactor and simplified front end code
- Reverted to python 3.11 for issues with ants python package
- Add arm64 to platform
- Added platform to docker compose
- Revert docker file to fix mac error
- Update docker file chamge image to ubuntu
- Update docker file to try to fix macos error
- Update docker file to include non root user
- Fixed bug with tkinter
- Added ability to skip first step. cleaned up code. deleted unused files
- Remove old scripts
- Refactor the code and update the ui
- Updated script and added remaining steps
- Add code for making lesion visitation maps
- Added some styling and fixed second step for warping lesion to control space
- Revert docker file
- Update docker file to fix hdf5 issue
- Update docker file
- Update dockerfile and requirements
- Update readme
- Initial commit of scripts which still rely on ANTS, FSL, and TrackVis
