import importlib

from . import routes


def load_modules() -> None:
    for mod in routes.submodules:
        importlib.reload(
            importlib.import_module(f"{routes.__name__}.{mod.name}", __name__)
        )
