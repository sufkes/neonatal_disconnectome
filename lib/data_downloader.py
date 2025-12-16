"""
Data Downloader Module

Handles downloading and managing large data files on first run.
Supports multiple hosting options: S3, GitHub Releases, institutional servers, etc.
"""

import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, List
import urllib.request
import urllib.error
import zipfile
import tarfile
import shutil

logger = logging.getLogger("disconnectome")


class DataDownloader:
    """
    Manages downloading and verifying large data files
    """

    # Configuration for data sources
    # You'll update these URLs to point to your actual data hosting
    DATA_SOURCES = {
        "controls": {
            "url": "https://your-server.edu/disconnectome/controls.tar.gz",
            "md5": "78d1353481151aeaec8d5d0c74b3ab89",  # MD5 hash for verification
            "size_mb": 500,  # Approximate size for progress display
            "required": True,
            "description": "Control subject tractography data",
        },
        "template": {
            "url": "https://your-server.edu/disconnectome/template.tar.gz",
            "md5": "e82bcba92123638b001efe6353df62c0",
            "size_mb": 3000,
            "required": True,
            "description": "dHCP brain templates (28-44 weeks) and warps",
        },
    }

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize data downloader

        Args:
            data_dir: Directory to store downloaded data
                     Defaults to user's application data directory
        """
        self.data_dir = Path(data_dir) if data_dir else self._get_default_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Track download progress
        self.current_file = ""
        self.bytes_downloaded = 0
        self.total_bytes = 0
        self.progress_callback: Optional[Callable] = None

        logger.info(f"Data directory: {self.data_dir}")

    def _get_default_data_dir(self) -> Path:
        """Get platform-specific data directory"""
        if sys.platform == "darwin":  # macOS
            base = Path.home() / "Library" / "Application Support"
        elif sys.platform == "win32":  # Windows
            base = Path(os.environ.get("APPDATA", Path.home()))
        else:  # Linux
            base = Path.home() / ".local" / "share"

        return base / "Disconnectome" / "data"

    def check_installation(self) -> Dict[str, bool]:
        """
        Check which data packages are installed

        Returns:
            Dictionary mapping package name to installation status
        """
        status = {}

        for package_name, config in self.DATA_SOURCES.items():
            # Check if marker file exists (created after successful extraction)
            marker_file = self.data_dir / f".{package_name}.installed"
            status[package_name] = marker_file.exists()

        return status

    def is_fully_installed(self) -> bool:
        """Check if all required packages are installed"""
        status = self.check_installation()
        return all(
            status.get(name, False)
            for name, config in self.DATA_SOURCES.items()
            if config["required"]
        )

    def get_missing_packages(self) -> List[str]:
        """Get list of missing required packages"""
        status = self.check_installation()
        return [
            name
            for name, config in self.DATA_SOURCES.items()
            if config["required"] and not status.get(name, False)
        ]

    def download_package(
        self,
        package_name: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> bool:
        """
        Download and install a data package

        Args:
            package_name: Name of package to download (from DATA_SOURCES)
            progress_callback: Optional callback(filename, bytes_done, bytes_total)

        Returns:
            True if successful, False otherwise
        """
        if package_name not in self.DATA_SOURCES:
            logger.error(f"Unknown package: {package_name}")
            return False

        config = self.DATA_SOURCES[package_name]
        self.progress_callback = progress_callback

        try:
            # Download
            logger.info(f"Downloading {package_name} from {config['url']}")
            archive_path = self._download_file(
                config["url"], package_name, config["size_mb"]
            )

            # Verify
            if config.get("md5"):
                logger.info(f"Verifying {package_name}...")
                if not self._verify_md5(archive_path, config["md5"]):
                    logger.error(f"MD5 verification failed for {package_name}")
                    return False

            # Extract
            logger.info(f"Extracting {package_name}...")
            if not self._extract_archive(archive_path, package_name):
                return False

            # Create marker file
            marker_file = self.data_dir / f".{package_name}.installed"
            marker_file.write_text(
                json.dumps({"version": "1.0", "installed": True, "url": config["url"]})
            )

            # Clean up archive
            archive_path.unlink()

            logger.info(f"Successfully installed {package_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to download {package_name}: {e}", exc_info=True)
            return False

    def _download_file(self, url: str, package_name: str, size_mb: int) -> Path:
        """
        Download a file with progress tracking

        Returns:
            Path to downloaded file
        """
        # Determine filename from URL
        filename = url.split("/")[-1]
        output_path = self.data_dir / f"{package_name}.download"

        self.current_file = filename
        self.bytes_downloaded = 0
        self.total_bytes = size_mb * 1024 * 1024  # Approximate

        def report_progress(block_num, block_size, total_size):
            """Progress callback for urllib"""
            self.bytes_downloaded = block_num * block_size
            if total_size > 0:
                self.total_bytes = total_size

            if self.progress_callback:
                self.progress_callback(
                    filename, self.bytes_downloaded, self.total_bytes
                )

        try:
            urllib.request.urlretrieve(url, output_path, reporthook=report_progress)
            return output_path

        except urllib.error.URLError as e:
            logger.error(f"Network error downloading {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            raise

    def _verify_md5(self, file_path: Path, expected_md5: str) -> bool:
        """Verify file MD5 hash"""
        md5_hash = hashlib.md5()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)

        actual_md5 = md5_hash.hexdigest()

        if actual_md5 != expected_md5:
            logger.error(f"MD5 mismatch: expected {expected_md5}, got {actual_md5}")
            return False

        return True

    def _extract_archive(self, archive_path: Path, package_name: str) -> bool:
        """Extract archive to data directory"""
        try:
            # Determine archive type
            if archive_path.suffix == ".zip":
                return self._extract_zip(archive_path, package_name)
            elif archive_path.suffixes[-2:] == [".tar", ".gz"]:
                return self._extract_targz(archive_path, package_name)
            else:
                logger.error(f"Unknown archive format: {archive_path}")
                return False

        except Exception as e:
            logger.error(f"Failed to extract {archive_path}: {e}", exc_info=True)
            return False

    def _extract_zip(self, archive_path: Path, package_name: str) -> bool:
        """Extract ZIP archive"""
        extract_dir = self.data_dir / package_name
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        return True

    def _extract_targz(self, archive_path: Path, package_name: str) -> bool:
        """Extract tar.gz archive"""
        extract_dir = self.data_dir / package_name
        extract_dir.mkdir(parents=True, exist_ok=True)

        with tarfile.open(archive_path, "r:gz") as tar_ref:
            tar_ref.extractall(extract_dir)

        return True

    def download_all_required(
        self, progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> bool:
        """
        Download all required packages

        Returns:
            True if all successful, False otherwise
        """
        missing = self.get_missing_packages()

        if not missing:
            logger.info("All required packages already installed")
            return True

        logger.info(f"Downloading {len(missing)} packages: {missing}")

        for package_name in missing:
            if not self.download_package(package_name, progress_callback):
                logger.error(f"Failed to download required package: {package_name}")
                return False

        logger.info("All required packages downloaded successfully")
        return True

    def get_package_path(self, package_name: str) -> Optional[Path]:
        """
        Get path to installed package

        Returns:
            Path to package directory, or None if not installed
        """
        status = self.check_installation()
        if not status.get(package_name, False):
            return None

        package_path = self.data_dir / package_name
        return package_path if package_path.exists() else None

    def get_download_info(self) -> Dict:
        """
        Get information about what needs to be downloaded

        Returns:
            Dictionary with download size and package info
        """
        missing = self.get_missing_packages()

        total_size_mb = sum(self.DATA_SOURCES[name]["size_mb"] for name in missing)

        packages = [
            {
                "name": name,
                "description": self.DATA_SOURCES[name]["description"],
                "size_mb": self.DATA_SOURCES[name]["size_mb"],
            }
            for name in missing
        ]

        return {
            "missing_count": len(missing),
            "total_size_mb": total_size_mb,
            "packages": packages,
        }

    def uninstall_package(self, package_name: str) -> bool:
        """
        Uninstall a package

        Returns:
            True if successful
        """
        try:
            # Remove package directory
            package_path = self.data_dir / package_name
            if package_path.exists():
                shutil.rmtree(package_path)

            # Remove marker file
            marker_file = self.data_dir / f".{package_name}.installed"
            if marker_file.exists():
                marker_file.unlink()

            logger.info(f"Uninstalled {package_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to uninstall {package_name}: {e}")
            return False


# Alternative hosting options configuration
class DataSourceConfig:
    """
    Examples of different hosting configurations
    """

    # Option 1: GitHub Releases (Free for public repos)
    GITHUB_RELEASES = {
        "controls": {
            "url": "https://github.com/your-org/disconnectome-data/releases/download/v1.0/controls.tar.gz",
            "md5": "...",
            "size_mb": 500,
            "required": True,
            "description": "Control subject data",
        }
    }

    # Option 2: AWS S3 (Paid but scalable)
    AWS_S3 = {
        "controls": {
            "url": "https://disconnectome-data.s3.amazonaws.com/v1.0/controls.tar.gz",
            "md5": "...",
            "size_mb": 500,
            "required": True,
            "description": "Control subject data",
        }
    }

    # Option 3: Google Drive (Manual setup)
    GOOGLE_DRIVE = {
        "controls": {
            "url": "https://drive.google.com/uc?export=download&id=YOUR_FILE_ID",
            "md5": "...",
            "size_mb": 500,
            "required": True,
            "description": "Control subject data",
        }
    }

    # Option 4: Institutional Server (Best for research)
    INSTITUTIONAL = {
        "controls": {
            "url": "https://data.youruniversity.edu/disconnectome/controls.tar.gz",
            "md5": "...",
            "size_mb": 500,
            "required": True,
            "description": "Control subject data",
        }
    }

    # Option 5: Zenodo (Research data repository - Free and permanent)
    ZENODO = {
        "controls": {
            "url": "https://zenodo.org/record/YOUR_RECORD_ID/files/controls.tar.gz",
            "md5": "...",
            "size_mb": 500,
            "required": True,
            "description": "Control subject data",
        }
    }
