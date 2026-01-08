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
import tarfile
import zipfile
import shutil
import tempfile

logger = logging.getLogger("disconnectome")


class DataDownloadError(Exception):
    """Custom exception for data download errors"""

    pass


class DataDownloader:
    """
    Manages downloading and verifying large data files
    """

    # Configuration for data sources
    # IMPORTANT: Update these URLs to point to your actual data hosting
    DATA_SOURCES = {
        "controls": {
            "url": "https://your-server.edu/disconnectome/controls.tar.gz",
            "md5": "78d1353481151aeaec8d5d0c74b3ab89",
            "size_mb": 500,
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

    def validate_url(self, url: str, package_name: str) -> bool:
        """
        Validate that URL is accessible and returns expected content

        Args:
            url: URL to validate
            package_name: Package name for logging

        Returns:
            True if URL is valid

        Raises:
            DataDownloadError: If URL is invalid
        """
        try:
            # Send HEAD request to check if URL exists
            request = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(request, timeout=10) as response:
                # Check status code
                if response.status != 200:
                    raise DataDownloadError(
                        f"URL returned status {response.status}: {url}"
                    )

                # Check content type
                content_type = response.headers.get("Content-Type", "")

                # Valid archive content types
                valid_types = [
                    "application/gzip",
                    "application/x-gzip",
                    "application/x-tar",
                    "application/x-compressed-tar",
                    "application/zip",
                    "application/octet-stream",  # Generic binary
                ]

                if not any(t in content_type for t in valid_types):
                    logger.warning(
                        f"Unexpected content type for {package_name}: {content_type}"
                    )
                    logger.warning("Proceeding anyway, but download may fail")

                # Check content length
                content_length = response.headers.get("Content-Length")
                if content_length:
                    size_mb = int(content_length) / (1024 * 1024)
                    logger.info(f"{package_name} size: {size_mb:.1f} MB")

                return True

        except urllib.error.HTTPError as e:
            raise DataDownloadError(f"HTTP error {e.code} accessing {url}: {e.reason}")
        except urllib.error.URLError as e:
            raise DataDownloadError(f"Failed to reach server at {url}: {e.reason}")
        except Exception as e:
            raise DataDownloadError(f"Failed to validate URL {url}: {e}")

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
        url = config["url"]
        self.progress_callback = progress_callback

        try:
            # Validate URL before attempting download
            logger.info(f"Validating URL for {package_name}...")
            try:
                self.validate_url(url, package_name)
            except DataDownloadError as e:
                logger.error(f"URL validation failed: {e}")
                logger.error(f"Please check that the URL is correct: {url}")
                logger.error(
                    f"Current DATA_SOURCES configuration may have placeholder URLs"
                )
                return False

            # Download
            logger.info(f"Downloading {package_name} from {url}")
            archive_path = self._download_file(url, package_name, config["size_mb"])

            # Verify file was downloaded and is not empty
            if not archive_path.exists():
                raise DataDownloadError(f"Download file not found: {archive_path}")

            file_size = archive_path.stat().st_size
            if file_size < 1024:  # Less than 1KB is suspicious
                # Read first few bytes to check if it's HTML error page
                with open(archive_path, "rb") as f:
                    first_bytes = f.read(512)
                    if (
                        b"<html" in first_bytes.lower()
                        or b"<!doctype" in first_bytes.lower()
                    ):
                        raise DataDownloadError(
                            f"Downloaded file appears to be an HTML error page, not data. "
                            f"URL may be incorrect: {url}"
                        )

                raise DataDownloadError(
                    f"Downloaded file is suspiciously small ({file_size} bytes). "
                    f"Download may have failed."
                )

            logger.info(f"Downloaded {file_size / (1024 * 1024):.1f} MB")

            # Verify MD5 if provided
            if config.get("md5"):
                logger.info(f"Verifying {package_name}...")
                if not self._verify_md5(archive_path, config["md5"]):
                    logger.error(f"MD5 verification failed for {package_name}")
                    logger.error("This could mean:")
                    logger.error("1. The download was corrupted")
                    logger.error("2. The file was modified")
                    logger.error("3. The MD5 hash in DATA_SOURCES is incorrect")

                    # Ask user if they want to proceed anyway
                    logger.warning("Proceeding with extraction anyway...")
            else:
                logger.warning(
                    f"No MD5 hash provided for {package_name}, skipping verification"
                )

            # Detect archive format
            archive_format = self._detect_archive_format(archive_path)
            if not archive_format:
                raise DataDownloadError(
                    f"Unknown archive format: {archive_path}. "
                    f"Expected .tar.gz or .zip file."
                )

            logger.info(f"Detected archive format: {archive_format}")

            # Extract
            logger.info(f"Extracting {package_name}...")
            if not self._extract_archive(archive_path, package_name, archive_format):
                return False

            # Verify extraction
            extract_dir = self.data_dir / package_name
            if not extract_dir.exists() or not any(extract_dir.iterdir()):
                raise DataDownloadError(
                    f"Extraction appears to have failed - directory is empty: {extract_dir}"
                )

            # Create marker file
            marker_file = self.data_dir / f".{package_name}.installed"
            marker_file.write_text(
                json.dumps(
                    {
                        "version": "1.0",
                        "installed": True,
                        "url": url,
                        "size_bytes": file_size,
                    }
                )
            )

            # Clean up archive
            logger.info(f"Cleaning up archive file...")
            archive_path.unlink()

            logger.info(f"Successfully installed {package_name}")
            return True

        except DataDownloadError as e:
            logger.error(f"Data download error for {package_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to download {package_name}: {e}", exc_info=True)
            return False

    def _detect_archive_format(self, archive_path: Path) -> Optional[str]:
        """
        Detect archive format by examining file signature (magic bytes)

        Args:
            archive_path: Path to archive file

        Returns:
            'tar.gz', 'zip', or None if unknown
        """
        with open(archive_path, "rb") as f:
            header = f.read(10)

        # Check for gzip signature (used by .tar.gz)
        if header[:2] == b"\x1f\x8b":
            return "tar.gz"

        # Check for ZIP signature
        if header[:4] == b"PK\x03\x04" or header[:4] == b"PK\x05\x06":
            return "zip"

        # Check for uncompressed tar signature
        if b"ustar" in header:
            return "tar"

        # If we can't detect, try based on filename
        if archive_path.name.endswith(".tar.gz") or archive_path.name.endswith(".tgz"):
            logger.warning(
                "Could not detect .tar.gz signature, but filename suggests tar.gz"
            )
            return "tar.gz"
        elif archive_path.name.endswith(".zip"):
            logger.warning("Could not detect .zip signature, but filename suggests zip")
            return "zip"

        return None

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

        except urllib.error.HTTPError as e:
            raise DataDownloadError(
                f"HTTP error {e.code} downloading {url}: {e.reason}"
            )
        except urllib.error.URLError as e:
            raise DataDownloadError(f"Network error downloading {url}: {e.reason}")
        except Exception as e:
            raise DataDownloadError(f"Error downloading {url}: {e}")

    def _verify_md5(self, file_path: Path, expected_md5: str) -> bool:
        """Verify file MD5 hash"""
        md5_hash = hashlib.md5()

        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    md5_hash.update(chunk)

            actual_md5 = md5_hash.hexdigest()

            if actual_md5 != expected_md5:
                logger.error(f"MD5 mismatch:")
                logger.error(f"  Expected: {expected_md5}")
                logger.error(f"  Actual:   {actual_md5}")
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to compute MD5: {e}")
            return False

    def _extract_archive(
        self, archive_path: Path, package_name: str, archive_format: str
    ) -> bool:
        """Extract archive to data directory"""
        try:
            if archive_format == "zip":
                return self._extract_zip(archive_path, package_name)
            elif archive_format in ("tar.gz", "tar"):
                return self._extract_targz(archive_path, package_name)
            else:
                logger.error(f"Unsupported archive format: {archive_format}")
                return False

        except Exception as e:
            logger.error(f"Failed to extract {archive_path}: {e}", exc_info=True)
            return False

    def _extract_zip(self, archive_path: Path, package_name: str) -> bool:
        """Extract ZIP archive"""
        extract_dir = self.data_dir / package_name
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
            return True
        except zipfile.BadZipFile as e:
            raise DataDownloadError(f"Invalid ZIP file: {e}")

    def _extract_targz(self, archive_path: Path, package_name: str) -> bool:
        """Extract tar.gz archive"""
        extract_dir = self.data_dir / package_name
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            with tarfile.open(archive_path, "r:gz") as tar_ref:
                tar_ref.extractall(extract_dir)
            return True
        except tarfile.TarError as e:
            raise DataDownloadError(f"Invalid TAR file: {e}")

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
