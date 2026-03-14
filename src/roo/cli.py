# src/roo/cli.py
import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Annotated, Optional
import typer
import re

from roo.services import (
    load_modules_config, 
    create_symlink, 
    RooError, 
    ROOMODULES_FILE
)
from roo.external_services import add_remote_module, download_github_folder, ExternalServiceError
from roo.utils.git import get_git_root, is_github_url, GitError
from roo.utils.os import is_admin, elevate_and_run

from rich.console import Console

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)
logger = logging.getLogger("roo")
console = Console()

app = typer.Typer(help="A tool to help manage Roo Code rules files", no_args_is_help=True)
submodule_app = typer.Typer(help="Manage submodules and rules")
app.add_typer(submodule_app, name="submodule")

def resolve_paths(src: str, dst: str):
    original_cwd = Path.cwd()
    try:
        git_root = get_git_root()
    except GitError as e:
        logger.error(str(e))
        raise typer.Exit(code=1)

    # Normalize source
    if not is_github_url(src):
        src_path = Path(src)
        if not src_path.is_absolute():
            src_abs = (original_cwd / src).absolute()
        else:
            src_abs = src_path.absolute()
        try:
            resolved_src = os.path.relpath(src_abs, git_root).replace('\\', '/')
        except ValueError:
            resolved_src = str(src_abs).replace('\\', '/')
    else:
        resolved_src = src

    # Normalize destination
    dst_path = Path(dst)
    if not dst_path.is_absolute():
        dst_abs = (original_cwd / dst).absolute()
    else:
        dst_abs = dst_path.absolute()
    try:
        resolved_dst = os.path.relpath(dst_abs, git_root).replace('\\', '/')
    except ValueError:
        resolved_dst = str(dst_abs).replace('\\', '/')

    return resolved_src, resolved_dst, git_root

@submodule_app.command(name="add")
def add(
    src: Annotated[str, typer.Argument(help="Source path or GitHub URL")],
    dst: Annotated[str, typer.Argument(help="Destination path")],
    elevated: Annotated[bool, typer.Option(hidden=True)] = False
):
    """Add a new submodule or symlink."""
    src, dst, git_root = resolve_paths(src, dst)
    
    # Change to git root for consistency
    os.chdir(git_root)
    
    try:
        if is_github_url(src):
            add_remote_module(src, dst)
        else:
            try:
                create_symlink(src, dst)
            except OSError as e:
                import platform
                if platform.system() == "Windows" and getattr(e, "winerror", None) == 1314:
                    if elevated or is_admin():
                        logger.error(f"Failed to create symlink even with elevated privileges: {e}")
                        raise typer.Exit(code=1)
                    else:
                        logger.warning(f"Privilege error detected: {e}")
                        # Filter out --elevated from sys.argv and call elevate_and_run
                        # In Typer, we need to be careful with how we reconstruct args
                        args = [arg for arg in sys.argv[1:] if arg != "--elevated"]
                        elevate_and_run(args, str(git_root))
                        return
                else:
                    logger.error(f"Failed to create symlink: {e}")
                    raise typer.Exit(code=1)
    except (RooError, ExternalServiceError) as e:
        logger.error(str(e))
        raise typer.Exit(code=1)

@submodule_app.command(name="update")
def update(
    elevated: Annotated[bool, typer.Option(hidden=True)] = False
):
    """Update all submodules from .roomodules."""
    try:
        git_root = get_git_root()
    except GitError as e:
        logger.error(str(e))
        raise typer.Exit(code=1)
        
    os.chdir(git_root)
    
    config = load_modules_config()
    if not config.sections():
        logger.info("No .roomodules found or file is empty.")
        return
        
    logger.info(f"Updating submodules from {ROOMODULES_FILE}...")
    
    for section in config.sections():
        if not section.startswith('submodule "'):
            continue
            
        dst_rel = config.get(section, 'path', fallback=None)
        if not dst_rel:
            logger.warning(f"Skipping {section}: No path specified")
            continue
            
        source_url = config.get(section, 'url', fallback=None)
        if not source_url:
            logger.warning(f"Skipping {section}: No url specified")
            continue
            
        try:
            if is_github_url(source_url):
                if re.match(r"https?://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.*)", source_url):
                    logger.info(f"Processing remote folder: {dst_rel}")
                    download_github_folder(source_url, dst_rel)
                else:
                    logger.info(f"Processing full git submodule: {dst_rel}")
                    subprocess.run(["git", "submodule", "update", "--init", "--recursive", dst_rel], check=True)
            elif source_url.startswith("file://"):
                src_uri_path = source_url[len("file://"):]
                if src_uri_path.startswith('/'):
                    src_uri_path = src_uri_path[1:]
                    
                if re.match(r"^[A-Za-z]:/", src_uri_path) or src_uri_path.startswith('/'):
                    src_path = Path(src_uri_path)
                else:
                    src_path = git_root / src_uri_path
                    
                dst_path = git_root / dst_rel
                
                logger.info(f"Processing local symlink: {dst_rel} -> {src_path}")
                try:
                    create_symlink(str(src_path), str(dst_path), is_update=True)
                except OSError as e:
                    import platform
                    if platform.system() == "Windows" and getattr(e, "winerror", None) == 1314:
                        if elevated or is_admin():
                            logger.error(f"Failed to create symlink even with elevated privileges: {e}")
                        else:
                            logger.warning(f"Privilege error detected: {e}")
                            args = [arg for arg in sys.argv[1:] if arg != "--elevated"]
                            elevate_and_run(args, str(git_root))
                            return
                    else:
                        logger.error(f"Failed to create symlink: {e}")
            else:
                logger.warning(f"Skipping {section}: Unrecognized url format '{source_url}'")
        except (RooError, ExternalServiceError, subprocess.CalledProcessError) as e:
            logger.error(f"Error processing {section}: {e}")

    logger.info("Submodule update complete.")
    
    if elevated:
        logger.info("(Window will close automatically)")
        input("Press Enter to exit...")

if __name__ == "__main__":
    app()
