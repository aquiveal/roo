# Roo

A tool to help manage Roo Code rules files using submodules and symlinks. Roo allows you to manage local symlinks, GitHub folders (via sparse-checkout), and standard Git submodules through a unified CLI, specifically designed to help organize, distribute, and in the future, generate Roo Code custom instructions and rules from documentation, books, and other resources.

## Installation

The recommended way to install Roo is using [pipx](https://github.com/pypa/pipx) to keep it in an isolated environment:

```powershell
pipx install git+https://github.com/aquiveal/roo.git
```

Alternatively, you can install it via pip:

```powershell
pip install git+https://github.com/aquiveal/roo.git
```

## Features

- **Unified CLI**: Simple `add` and `update` commands for all module types.
- **Local Symlinks**: Create relative, OS-specific symlinks that are automatically added to `.gitignore`.
- **GitHub Folders**: Download specific folders from GitHub repositories using Git sparse-checkout.
- **Git Submodules**: Seamless integration with standard Git submodules.
- **Config Driven**: All modules are tracked in a `.roomodules` file for easy versioning and sharing.
- **Windows Support**: Handles administrator elevation automatically on Windows when creating symlinks.

## Usage

### Adding a Module

Add a local directory as a symlink:
```powershell
roo submodule add ./path/to/source ./path/to/link
```

Add a specific folder from a GitHub repository:
```powershell
roo submodule add https://github.com/user/repo/tree/main/folder ./libs/folder
```

Add a full Git repository as a submodule:
```powershell
roo submodule add https://github.com/user/repo.git ./libs/repo
```

### Updating Modules

Update all modules defined in `.roomodules`:
```powershell
roo submodule update
```

## Development

This project uses [PDM](https://pdm-project.org/) for dependency management.

```powershell
# Install dependencies
pdm install

# Run tests
pdm run pytest

# Run the CLI locally
pdm run roo --help
```

## License

MIT
