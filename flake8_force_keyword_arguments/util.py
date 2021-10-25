import ast
import inspect
from enum import Enum
from types import ModuleType
from typing import Any, Callable, Iterable, Optional, Set


class QualifierOption(str, Enum):
    ONLY_NAME = 'only_name'
    ONLY_WITH_QUALIFIER = 'only_with_qualifier'
    BOTH = 'both'


def list_pos_only_callables(
    m: ModuleType,
    parent_module_qualifier: str,
    poa_threshold: int,
    qualifier_option: QualifierOption = QualifierOption.BOTH,
) -> Iterable[str]:
    """POA: Positional Only Arguments"""
    return _list_pos_only_callables(
        m=m,
        parent_module_qualifier=parent_module_qualifier,
        poa_threshold=poa_threshold,
        visited=set(),
        qualifier_option=qualifier_option,
    )


def _list_pos_only_callables(
    m: ModuleType,
    parent_module_qualifier: str,
    poa_threshold: int,
    visited: Set[ModuleType],
    qualifier_option: QualifierOption = QualifierOption.BOTH,
) -> Iterable[str]:
    """POA: Positional Only Arguments"""
    if m in visited:
        return

    visited.add(m)

    parent_module_qualifiers = parent_module_qualifier.split('.')
    for name, obj in inspect.getmembers(m):
        if name.startswith('_'):
            continue

        if inspect.ismodule(obj):
            yield from _list_pos_only_callables(
                m=obj,
                parent_module_qualifier=f'{parent_module_qualifier}.{name}',
                poa_threshold=poa_threshold,
                visited=visited,
                qualifier_option=qualifier_option,
            )

        if not does_callable_have_poa_more_than(o=obj, poa_threshold=poa_threshold):
            continue

        if parent_module_qualifier == 'builtins' or qualifier_option is not QualifierOption.ONLY_WITH_QUALIFIER:
            yield name

        if qualifier_option is not QualifierOption.ONLY_NAME:
            for i in range(len(parent_module_qualifiers)):
                yield f'{".".join(parent_module_qualifiers[i:])}.{name}'


def does_callable_have_poa_more_than(o: object, poa_threshold: int) -> bool:
    """POA: Positional Only Arguments"""
    func = get_inspectable_function(o)
    if func is None:
        return False

    sig = inspect.signature(func)
    params = tuple(sig.parameters.values())
    if (
        (inspect.ismethoddescriptor(func) or inspect.iscoroutinefunction(func))
        and len(params) > 0
        and params[0].name in ('self', 'cls')
    ):
        params = params[1:]

    poa_count = 0
    for p in params:
        if p.kind is inspect.Parameter.VAR_POSITIONAL:
            return True
        elif p.kind is inspect.Parameter.POSITIONAL_ONLY:
            poa_count += 1

    return poa_count >= poa_threshold


def get_inspectable_function(o: object) -> Optional[Callable[..., Any]]:
    try:
        inspect.signature(o)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        pass
    else:
        return o  # type: ignore

    if inspect.isclass(o):
        try:
            inspect.signature(o.__init__)  # type: ignore[misc]
        except (ValueError, TypeError):
            return None
        else:
            return o.__init__  # type: ignore[no-any-return,misc]
    elif callable(o):
        try:
            inspect.signature(o.__call__)
        except (ValueError, TypeError):
            return None
        else:
            return o.__call__
    return None


def get_invocation_line(c: ast.Call) -> str:
    def dfs(a: ast.AST) -> str:
        child = getattr(a, 'value', None)
        name = getattr(a, 'id', getattr(a, 'attr', None))

        if child is None or not isinstance(child, ast.AST):
            if name is None or not isinstance(name, str):
                return ''
            return name

        return '.'.join(filter(None, (dfs(child), name)))

    return dfs(c.func)
