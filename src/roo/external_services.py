import os
import re
import shutil
import subprocess
import logging
from pathlib import Path

from roo.services import load_modules_config, save_modules_config, ensure_ignored
from roo.utils.git import get_git_root

logger = logging.getLogger("roo")

class ExternalServiceError(Exception):
    pass

def download_github_folder(url: str, dest_str: str):
    dest_path = Path(dest_str).resolve()
    
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.*)", url)
    if not match:
        raise ExternalServiceError(f"Invalid GitHub folder URL format: {url}")
        
    owner, repo, branch, folder_path = match.groups()
    repo_url = f"https://github.com/{owner}/{repo}.git"
    
    logger.info(f"Downloading from {repo_url} (branch: {branch}, folder: {folder_path})")
    
    tmp_dir = Path.cwd() / f".tmp_{repo}_{branch}"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
        
    try:
        subprocess.run(["git", "clone", "--no-checkout", "--depth", "1", "--branch", branch, repo_url, str(tmp_dir)], check=True, capture_output=True)
        subprocess.run(["git", "sparse-checkout", "init", "--cone"], cwd=str(tmp_dir), check=True, capture_output=True)
        subprocess.run(["git", "sparse-checkout", "set", folder_path], cwd=str(tmp_dir), check=True, capture_output=True)
        subprocess.run(["git", "checkout"], cwd=str(tmp_dir), check=True, capture_output=True)
        
        source_folder = tmp_dir / folder_path
        if not source_folder.exists():
            raise ExternalServiceError(f"Folder '{folder_path}' not found in repository.")
            
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        if dest_path.exists():
            if dest_path.is_dir() and not dest_path.is_symlink():
                shutil.rmtree(dest_path)
            else:
                dest_path.unlink()
                
        shutil.move(str(source_folder), str(dest_path))
        logger.info(f"Successfully downloaded to {dest_str}")
        
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise ExternalServiceError(f"Git operation failed: {stderr}")
    finally:
        if tmp_dir.exists():
            def handle_remove_readonly(func, path, exc_info):
                import stat
                os.chmod(path, stat.S_IWRITE)
                func(path)
            shutil.rmtree(tmp_dir, onerror=handle_remove_readonly)

def add_remote_module(src: str, dst: str):
    if re.match(r"https?://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.*)", src):
        download_github_folder(src, dst)
        
        config = load_modules_config()
        try:
            repo_root = get_git_root()
            dst_rel = Path(dst).absolute().relative_to(repo_root).as_posix()
        except ValueError:
            dst_rel = Path(dst).absolute().as_posix()
            
        ensure_ignored(dst_rel)
            
        section_name = f'submodule "{dst_rel}"'
        if not config.has_section(section_name):
            config.add_section(section_name)
            
        config.set(section_name, 'path', dst_rel)
        config.set(section_name, 'url', src)
        
        save_modules_config(config)
    else:
        logger.info(f"Adding full repository as git submodule: {src} -> {dst}")
        try:
            subprocess.run(["git", "submodule", "add", "--force", src, dst], check=True)
            logger.info(f"Successfully added git submodule: {dst}")
            
            config = load_modules_config()
            try:
                repo_root = get_git_root()
                dst_rel = Path(dst).resolve().relative_to(repo_root).as_posix()
            except ValueError:
                dst_rel = Path(dst).resolve().as_posix()
                
            section_name = f'submodule "{dst_rel}"'
            if not config.has_section(section_name):
                config.add_section(section_name)
                
            config.set(section_name, 'path', dst_rel)
            config.set(section_name, 'url', src)
            
            save_modules_config(config)
        except subprocess.CalledProcessError as e:
            raise ExternalServiceError(f"Failed to add git submodule: {e}")
