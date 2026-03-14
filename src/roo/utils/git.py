import subprocess
import logging
from pathlib import Path

logger = logging.getLogger("roo")

class GitError(Exception):
    pass

def get_git_root() -> Path:
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip()).resolve()
    except subprocess.CalledProcessError:
        raise GitError("Not inside a git repository.")
    except FileNotFoundError:
        raise GitError("git command not found.")

def is_github_url(url: str) -> bool:
    return url.startswith(("https://github.com/", "http://github.com/"))

def is_github_folder_url(url: str) -> bool:
    import re
    return bool(re.match(r"https?://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.*)", url))
