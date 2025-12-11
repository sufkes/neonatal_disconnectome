"""
State Management Module for Disconnectome Application

This module provides robust state management using dataclasses and Pydantic
for validation. It replaces the simple dictionary-based approach with
type-safe, validated state containers.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any
from pathlib import Path
from enum import Enum
import json
import logging
import os

from lib.constants import TEMPLATE_TEMPLATES_DIR

logger = logging.getLogger("disconnectome")


class BrainImageType(Enum):
    """Enumeration for brain image types"""

    T1W = "T1w"
    T2W = "T2w"


class AppearanceMode(Enum):
    """Enumeration for appearance modes"""

    LIGHT = "Light"
    DARK = "Dark"
    SYSTEM = "System"


@dataclass
class AppConfig:
    """Application configuration settings that persist across sessions"""

    runs_folder: str = ""
    theme: str = "blue"
    appearance: str = AppearanceMode.LIGHT.value

    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.appearance not in [mode.value for mode in AppearanceMode]:
            logger.warning(
                f"Invalid appearance mode: {self.appearance}, defaulting to Light"
            )
            self.appearance = AppearanceMode.LIGHT.value

    @classmethod
    def load(cls, path: str = "user_settings.json") -> "AppConfig":
        """
        Load configuration from JSON file

        Args:
            path: Path to settings file

        Returns:
            AppConfig instance with loaded settings or defaults
        """
        if Path(path).exists():
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    logger.info(f"Loaded configuration from {path}")
                    return cls(**data)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse settings file: {e}")
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")

        logger.info("Using default configuration")
        return cls()

    def save(self, path: str = "user_settings.json") -> bool:
        """
        Save configuration to JSON file

        Args:
            path: Path to settings file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(path, "w") as f:
                json.dump(asdict(self), f, indent=4)
            logger.info(f"Saved configuration to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    def update(self, **kwargs) -> None:
        """
        Update configuration values

        Args:
            **kwargs: Configuration fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"Updated config: {key} = {value}")
            else:
                logger.warning(f"Attempted to update unknown config field: {key}")


@dataclass
class ProcessingState:
    """State for the current processing workflow"""

    # Input data
    brain_image_path: str = ""
    lesion_mask_path: str = ""
    brain_type: str = ""
    subject_id: str = ""
    gestational_age: str = ""
    template_age: str = ""

    # Workflow state
    lesion_already_warped: bool = False
    step1_completed: bool = False
    step2_completed: bool = False

    # Output paths (populated after processing)
    warped_brain_image_path: str = ""
    warped_lesion_mask_path: str = ""
    age_matched_template_path: str = ""
    disconnectome_map_path: str = ""
    lesion_40w_space_path: str = ""
    template_40w_path: str = ""

    # Thumbnail paths
    thumbnail_aligned_pair: str = ""
    thumbnail_lesion_original: str = ""
    thumbnail_lesion_template: str = ""
    thumbnail_disconnectome: str = ""

    # Progress tracking
    current_step: str = ""  # "idle", "step1_running", "step1_complete", etc.
    current_step_details: str = ""  # "create control space directory", "warp subject to age-matched template", etc.
    step1_progress: float = 0.0  # 0.0 to 1.0
    step2_progress: float = 0.0

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the current processing state

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Validate required fields for step 1
        if not self.brain_image_path and not self.lesion_already_warped:
            errors.append("Brain image path is required")

        if not self.lesion_mask_path:
            errors.append("Lesion mask path is required")

        if not self.brain_type and not self.lesion_already_warped:
            if self.brain_type not in [t.value for t in BrainImageType]:
                errors.append("Invalid brain image type")

        if not self.subject_id:
            errors.append("Subject ID is required")
        elif not self._is_valid_subject_id(self.subject_id):
            errors.append(
                "Subject ID contains invalid characters (only letters, numbers, underscore, and dash allowed)"
            )

        if self.lesion_already_warped:
            if not self.template_age:
                errors.append("Template age is required")
            else:
                try:
                    age = float(self.template_age)
                    if age < 28 or age > 44:
                        errors.append(
                            "Warning: Age is outside of 28-44 weeks. Registration to template may be poor."
                        )
                except ValueError:
                    errors.append("Template age must be a valid number")
        else:
            if not self.gestational_age:
                errors.append("Gestational age is required")
            else:
                try:
                    age = float(self.gestational_age)
                    if age < 28 or age > 44:
                        errors.append(
                            "Warning: Age is outside of 28-44 weeks. Registration to template may be poor."
                        )
                except ValueError:
                    errors.append("Gestational age must be a valid number")

        # Validate file paths exist
        if self.brain_image_path and not Path(self.brain_image_path).exists():
            errors.append(f"Brain image file not found: {self.brain_image_path}")

        # Validate file extensions
        if self.brain_image_path:
            if not (
                self.brain_image_path.endswith(".nii")
                or self.brain_image_path.endswith(".nii.gz")
            ):
                errors.append("Brain image must be a NIFTI file (.nii or .nii.gz)")

        if self.lesion_mask_path and not Path(self.lesion_mask_path).exists():
            errors.append(f"Lesion mask file not found: {self.lesion_mask_path}")

        if self.lesion_mask_path:
            if not (
                self.lesion_mask_path.endswith(".nii")
                or self.lesion_mask_path.endswith(".nii.gz")
            ):
                errors.append("Lesion mask must be a NIFTI file (.nii or .nii.gz)")

        return len(errors) == 0, errors

    @staticmethod
    def _is_valid_subject_id(subject_id: str) -> bool:
        """Check if subject ID contains only allowed characters"""
        import re

        return bool(re.match(r"^[\w-]+$", subject_id))

    def get_input_summary(self) -> Dict[str, str]:
        """
        Get a summary of input data for display

        Returns:
            Dictionary of input parameters (filters out None/empty values)
        """
        summary = {
            "Subject ID": self.subject_id,
            "Gestational Age (weeks)": self.gestational_age
            if not self.lesion_already_warped
            else None,
            "Brain Image Type": self.brain_type,
            "Brain Image Path": self.brain_image_path
            if not self.lesion_already_warped
            else None,
            "Lesion Mask Path": self.lesion_mask_path,
            "Lesion Already Warped": "Yes" if self.lesion_already_warped else "No",
            "Template Age (weeks)": self.template_age
            if self.lesion_already_warped
            else None,
        }

        # Filter out None values and empty strings
        return {k: v for k, v in summary.items() if v is not None and v != ""}

    def get_output_summary(self, runs_folder: str = "") -> Dict[str, str]:
        """
        Get a summary of output data for display

        Args:
            runs_folder: Path to runs folder to build complete paths

        Returns:
            Dictionary of output paths
        """
        outputs = {}

        if not runs_folder or not self.subject_id:
            return outputs

        # Import here to avoid circular imports
        from lib.constants import TEMPLATE_SPACE, DISCONNECTOME

        # Build actual output paths based on what's been completed
        if self.step1_completed and not self.lesion_already_warped:
            age = self.gestational_age
            if age:
                from lib.utils import getRoundedAge

                rounded_age = getRoundedAge(age)
                template_dir = os.path.join(
                    runs_folder, self.subject_id, TEMPLATE_SPACE, f"{rounded_age}W"
                )

                warped_brain = os.path.join(
                    template_dir,
                    f"brain_img_{rounded_age}-week-template-space-warped.nii.gz",
                )
                if os.path.exists(warped_brain):
                    outputs["Input brain image warped to age-matched template"] = (
                        warped_brain
                    )

                warped_lesion = os.path.join(
                    template_dir,
                    f"lesion_mask_{rounded_age}-week-template-space-warped.nii.gz",
                )
                if os.path.exists(warped_lesion):
                    outputs["Input lesion image warped to age-matched template"] = (
                        warped_lesion
                    )

        if self.step2_completed:
            if self.lesion_already_warped:
                age = self.template_age
            else:
                age = self.gestational_age

            if age:
                from lib.utils import getRoundedAge

                rounded_age = getRoundedAge(age)
                age_matched_template = os.path.join(
                    TEMPLATE_TEMPLATES_DIR,
                    f"week{rounded_age}_{self.brain_type}.nii.gz",
                )
                if os.path.exists(age_matched_template):
                    outputs["Age-matched template image(fixed image for warp step)"] = (
                        age_matched_template
                    )

            disconnectome_dir = os.path.join(
                runs_folder, self.subject_id, DISCONNECTOME
            )

            disconnectome_map = os.path.join(
                disconnectome_dir, "disconnectome-threshold_0.nii.gz"
            )
            if os.path.exists(disconnectome_map):
                outputs["Disconnectome map in 40w template space"] = disconnectome_map

            lesion_40w = os.path.join(
                disconnectome_dir, "lesion_mask_40-week-template-space-warped.nii.gz"
            )
            if os.path.exists(lesion_40w):
                outputs["Lesion image in 40w template space"] = lesion_40w

            week40_template = os.path.join(
                TEMPLATE_TEMPLATES_DIR, f"week40_{self.brain_type}.nii.gz"
            )
            if os.path.exists(week40_template):
                outputs["40w template image"] = week40_template

        return outputs

    def reset(self) -> None:
        """Reset processing state to initial values"""
        self.__init__()
        logger.info("Processing state reset")

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessingState":
        """Create ProcessingState from dictionary"""
        return cls(**data)


class StateManager:
    """
    Central state manager for the application

    This class manages both configuration and processing state,
    providing a single interface for state operations.
    """

    def __init__(self, config_path: str = "user_settings.json"):
        """
        Initialize state manager

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = AppConfig.load(config_path)
        self.processing = ProcessingState()
        self._observers: list[callable] = []

        logger.info("State manager initialized")

    def update_config(self, **kwargs) -> bool:
        """
        Update configuration and save to disk

        Args:
            **kwargs: Configuration fields to update

        Returns:
            True if saved successfully
        """
        self.config.update(**kwargs)
        success = self.config.save(self.config_path)
        if success:
            self._notify_observers("config")
        return success

    def update_processing(self, **kwargs) -> None:
        """
        Update processing state

        Args:
            **kwargs: Processing state fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self.processing, key):
                setattr(self.processing, key, value)
                logger.debug(f"Updated processing state: {key}")
            else:
                logger.warning(f"Attempted to update unknown processing field: {key}")

        self._notify_observers("processing")

    def validate_processing_state(self) -> tuple[bool, list[str]]:
        """
        Validate current processing state

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        return self.processing.validate()

    def reset_processing(self) -> None:
        """Reset processing state to initial values"""
        self.processing.reset()
        self._notify_observers("processing")

    def get_config(self) -> AppConfig:
        """Get current configuration"""
        return self.config

    def get_processing(self) -> ProcessingState:
        """Get current processing state"""
        return self.processing

    def subscribe(self, observer: callable) -> None:
        """
        Subscribe to state changes

        Args:
            observer: Callable that takes (state_type: str) as argument
        """
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(f"Observer subscribed: {observer.__name__}")

    def unsubscribe(self, observer: callable) -> None:
        """
        Unsubscribe from state changes

        Args:
            observer: Previously subscribed observer
        """
        if observer in self._observers:
            self._observers.remove(observer)
            logger.debug(f"Observer unsubscribed: {observer.__name__}")

    def _notify_observers(self, state_type: str) -> None:
        """
        Notify all observers of state change

        Args:
            state_type: Type of state that changed ("config" or "processing")
        """
        for observer in self._observers:
            try:
                observer(state_type)
            except Exception as e:
                logger.error(f"Error notifying observer {observer.__name__}: {e}")

    def save_session(self, path: str) -> bool:
        """
        Save current processing session to file

        Args:
            path: Path to save session data

        Returns:
            True if successful
        """
        try:
            from datetime import datetime

            session_data = {
                "processing": self.processing.to_dict(),
                "timestamp": datetime.now().isoformat(),
            }

            with open(path, "w") as f:
                json.dump(session_data, f, indent=4)

            logger.info(f"Session saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False

    def load_session(self, path: str) -> bool:
        """
        Load processing session from file

        Args:
            path: Path to session file

        Returns:
            True if successful
        """
        try:
            if not Path(path).exists():
                logger.warning(f"Session file not found: {path}")
                return False

            with open(path, "r") as f:
                session_data = json.load(f)

            self.processing = ProcessingState.from_dict(session_data["processing"])
            self._notify_observers("processing")

            logger.info(f"Session loaded from {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False
