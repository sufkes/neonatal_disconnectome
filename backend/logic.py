"""
Backend Logic with State Management Integration

This module provides processing functions that work with the state management system.
Functions can accept either individual parameters or state objects.
"""

import logging
from typing import Optional, Union
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
    processing: ProcessingState, config: AppConfig, state_manager=None
) -> bool:
    """
    Step 1: Warp subject brain image and lesion mask to age-matched template
    Using state objects instead of individual parameters.

    Args:
        processing: ProcessingState object containing all input data
        config: AppConfig object containing configuration

    Returns:
        True if successful, False otherwise

    Example:
        >>> from lib.state_management import StateManager
        >>> state_manager = StateManager()
        >>> processing = state_manager.get_processing()
        >>> config = state_manager.get_config()
        >>> success = step1_from_state(processing, config)
    """
    try:
        # Update state and notify observers
        if state_manager:
            state_manager.update_processing(
                current_step="step1_running",
                step1_progress=0.1,
                current_step_details="Starting warp",
            )

        logger.info(f"Starting step1 from state for subject={processing.subject_id}")

        # Validate state before processing
        is_valid, errors = processing.validate()
        if not is_valid:
            logger.error(f"Invalid processing state: {errors}")
            return False

        # Extract parameters from state
        runs_dir = config.runs_folder
        subject = processing.subject_id
        image_type = processing.brain_type
        moving_image = processing.brain_image_path
        lesion_image = processing.lesion_mask_path
        age = processing.gestational_age

        logger.debug(
            f"Step1 parameters: runs_dir={runs_dir}, subject={subject}, "
            f"image_type={image_type}, age={age}"
        )

        if state_manager:
            state_manager.update_processing(
                step1_progress=0.5,
                current_step_details="Creating control space directory",
            )
        createControlSpaceDirectory(subject, runs_dir)

        roundedAge = getRoundedAge(age)

        if state_manager:
            state_manager.update_processing(
                step1_progress=0.95,
                current_step_details="Warping subject to age-matched template",
            )
        warpSubjectToAgeMatchedTemplate(
            runs_dir, subject, image_type, moving_image, lesion_image, roundedAge
        )

        # Mark as complete
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


def step1(
    runs_dir: str,
    subject: str,
    image_type: str,
    moving_image: str,
    lesion_image: str,
    age: str,
) -> bool:
    """
    Step 1: Warp subject brain image and lesion mask to age-matched template
    Legacy function signature for backward compatibility.

    Args:
        runs_dir: Directory to store run outputs
        subject: Subject ID
        image_type: Type of brain image (T1w or T2w)
        moving_image: Path to brain image
        lesion_image: Path to lesion mask
        age: Gestational age in weeks

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.debug(f"Starting step1 with subject={subject}, age={age}")
        createControlSpaceDirectory(subject, runs_dir)
        roundedAge = getRoundedAge(age)
        warpSubjectToAgeMatchedTemplate(
            runs_dir, subject, image_type, moving_image, lesion_image, roundedAge
        )
        logger.info(f"Step1 completed successfully for subject={subject}")
        return True
    except Exception as e:
        logger.error(f"Step1 failed for subject={subject}: {e}", exc_info=True)
        return False


def step2_from_state(
    processing: ProcessingState,
    config: AppConfig,
    state_manager=None,
    threshold: float = 0,
) -> bool:
    """
    Step 2: Generate disconnectome from warped lesion
    Using state objects instead of individual parameters.

    Args:
        processing: ProcessingState object containing all input data
        config: AppConfig object containing configuration
        threshold: Threshold for disconnectome map (default 0)

    Returns:
        True if successful, False otherwise

    Example:
        >>> success = step2_from_state(processing, config, threshold=0)
    """
    try:
        # Update state and notify observers
        if state_manager:
            state_manager.update_processing(
                current_step="step2_running",
                step2_progress=0.1,
                current_step_details="Starting Disconectome Generation",
            )

        logger.info(f"Starting step2 from state for subject={processing.subject_id}")

        # Extract parameters from state
        runs_dir = config.runs_folder
        subject = processing.subject_id
        lesion_image = processing.lesion_mask_path
        age = processing.gestational_age
        image_type = processing.brain_type

        roundedAge = getRoundedAge(age)

        logger.debug(
            f"Step2 parameters: runs_dir={runs_dir}, subject={subject}, "
            f"age={roundedAge}, threshold={threshold}"
        )

        if state_manager:
            state_manager.update_processing(
                step2_progress=0.3,
                current_step_details="Applying subject lesion to control image warp",
            )
        applySubjectLesionToControlImageWarp(
            runs_dir, subject, lesion_image, roundedAge
        )

        if state_manager:
            state_manager.update_processing(
                step2_progress=0.5,
                current_step_details="Generating visitation map",
            )
        generateVisitationMap(runs_dir, subject)

        if state_manager:
            state_manager.update_processing(
                step2_progress=0.7,
                current_step_details="Warping visitation map",
            )

        warpVisitationMap(runs_dir, subject, image_type)

        if state_manager:
            state_manager.update_processing(
                step2_progress=0.95,
                current_step_details="Generating disconnectome",
            )

        generateDisconnectome(runs_dir, subject, image_type, threshold)

        # Mark as complete
        # Mark as complete
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


def step2(
    runs_dir: str,
    subject: str,
    lesion_image: str,
    age: str,
    threshold: float = 0,
    image_type: str = "T1w",
) -> bool:
    """
    Step 2: Generate disconnectome from warped lesion
    Legacy function signature for backward compatibility.

    Args:
        runs_dir: Directory containing run outputs
        subject: Subject ID
        lesion_image: Path to original lesion mask
        age: Gestational age in weeks
        threshold: Threshold for disconnectome map (default 0)
        image_type: Type of brain image (T1w or T2w)

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.debug(f"Starting step2 with subject={subject}, age={age}")
        roundedAge = getRoundedAge(age)
        applySubjectLesionToControlImageWarp(
            runs_dir, subject, lesion_image, roundedAge
        )
        generateVisitationMap(runs_dir, subject)
        warpVisitationMap(runs_dir, subject, image_type)
        generateDisconnectome(runs_dir, subject, image_type, threshold)
        return True
    except Exception as e:
        logger.exception("generate disconnectome failed", e)
        return False


def process_warped_lesion_from_state(
    processing: ProcessingState,
    config: AppConfig,
    state_manager=None,
) -> bool:
    """
    Process a lesion mask that is already warped to a dHCP template
    Using state objects instead of individual parameters.

    Args:
        processing: ProcessingState object containing all input data
        config: AppConfig object containing configuration

    Returns:
        True if successful, False otherwise

    Example:
        >>> from lib.state_management import StateManager
        >>> state_manager = StateManager()
        >>> processing = state_manager.get_processing()
        >>> config = state_manager.get_config()
        >>> success = process_warped_lesion_from_state(processing, config)
    """
    try:
        # Update state and notify observers
        if state_manager:
            state_manager.update_processing(
                current_step="step2_running",
                step2_progress=0.1,
                current_step_details="Starting warped lesion processing",
            )

        logger.info(
            f"Starting warped lesion processing from state for subject={processing.subject_id}"
        )

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

        # Extract parameters from state
        runs_dir = config.runs_folder
        subject = processing.subject_id
        lesion_image = processing.lesion_mask_path
        age = processing.template_age

        roundedAge = getRoundedAge(age)

        logger.debug(
            f"Warped lesion parameters: runs_dir={runs_dir}, subject={subject}, "
            f"age={roundedAge},"
        )

        # Create necessary directory structure
        if state_manager:
            state_manager.update_processing(
                step2_progress=0.3,
                current_step_details="Creating control space directory",
            )
        createControlSpaceDirectory(subject, runs_dir)
        if state_manager:
            state_manager.update_processing(
                step2_progress=0.4,
                current_step_details="Creating template space directory",
            )
        createTemplateSpaceDirectory(roundedAge, runs_dir, subject)

        # Apply pre-warped lesion to control images (skip=True)
        logger.info("Applying pre-warped lesion to control images...")
        if state_manager:
            state_manager.update_processing(
                step2_progress=0.5,
                current_step_details="Applying subject lesion to control image warp",
            )
        applySubjectLesionToControlImageWarp(
            runs_dir, subject, lesion_image, roundedAge, skip=True
        )

        # Generate visitation maps
        logger.info("Generating visitation maps...")
        if state_manager:
            state_manager.update_processing(
                step2_progress=0.6,
                current_step_details="Generating visitation map",
            )

        generateVisitationMap(runs_dir, subject)

        # Warp visitation maps to 40w template
        # Use T2w as default for warped lesions (can be made configurable)
        image_type = processing.brain_type if processing.brain_type else "T2w"
        logger.info(
            f"Warping visitation maps to 40w template (image_type={image_type})..."
        )
        if state_manager:
            state_manager.update_processing(
                step2_progress=0.75,
                current_step_details="Warping visitation map",
            )

        warpVisitationMap(runs_dir, subject, image_type)

        # Generate disconnectome map
        threshold = 0
        logger.info(f"Generating disconnectome map (threshold={threshold})...")
        if state_manager:
            state_manager.update_processing(
                step2_progress=0.95,
                current_step_details="Generating disconnectome",
            )
        generateDisconnectome(runs_dir, subject, image_type, threshold)

        logger.info(
            f"Warped lesion processing completed successfully for subject={subject}"
        )

        if state_manager:
            state_manager.update_processing(
                current_step="step2_complete", step2_progress=1.0, step2_completed=True
            )
        return True

    except FileNotFoundError as e:
        logger.error(
            f"File not found during warped lesion processing: {e}", exc_info=True
        )
        return False
    except ValueError as e:
        logger.error(
            f"Invalid value during warped lesion processing: {e}", exc_info=True
        )
        return False
    except Exception as e:
        logger.error(f"Warped lesion processing failed: {e}", exc_info=True)
        if state_manager:
            state_manager.update_processing(current_step="step2_failed")
        return False


def process_warped_lesion(
    runs_dir: str,
    subject: str,
    lesion_image: str,
    age: str,
) -> bool:
    """
    Process a lesion mask that is already warped to a dHCP template
    Legacy function signature for backward compatibility.

    Args:
        runs_dir: Directory to store run outputs
        subject: Subject ID
        lesion_image: Path to pre-warped lesion mask
        age: Templates's gestational age in weeks

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(
            f"Starting warped lesion processing for subject={subject}, age={age},"
        )

        roundedAge = getRoundedAge(age)

        createControlSpaceDirectory(subject, runs_dir)
        createTemplateSpaceDirectory(roundedAge, runs_dir, subject)

        applySubjectLesionToControlImageWarp(
            runs_dir, subject, lesion_image, roundedAge, skip=True
        )

        generateVisitationMap(runs_dir, subject)

        image_type = "T2w"
        warpVisitationMap(runs_dir, subject, image_type)

        threshold = 0
        generateDisconnectome(runs_dir, subject, image_type, threshold)

        logger.info(
            f"Warped lesion processing completed successfully for subject={subject}"
        )
        return True

    except Exception as e:
        logger.error(
            f"Warped lesion processing failed for subject={subject}: {e}", exc_info=True
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


def process_full_pipeline(
    runs_dir: str,
    subject: str,
    image_type: str,
    moving_image: str,
    lesion_image: str,
    age: str,
    threshold: float = 0,
) -> bool:
    """
    Run the complete processing pipeline (both step1 and step2)
    Legacy function signature for backward compatibility.

    Args:
        runs_dir: Directory to store run outputs
        subject: Subject ID
        image_type: Type of brain image (T1w or T2w)
        moving_image: Path to brain image
        lesion_image: Path to lesion mask
        age: Gestational age in weeks
        threshold: Threshold for disconnectome map (default 0)

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Starting full pipeline for subject={subject}")

        success = step1(runs_dir, subject, image_type, moving_image, lesion_image, age)
        if not success:
            logger.error("Step 1 failed, aborting pipeline")
            return False

        logger.info("Step 1 completed, proceeding to step 2")

        success = step2(runs_dir, subject, lesion_image, age, threshold, image_type)
        if not success:
            logger.error("Step 2 failed")
            return False

        logger.info(f"Full pipeline completed successfully for subject={subject}")
        return True

    except Exception as e:
        logger.error(f"Full pipeline failed for subject={subject}: {e}", exc_info=True)
        return False


# Utility function to automatically choose the right function based on input type
def run_step1(
    runs_dir_or_processing: Union[str, ProcessingState],
    subject_or_config: Union[str, AppConfig] = None,
    image_type: Optional[str] = None,
    moving_image: Optional[str] = None,
    lesion_image: Optional[str] = None,
    age: Optional[str] = None,
) -> bool:
    """
    Flexible step1 function that accepts either state objects or individual parameters.

    Usage:
        # With state objects:
        >>> run_step1(processing, config)

        # With individual parameters:
        >>> run_step1(runs_dir, subject, image_type, moving_image, lesion_image, age)

    Args:
        runs_dir_or_processing: Either runs_dir (str) or ProcessingState object
        subject_or_config: Either subject (str) or AppConfig object
        image_type: Type of brain image (only needed for individual params)
        moving_image: Path to brain image (only needed for individual params)
        lesion_image: Path to lesion mask (only needed for individual params)
        age: Gestational age (only needed for individual params)

    Returns:
        True if successful, False otherwise
    """
    # Check if first argument is a ProcessingState object
    if isinstance(runs_dir_or_processing, ProcessingState):
        processing = runs_dir_or_processing
        config = subject_or_config
        if not isinstance(config, AppConfig):
            raise TypeError(
                "When using ProcessingState, second argument must be AppConfig"
            )
        return step1_from_state(processing, config)

    # Otherwise, use individual parameters
    else:
        runs_dir = runs_dir_or_processing
        subject = subject_or_config

        if None in [image_type, moving_image, lesion_image, age]:
            raise ValueError(
                "When using individual parameters, all parameters must be provided: "
                "runs_dir, subject, image_type, moving_image, lesion_image, age"
            )

        return step1(runs_dir, subject, image_type, moving_image, lesion_image, age)


def run_step2(
    runs_dir_or_processing: Union[str, ProcessingState],
    subject_or_config: Union[str, AppConfig] = None,
    lesion_image: Optional[str] = None,
    age: Optional[str] = None,
    threshold: float = 0,
    image_type: Optional[str] = "T1w",
) -> bool:
    """
    Flexible step2 function that accepts either state objects or individual parameters.

    Usage:
        # With state objects:
        >>> run_step2(processing, config)

        # With individual parameters:
        >>> run_step2(runs_dir, subject, lesion_image, age, threshold, image_type)
    """
    if isinstance(runs_dir_or_processing, ProcessingState):
        processing = runs_dir_or_processing
        config = subject_or_config
        if not isinstance(config, AppConfig):
            raise TypeError(
                "When using ProcessingState, second argument must be AppConfig"
            )
        return step2_from_state(processing, config, threshold)
    else:
        runs_dir = runs_dir_or_processing
        subject = subject_or_config

        if None in [lesion_image, age]:
            raise ValueError(
                "When using individual parameters, runs_dir, subject, lesion_image, "
                "and age must be provided"
            )

        return step2(runs_dir, subject, lesion_image, age, threshold, image_type)
