import types
from textwrap import dedent
from typing import Dict, Optional

import pytest
import sys


@pytest.fixture()
def register_module():
    created_modules: Dict[str, types.ModuleType] = dict()

    def _inner(
        module_name: str,
        source_code: str,
        parent_module: Optional[types.ModuleType] = None,
    ) -> types.ModuleType:
        if parent_module is not None:
            orig_module_name = module_name
            module_name = f'{parent_module.__name__}.{module_name}'

        module = types.ModuleType(module_name)
        created_modules[module_name] = module

        exec(compile(source=source_code, filename='__init__.py', mode='exec'), module.__dict__)  # noqa: S102
        sys.modules[module_name] = module

        if parent_module is not None:
            setattr(parent_module, orig_module_name, module)

        return module

    yield _inner

    for m in created_modules.keys():
        if m in sys.modules:
            del sys.modules[m]


@pytest.fixture()
def flake8_path(flake8_path):
    (flake8_path / 'setup.cfg').write_text(
        dedent(
            '''
            [flake8]
            select = FKA1
            '''
        )
    )
    return flake8_path
