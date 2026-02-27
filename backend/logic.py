"""
Backend Logic with State Management Integration

This module provides processing functions that work with the state management system.
Functions can accept either individual parameters or state objects.
"""

import logging
import threading
from typing import Callable, Optional
from lib.utils import (
    createControlSpaceDirectory,
    createTemplateSpaceDirectory,
    getRoundedAge,
)
from lib.state_management import ProcessingState, AppConfig
from .step1WarpSubjectToAgeMatchedTemplate import warpSubjectToAgeMatchedTemplate
from .step2ApplySubjectLesionToControlImageWarp import (
    applySubjectLesionToControlImageWarp,
)
from .step3GenerateVisitationMap import generateVisitationMap
from .step4WarpVisitationMapTo40wTemplate import warpVisitationMap
from .step5MakeDisconnectomeMap import generateDisconnectome

# Get the same logger used by the app's GUI logging setup
logger = logging.getLogger(__name__)


def step1_from_state(
    processing: ProcessingState,
    config: AppConfig,
    state_manager=None,
    cancel_event: Optional[threading.Event] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> bool:
    """
    Step 1: Warp subject brain image and lesion mask to age-matched template

    Args:
        processing: ProcessingState object
        config: AppConfig object
        state_manager: Optional state manager for updates
        cancel_event: Optional event to signal cancellation
        progress_callback: Optional progress callback

    Returns:
        True if successful, False otherwise
    """

    def check_cancelled():
        """Check if cancellation was requested"""
        return cancel_event and cancel_event.is_set()

    def update_progress(progress: float, message: str):
        """Update progress if callback provided"""
        if progress_callback:
            progress_callback(progress, message)

        if state_manager and progress in (0.0, 0.5, 1.0):
            state_manager.update_processing(
                current_step="step1_running",
                step1_progress=progress,
                current_step_details=message,
            )

    try:
        # Update state
        if state_manager:
            state_manager.update_processing(
                current_step="step1_running",
                step1_progress=0.0,
                current_step_details="Starting",
            )

        logger.info(f"Starting step1 from state for subject={processing.subject_id}")

        # Check cancellation
        if check_cancelled():
            logger.info("Step1 cancelled before start")
            return False

        # Validate state
        update_progress(0.1, "Validating input")
        is_valid, errors = processing.validate()
        if not is_valid:
            logger.error(f"Invalid processing state: {errors}")
            return False

        if check_cancelled():
            return False

        # Extract parameters
        runs_dir = config.runs_folder
        subject = processing.subject_id
        image_type = processing.brain_type
        moving_image = processing.brain_image_path
        lesion_image = processing.lesion_mask_path
        age = processing.gestational_age

        # Create control space directory
        update_progress(0.2, "Creating directory structure")
        if check_cancelled():
            return False

        createControlSpaceDirectory(subject, runs_dir)

        # Get rounded age
        update_progress(0.3, "Preparing template")
        if check_cancelled():
            return False

        roundedAge = getRoundedAge(age)

        # Run warp
        update_progress(0.4, "Warping to age-matched template (this may take a while)")
        if check_cancelled():
            return False

        # Pass cancellation support to warp function
        warpSubjectToAgeMatchedTemplate(
            runs_dir,
            subject,
            image_type,
            moving_image,
            lesion_image,
            roundedAge,
            cancel_event=cancel_event,
            progress_callback=lambda p, m: update_progress(
                0.4 + (p * 0.5), m
            ),  # Map 0-100% to 40-90%
        )

        if check_cancelled():
            return False

        # Mark as complete
        update_progress(1.0, "Complete")
        if state_manager:
            state_manager.update_processing(
                current_step="step1_complete", step1_progress=1.0, step1_completed=True
            )

        logger.info(f"Step1 completed successfully for subject={subject}")
        return True

    except Exception as e:
        if state_manager:
            state_manager.update_processing(current_step="step1_failed")
        logger.error(
            f"Step1 failed for subject={processing.subject_id}: {e}", exc_info=True
        )
        return False


def step2_from_state(
    processing: ProcessingState,
    config: AppConfig,
    state_manager=None,
    threshold: float = 0,
    cancel_event: Optional[threading.Event] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> bool:
    """
    Step 2: Generate disconnectome from warped lesion
    Using state objects instead of individual parameters.

    Args:
        processing: ProcessingState object containing all input data
        config: AppConfig object containing configuration
        threshold: Threshold for disconnectome map (default 0)
        cancel_event: Optional event to signal cancellation
        progress_callback: Optional progress callback

    Returns:
        True if successful, False otherwise

    Example:
        >>> success = step2_from_state(processing, config, threshold=0)
    """

    def check_cancelled():
        """Check if cancellation was requested"""
        return cancel_event and cancel_event.is_set()

    def update_progress(progress: float, message: str):
        """Update progress if callback provided"""
        if progress_callback:
            progress_callback(progress, message)

        if state_manager and progress in (0.0, 0.5, 1.0):
            state_manager.update_processing(
                current_step="step2_running",
                step1_progress=progress,
                current_step_details=message,
            )

    try:
        # Update state and notify observers
        if state_manager:
            state_manager.update_processing(
                current_step="step2_running",
                step2_progress=0.0,
                current_step_details="Starting Disconectome Generation",
            )

        logger.info(f"Starting step2 from state for subject={processing.subject_id}")

        # Check cancellation
        if check_cancelled():
            logger.info("Step1 cancelled before start")
            return False

        # Validate state
        update_progress(0.1, "Validating input")
        is_valid, errors = processing.validate()
        if not is_valid:
            logger.error(f"Invalid processing state: {errors}")
            return False

        if check_cancelled():
            return False

        # Extract parameters from state
        runs_dir = config.runs_folder
        subject = processing.subject_id
        lesion_image = processing.lesion_mask_path
        age = processing.gestational_age or processing.template_age
        image_type = processing.brain_type

        # Get rounded age
        update_progress(0.2, "Preparing template")
        if check_cancelled():
            return False

        roundedAge = getRoundedAge(age)

        update_progress(0.3, "Applying subject lesion to control image warp")
        if check_cancelled():
            return False

        applySubjectLesionToControlImageWarp(
            runs_dir,
            subject,
            lesion_image,
            roundedAge,
            cancel_event=cancel_event,
            progress_callback=lambda p, m: update_progress(0.15 + (p * 0.25), m),
        )

        # Generate Visitation Map
        update_progress(0.4, "Generating visitation map (this may take a while)")
        if check_cancelled():
            return False

        generateVisitationMap(
            runs_dir,
            subject,
            cancel_event=cancel_event,
            progress_callback=lambda p, m: update_progress(0.40 + (p * 0.40), m),
        )

        # Warp Visitation Map
        update_progress(0.5, "Warping visitation map (this may take a while)")
        if check_cancelled():
            return False

        warpVisitationMap(
            runs_dir,
            subject,
            image_type,
            cancel_event=cancel_event,
            progress_callback=lambda p, m: update_progress(0.80 + (p * 0.15), m),
        )

        # Generating disconnectome
        update_progress(0.5, "Generating disconnectome (this may take a while)")
        if check_cancelled():
            return False

        generateDisconnectome(
            runs_dir, subject, image_type, threshold, cancel_event=cancel_event
        )

        if check_cancelled():
            return False

        # Mark as complete
        update_progress(1.0, "Complete")
        if state_manager:
            state_manager.update_processing(
                current_step="step2_complete", step2_progress=1.0, step2_completed=True
            )

        logger.info(f"Step2 completed successfully for subject={subject}")
        return True

    except Exception as e:
        if state_manager:
            state_manager.update_processing(current_step="step2_failed")
        logger.exception(f"Step2 failed for subject={processing.subject_id}: {e}")
        return False


def process_warped_lesion_from_state(
    processing: ProcessingState,
    config: AppConfig,
    state_manager=None,
    cancel_event: Optional[threading.Event] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> bool:
    """
    Process a lesion mask that is already warped to a dHCP template
    Using state objects instead of individual parameters.

    Args:
        processing: ProcessingState object containing all input data
        config: AppConfig object containing configuration
        state_manager: Optional state manager for updates
        cancel_event: Optional event to signal cancellation
        progress_callback: Optional progress callback

    Returns:
        True if successful, False otherwise

    Example:
        >>> from lib.state_management import StateManager
        >>> state_manager = StateManager()
        >>> processing = state_manager.get_processing()
        >>> config = state_manager.get_config()
        >>> success = process_warped_lesion_from_state(processing, config)
    """

    def check_cancelled():
        """Check if cancellation was requested"""
        return cancel_event and cancel_event.is_set()

    def update_progress(progress: float, message: str):
        """Update progress if callback provided"""
        if progress_callback:
            progress_callback(progress, message)

        if state_manager and progress in (0.0, 0.5, 1.0):
            state_manager.update_processing(
                current_step="step2_running",
                step1_progress=progress,
                current_step_details=message,
            )

    try:
        # Update state and notify observers
        if state_manager:
            state_manager.update_processing(
                current_step="step2_running",
                step2_progress=0.0,
                current_step_details="Starting warped lesion processing",
            )

        logger.info(
            f"Starting warped lesion processing from state for subject={processing.subject_id}"
        )

        # Check cancellation
        if check_cancelled():
            logger.info("Step2 cancelled before start")
            return False

        # Validate required fields for warped lesion processing
        if not processing.lesion_mask_path:
            logger.error("Lesion mask path is required")
            return False

        if not processing.subject_id:
            logger.error("Subject ID is required")
            return False

        if not processing.template_age:
            logger.error("Template age is required")
            return False

        # Validate state
        update_progress(0.1, "Validating input")
        is_valid, errors = processing.validate()
        if not is_valid:
            logger.error(f"Invalid processing state: {errors}")
            return False

        if check_cancelled():
            return False

        # Extract parameters from state
        runs_dir = config.runs_folder
        subject = processing.subject_id
        lesion_image = processing.lesion_mask_path
        age = processing.template_age

        # Get rounded age
        update_progress(0.2, "Preparing template")
        if check_cancelled():
            return False

        roundedAge = getRoundedAge(age)

        # Create control space directory
        update_progress(0.3, "Creating control space directory")
        if check_cancelled():
            return False

        createControlSpaceDirectory(subject, runs_dir)

        # Run warp
        update_progress(0.4, "Creating template space directory")
        if check_cancelled():
            return False

        createTemplateSpaceDirectory(roundedAge, runs_dir, subject)

        # Apply pre-warped lesion to control images (skip=True)
        update_progress(0.5, "Applying subject lesion to control image warp")
        if check_cancelled():
            return False

        applySubjectLesionToControlImageWarp(
            runs_dir,
            subject,
            lesion_image,
            roundedAge,
            skip=True,
            cancel_event=cancel_event,
            progress_callback=lambda p, m: update_progress(0.5 + (p * 0.5), m),
        )

        # Generate visitation maps
        update_progress(0.6, "Generating visitation map")
        if check_cancelled():
            return False

        generateVisitationMap(
            runs_dir,
            subject,
            cancel_event=cancel_event,
            progress_callback=lambda p, m: update_progress(0.6 + (p * 0.6), m),
        )

        # Warp visitation maps to 40w template
        # Use T2w as default for warped lesions (can be made configurable)
        update_progress(0.7, "Warping visitation map")
        if check_cancelled():
            return False
        image_type = processing.brain_type if processing.brain_type else "T2w"

        warpVisitationMap(
            runs_dir,
            subject,
            image_type,
            cancel_event=cancel_event,
            progress_callback=lambda p, m: update_progress(0.7 + (p * 0.7), m),
        )

        # Generate disconnectome map
        update_progress(0.8, "Generating disconnectome")
        if check_cancelled():
            return False

        threshold = 0

        generateDisconnectome(runs_dir, subject, image_type, threshold, cancel_event)

        if check_cancelled():
            return False

        update_progress(1.0, "Complete")
        if state_manager:
            state_manager.update_processing(
                current_step="step2_complete", step2_progress=1.0, step2_completed=True
            )

        logger.info(
            f"Warped lesion processing completed successfully for subject={subject}"
        )
        return True

    except Exception as e:
        if state_manager:
            state_manager.update_processing(current_step="step2_failed")
        logger.error(
            f"Step1 failed for subject={processing.subject_id}: {e}", exc_info=True
        )
        return False


def process_full_pipeline_from_state(
    processing: ProcessingState, config: AppConfig, threshold: float = 0
) -> bool:
    """
    Run the complete processing pipeline (both step1 and step2)
    Using state objects instead of individual parameters.

    Args:
        processing: ProcessingState object containing all input data
        config: AppConfig object containing configuration
        threshold: Threshold for disconnectome map (default 0)

    Returns:
        True if successful, False otherwise

    Example:
        >>> success = process_full_pipeline_from_state(processing, config)
    """
    try:
        logger.info(
            f"Starting full pipeline from state for subject={processing.subject_id}"
        )

        # Step 1: Warp to age-matched template
        success = step1_from_state(processing, config)
        if not success:
            logger.error("Step 1 failed, aborting pipeline")
            return False

        logger.info("Step 1 completed, proceeding to step 2")

        # Step 2: Generate disconnectome
        success = step2_from_state(processing, config, threshold)
        if not success:
            logger.error("Step 2 failed")
            return False

        logger.info(
            f"Full pipeline completed successfully for subject={processing.subject_id}"
        )
        return True

    except Exception as e:
        logger.error(f"Full pipeline failed: {e}", exc_info=True)
        return False
