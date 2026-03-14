import os
import sys
import platform
import ctypes
import logging
from pathlib import Path

logger = logging.getLogger("roo")

def is_admin() -> bool:
    if platform.system() != "Windows":
        return True
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        return True
    except Exception:
        return False

def elevate_and_run(args: list[str], original_cwd: str):
    logger.info("Requesting Administrator privileges...")
    
    # Use 'python -m roo' to ensure it works across different installation methods
    params = f'-m roo ' + " ".join([f'"{arg}"' for arg in args]) + ' --elevated'
    
    # shell32.ShellExecuteW parameters: hwnd, operation, file, parameters, directory, show
    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, original_cwd, 1)
    
    if int(ret) > 32:
        logger.info("Elevation requested successfully. Please check the new Administrator window.")
        sys.exit(0)
    else:
        logger.error(f"Failed to elevate privileges. Error code: {ret}")
        sys.exit(1)
