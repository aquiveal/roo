import pytest
import os
import shutil
import subprocess
from pathlib import Path

@pytest.fixture
def temp_repo(tmp_path):
    """Create a temporary git repository for testing."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    
    # Initialize git
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    
    # Configure git
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
    
    # Create an initial commit
    (repo_dir / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_dir, check=True)
    
    old_cwd = os.getcwd()
    os.chdir(repo_dir)
    yield repo_dir
    os.chdir(old_cwd)

@pytest.fixture
def mock_git_root(mocker, temp_repo):
    """Mock get_git_root to return the temp_repo path."""
    return mocker.patch("roo.utils.git.get_git_root", return_value=temp_repo)

@pytest.fixture
def mock_os_symlink(mocker):
    """Mock os.symlink to avoid privilege issues on Windows."""
    return mocker.patch("os.symlink")
