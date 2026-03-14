# src/roo/services.py
import os
import platform
import logging
import configparser
from pathlib import Path
from typing import Optional

from roo.models import Module, ModuleType
from roo.utils.git import get_git_root

logger = logging.getLogger("roo")

ROOMODULES_FILE = ".roomodules"

class RooError(Exception):
    pass

def load_modules_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    if not os.path.exists(ROOMODULES_FILE):
        return config
    try:
        config.read(ROOMODULES_FILE)
        return config
    except Exception as e:
        logger.error(f"Error reading {ROOMODULES_FILE}: {e}")
        return config

def save_modules_config(config: configparser.ConfigParser):
    with open(ROOMODULES_FILE, 'w') as f:
        for section in config.sections():
            f.write(f'[{section}]\n')
            for key, value in config.items(section):
                f.write(f'\t{key} = {value}\n')
    print(f"Updated {ROOMODULES_FILE}")

def ensure_ignored(path_rel: str):
    """Ensure a given relative path is in .gitignore under '# Roo Modules'."""
    gitignore_path = Path(".gitignore")
    path_to_ignore = path_rel.replace('\\', '/')
    header = "# Roo Modules"
    
    lines = []
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            lines = f.readlines()
            
    # Check if already ignored anywhere
    for line in lines:
        if line.strip() == path_to_ignore:
            return
            
    logger.info(f"Adding '{path_to_ignore}' to .gitignore")
    
    header_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == header:
            header_idx = i
            break
            
    if header_idx != -1:
        lines.insert(header_idx + 1, f"{path_to_ignore}\n")
    else:
        if lines and not lines[-1].endswith('\n'):
            lines[-1] += '\n'
        if lines:
            lines.append('\n')
        lines.append(f"{header}\n")
        lines.append(f"{path_to_ignore}\n")
        
    with open(gitignore_path, 'w') as f:
        f.writelines(lines)

def create_symlink(src_str: str, dst_str: str, is_update: bool = False):
    source_path = Path(src_str).absolute()
    dest_path = Path(dst_str).absolute()

    if not source_path.exists():
        raise RooError(f"Source path '{src_str}' does not exist.")

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if dest_path.exists() or dest_path.is_symlink():
        logger.warning(f"Destination '{dst_str}' already exists. Overwriting...")
        if dest_path.is_dir() and not dest_path.is_symlink():
            import shutil
            shutil.rmtree(dest_path)
        else:
            dest_path.unlink()

    relative_target = os.path.relpath(source_path, dest_path.parent)

    if platform.system() == "Windows":
        local_target = relative_target.replace('/', '\\')
    else:
        local_target = relative_target.replace('\\', '/')

    is_dir = source_path.is_dir()

    try:
        os.symlink(local_target, dest_path, target_is_directory=is_dir)
        print(f"Created local OS-specific symlink: {dst_str} -> {local_target}")
        
        if is_update:
            return
            
        repo_root = get_git_root()
        try:
            dst_rel = dest_path.relative_to(repo_root).as_posix()
        except ValueError:
            dst_rel = dest_path.as_posix()
            
        original_src_path = Path(src_str)
        if original_src_path.is_absolute():
            src_url_path = source_path.as_posix()
            if not src_url_path.startswith('/'):
                src_url_path = '/' + src_url_path
        else:
            try:
                src_url_path = source_path.relative_to(repo_root).as_posix()
            except ValueError:
                src_url_path = os.path.relpath(source_path, repo_root).replace('\\', '/')
            
        ensure_ignored(dst_rel)
            
        config = load_modules_config()
        section_name = f'submodule "{dst_rel}"'
        if not config.has_section(section_name):
            config.add_section(section_name)
            
        config.set(section_name, 'path', dst_rel)
        
        if is_dir and not src_url_path.endswith('/'):
            src_url_path += '/'
            
        if src_url_path.startswith('/'):
            config.set(section_name, 'url', f"file://{src_url_path}")
        else:
            config.set(section_name, 'url', f"file:///{src_url_path}")
        
        save_modules_config(config)
        
    except OSError as e:
        # Re-raise to let CLI handle elevation if needed
        raise e
