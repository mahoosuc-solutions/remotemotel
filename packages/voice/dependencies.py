"""
Dependency checking for voice module

Ensures all required dependencies are available before importing voice components.
"""

import sys
import logging

logger = logging.getLogger(__name__)

# Required dependencies for voice module
REQUIRED_DEPENDENCIES = [
    ("pydub", "pydub", "Pydub is required for audio format conversions"),
    ("webrtcvad", "webrtcvad", "webrtcvad is required for Voice Activity Detection"),
    ("websockets", "websockets", "WebSockets is required for real-time audio streaming"),
    ("twilio", "twilio", "Twilio is required for phone call handling"),
]

# Optional dependencies (warn if missing but don't fail)
OPTIONAL_DEPENDENCIES = [
    ("numpy", "numpy", "NumPy is recommended for audio processing"),
    ("openai", "openai", "OpenAI is required for Realtime API"),
    ("fastapi", "fastapi", "FastAPI is required for web endpoints"),
    ("uvicorn", "uvicorn", "Uvicorn is required for ASGI server"),
]

def check_required_dependencies():
    """
    Check that all required dependencies are available.
    
    Raises:
        ImportError: If any required dependency is missing
    """
    missing_deps = []
    
    # Check required dependencies
    for module_name, package_name, error_message in REQUIRED_DEPENDENCIES:
        try:
            __import__(module_name)
            logger.debug(f"✓ {package_name} is available")
        except ImportError:
            missing_deps.append((package_name, error_message))
            logger.error(f"✗ {package_name} is missing")
    
    # Check optional dependencies
    for module_name, package_name, error_message in OPTIONAL_DEPENDENCIES:
        try:
            __import__(module_name)
            logger.debug(f"✓ {package_name} is available")
        except ImportError:
            logger.warning(f"⚠ {package_name} is missing - {error_message}")
    
    if missing_deps:
        error_msg = "Missing required dependencies:\n"
        for package_name, error_message in missing_deps:
            error_msg += f"  - {error_message}\n"
        error_msg += f"\nInstall missing dependencies with:\n"
        error_msg += f"  pip install {' '.join(dep[0] for dep in missing_deps)}"
        
        raise ImportError(error_msg)
    
    logger.info("✓ All required dependencies are available")

def get_dependency_info():
    """
    Get information about installed dependencies.
    
    Returns:
        dict: Information about dependency versions
    """
    info = {}
    
    for module_name, package_name, _ in REQUIRED_DEPENDENCIES:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'unknown')
            info[package_name] = {
                'available': True,
                'version': version,
                'module': module_name
            }
        except ImportError:
            info[package_name] = {
                'available': False,
                'version': None,
                'module': module_name
            }
    
    return info

def log_dependency_info():
    """Log information about all dependencies."""
    info = get_dependency_info()
    
    logger.info("Voice module dependency status:")
    for package_name, dep_info in info.items():
        if dep_info['available']:
            logger.info(f"  ✓ {package_name} v{dep_info['version']}")
        else:
            logger.error(f"  ✗ {package_name} - NOT AVAILABLE")