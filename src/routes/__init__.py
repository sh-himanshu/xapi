import pkgutil
from pathlib import Path

current_dir = str(Path(__file__).parent)
submodules = pkgutil.iter_modules([current_dir])
