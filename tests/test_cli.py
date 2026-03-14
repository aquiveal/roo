from typer.testing import CliRunner
from roo.cli import app
import os
from pathlib import Path

runner = CliRunner()

def test_cli_add_symlink(temp_repo, mock_git_root, mock_os_symlink):
    src = temp_repo / "my_source"
    src.mkdir()
    
    # Use relative path for dst as it's common in CLI usage
    result = runner.invoke(app, ["submodule", "add", str(src), "my_link"])
    
    assert result.exit_code == 0
    assert "Created local OS-specific symlink" in result.stdout
    mock_os_symlink.assert_called_once()
    assert os.path.exists(".roomodules")

def test_cli_submodule_add_alias(temp_repo, mock_git_root, mock_os_symlink):
    src = temp_repo / "my_source_2"
    src.mkdir()
    
    result = runner.invoke(app, ["submodule", "add", str(src), "my_link_2"])
    
    assert result.exit_code == 0
    mock_os_symlink.assert_called_once()

def test_cli_update(temp_repo, mock_git_root, mock_os_symlink):
    # Setup .roomodules manually
    src = temp_repo / "actual_source"
    src.mkdir()
    (src / "data.txt").write_text("important")
    
    from roo.services import load_modules_config, save_modules_config
    config = load_modules_config()
    section = 'submodule "links/data"'
    config.add_section(section)
    config.set(section, 'path', 'links/data')
    config.set(section, 'url', f"file:///{src.as_posix()}")
    save_modules_config(config)
    
    result = runner.invoke(app, ["submodule", "update"])
    
    assert result.exit_code == 0
    mock_os_symlink.assert_called_once()
