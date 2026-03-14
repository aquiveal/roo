import subprocess
from roo.external_services import add_remote_module, download_github_folder

def test_download_github_folder(mocker, temp_repo):
    mock_run = mocker.patch("subprocess.run")
    
    # Mock shutil.move and shutil.rmtree to avoid actual filesystem changes
    mocker.patch("shutil.move")
    mocker.patch("shutil.rmtree")
    
    # Create the source folder that the service expects to exist before moving
    # We need to know what tmp_dir the service will generate.
    # In external_services.py: tmp_dir = Path.cwd() / f".tmp_{repo}_{branch}"
    # repo=repo, branch=branch
    tmp_dir = temp_repo / ".tmp_repo_branch"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    source_folder = tmp_dir / "folder"
    source_folder.mkdir(parents=True, exist_ok=True)

    url = "https://github.com/user/repo/tree/branch/folder"
    dest = "my_dest"
    
    download_github_folder(url, dest)
    
    # Check that git clone was called
    mock_run.assert_any_call(
        ["git", "clone", "--no-checkout", "--depth", "1", "--branch", "branch", "https://github.com/user/repo.git", mocker.ANY],
        check=True, capture_output=True
    )

def test_add_remote_module_submodule(mocker, temp_repo):
    # Mock subprocess.run locally in external_services
    mock_run = mocker.patch("roo.external_services.subprocess.run")
    # Mock get_git_root where it's used in external_services
    mocker.patch("roo.external_services.get_git_root", return_value=temp_repo)
    
    # URL without /tree/ should trigger git submodule add
    url = "https://github.com/user/repo.git"
    dst = "libs/repo"
    
    add_remote_module(url, dst)
    
    # Check that git submodule add was called
    mock_run.assert_called_once_with(
        ["git", "submodule", "add", "--force", url, dst],
        check=True
    )
    
    assert (temp_repo / ".roomodules").exists()
