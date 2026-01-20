"""
Security Module: Password hashing, model verification, and secure operations

Implements:
- Secure password hashing with SHA256
- Model checksum verification
- Fail-safe model loading
- Secure credential handling
"""

import hashlib
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == hashed


def compute_file_sha256(filepath: str, chunk_size: int = 65536) -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        filepath: Path to file
        chunk_size: Read chunk size (for large files)
    
    Returns:
        SHA256 hex string
    
    Raises:
        FileNotFoundError: If file not found
        IOError: If file cannot be read
    """
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                sha256.update(data)
        return sha256.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {filepath}")
        raise
    except IOError as e:
        logger.error(f"Failed to read file for checksum: {filepath} - {e}")
        raise


def verify_model_integrity(
    model_filepath: str,
    expected_checksum: str,
    fail_safe: bool = True
) -> Tuple[bool, str]:
    """
    Verify model file integrity with cryptographic checksum.
    
    Fail-safe: If verification fails and fail_safe=True, returns False.
    Model should NOT be loaded if this returns False.
    
    Args:
        model_filepath: Path to model file
        expected_checksum: Expected SHA256 checksum (hex string)
        fail_safe: If True, fail on any error (default: True)
    
    Returns:
        (is_valid: bool, message: str)
    """
    if not expected_checksum:
        msg = "No checksum provided - skipping verification"
        logger.warning(msg)
        return True, msg
    
    try:
        actual_checksum = compute_file_sha256(model_filepath)
        
        if actual_checksum == expected_checksum:
            msg = f"Model integrity verified: {model_filepath}"
            logger.info(msg)
            return True, msg
        else:
            msg = (
                f"Model checksum mismatch!\n"
                f"  File: {model_filepath}\n"
                f"  Expected: {expected_checksum}\n"
                f"  Actual:   {actual_checksum}\n"
                f"  Status: FAIL-SAFE (model will not be loaded)"
            )
            logger.critical(msg)
            return False, msg
    
    except FileNotFoundError as e:
        msg = f"Model file not found: {model_filepath} - FAIL-SAFE"
        logger.critical(msg)
        return False, msg
    
    except Exception as e:
        if fail_safe:
            msg = f"Model verification failed with error: {e} - FAIL-SAFE (treating as compromised)"
            logger.critical(msg)
            return False, msg
        else:
            raise


def validate_model_before_loading(
    model_filepath: str,
    expected_checksum: Optional[str] = None,
    allow_unverified: bool = False
) -> Tuple[bool, str]:
    """
    Pre-load validation of model file.
    
    This is the primary function called before loading a model.
    Implements fail-safe: model will not load if this returns False.
    
    Args:
        model_filepath: Path to model file
        expected_checksum: Expected SHA256 checksum (if None, skips verification)
        allow_unverified: If False, unverified models are rejected (default: False - SECURE)
    
    Returns:
        (should_load: bool, message: str)
    
    Security Notes:
        - If allow_unverified=False (recommended), models without matching checksums are rejected
        - If allow_unverified=True, models can load without verification (use only for development!)
        - Fail-safe: any error results in model rejection
    """
    # Check file exists
    import os
    if not os.path.exists(model_filepath):
        msg = f"Model file not found: {model_filepath} - LOAD DENIED"
        logger.critical(msg)
        return False, msg
    
    # If no checksum provided
    if not expected_checksum:
        if allow_unverified:
            msg = f"No checksum provided, but allow_unverified=True - proceeding (NOT RECOMMENDED)"
            logger.warning(msg)
            return True, msg
        else:
            msg = f"No checksum provided and allow_unverified=False - LOAD DENIED"
            logger.critical(msg)
            return False, msg
    
    # Verify checksum
    is_valid, verify_msg = verify_model_integrity(model_filepath, expected_checksum, fail_safe=True)
    
    return is_valid, verify_msg


def secure_model_load_context(
    model_filepath: str,
    expected_checksum: Optional[str] = None,
    allow_unverified: bool = False
) -> Tuple[bool, str]:
    """
    Secure model loading context check.
    Call this before loading any model to ensure security requirements are met.
    
    Usage:
        ```python
        can_load, message = secure_model_load_context(model_path, checksum)
        if not can_load:
            logger.error(f"Security check failed: {message}")
            return None  # Do not load model
        model = torch.load(model_path)  # Safe to load
        ```
    
    Args:
        model_filepath: Path to model file
        expected_checksum: Expected SHA256 checksum
        allow_unverified: Allow loading without verification
    
    Returns:
        (can_load: bool, message: str)
    """
    return validate_model_before_loading(model_filepath, expected_checksum, allow_unverified)
