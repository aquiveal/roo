import os
import configparser
from pathlib import Path
from roo.services import create_symlink, load_modules_config, ensure_ignored

def test_create_symlink(temp_repo, mock_os_symlink):
    src = temp_repo / "source_dir"
    src.mkdir()
    (src / "file.txt").write_text("hello")
    
    dst = temp_repo / "dest_dir" / "link"
    
    create_symlink(str(src), str(dst))
    
    mock_os_symlink.assert_called_once()

def test_load_save_config(temp_repo):
    config = load_modules_config()
    config.add_section('submodule "test"')
    config.set('submodule "test"', 'path', 'test')
    
    from roo.services import save_modules_config
    save_modules_config(config)
    
    assert os.path.exists(".roomodules")
    
    new_config = load_modules_config()
    assert new_config.has_section('submodule "test"')
    assert new_config.get('submodule "test"', 'path') == 'test'

def test_ensure_ignored(temp_repo):
    ensure_ignored("some/path")
    
    gitignore = Path(".gitignore")
    assert gitignore.exists()
    content = gitignore.read_text()
    assert "# Roo Modules" in content
    assert "some/path" in content
