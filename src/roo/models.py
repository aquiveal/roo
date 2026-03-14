from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

class ModuleType(Enum):
    SYMLINK = "symlink"
    GITHUB_FOLDER = "github_folder"
    GIT_SUBMODULE = "git_submodule"

@dataclass(frozen=True)
class Module:
    path: str
    url: str
    type: Optional[ModuleType] = None
    
    @property
    def section_name(self) -> str:
        return f'submodule "{self.path}"'

    def __eq__(self, other):
        if not isinstance(other, Module):
            return False
        return self.path == other.path

    def __hash__(self):
        return hash(self.path)
