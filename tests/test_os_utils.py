import sys
from unittest.mock import MagicMock
from roo.utils.os import elevate_and_run

def test_elevate_and_run(mocker):
    # Mock ctypes.windll.shell32.ShellExecuteW
    mock_shell32 = MagicMock()
    mocker.patch("ctypes.windll.shell32", mock_shell32)
    
    # Mock sys.exit to avoid exiting the test
    mocker.patch("sys.exit")
    
    args = ["submodule", "add", "src", "dst"]
    original_cwd = "C:\\test"
    
    elevate_and_run(args, original_cwd)
    
    # Verify ShellExecuteW was called
    # params = f'-m roo ' + " ".join([f'"{arg}"' for arg in args]) + ' --elevated'
    expected_params = '-m roo "submodule" "add" "src" "dst" --elevated'
    
    mock_shell32.ShellExecuteW.assert_called_once_with(
        None, "runas", sys.executable, expected_params, original_cwd, 1
    )
