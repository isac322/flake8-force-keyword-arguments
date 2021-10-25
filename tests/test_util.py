import ast
import sys
from functools import partial
from textwrap import dedent
from typing import Set

import pytest

from flake8_force_keyword_arguments import util

if sys.version_info < (3, 8):
    from typing_extensions import Final
else:
    from typing import Final


@pytest.mark.parametrize(
    ('source_code', 'expected'),
    (
        ('a()', 'a'),
        ('a(p=132)', 'a'),
        ('a.b()', 'a.b'),
        ('a.b(111, p=123)', 'a.b'),
        ('a.b().c.d()', 'c.d'),
        ('"test".a.b()', 'a.b'),
        ('globals()[\'multiple_arguments\'](1, 2, 3)', ''),
    ),
)
def test_get_invocation_line(source_code: str, expected: str) -> None:
    a = ast.parse(source_code).body[0].value  # type: ignore[attr-defined]
    assert util.get_invocation_line(a) == expected


@pytest.mark.parametrize(
    ('obj', 'expected_attribute_name'),
    (
        (1, None),
        ('qwr', None),
        (int, '__init__'),
        (getattr, '__call__'),
        (type('TestClass', (), dict(__init__=lambda self, a, b: None)), '$self$'),
        (lambda c: None, '$self$'),
        (type('TestClass', (), dict(__call__=lambda self, a: None))(), '$self$'),
    ),
)
def test_get_inspectable_function(obj, expected_attribute_name):
    if expected_attribute_name == '$self$':
        assert util.get_inspectable_function(obj) == obj
    elif expected_attribute_name is None:
        assert util.get_inspectable_function(obj) is None
    else:
        assert util.get_inspectable_function(obj) == getattr(obj, expected_attribute_name)


@pytest.mark.parametrize(
    ('obj', 'threshold', 'expected'),
    (
        (1, 0, False),
        (1, 1, False),
        (1, 2, False),
        ('qwr', 0, False),
        ('qwr', 1, False),
        (int, 0, True),
        (int, 1, True),
        (int, 2, True),
        (getattr, 0, True),
        (getattr, 1, True),
        (getattr, 2, True),
        (type('TestClass', (), dict(__init__=lambda self, a, b: None)), 0, True),
        (type('TestClass', (), dict(__init__=lambda self, a, b: None)), 1, False),
        (type('TestClass', (), dict(__init__=lambda self, a, b: None)), 2, False),
        (type('TestClass', (), dict(__init__=lambda self: None)), 0, True),
        (type('TestClass', (), dict(__init__=lambda self: None)), 1, False),
        (type('TestClass', (), dict(__init__=lambda self: None)), 2, False),
        (lambda c: None, 0, True),
        (lambda c: None, 1, False),
        (lambda c: None, 2, False),
        (partial(lambda c, d: None, 1), 0, True),
        (partial(lambda c, d: None, 1), 1, False),
        (partial(lambda c, d: None, 1), 2, False),
        (type('TestClass', (), dict(__call__=lambda self, a: None))(), 0, True),
        (type('TestClass', (), dict(__call__=lambda self, a: None))(), 1, False),
        (type('TestClass', (), dict(__call__=lambda self, a: None))(), 2, False),
        (issubclass, 0, True),
        (issubclass, 1, True),
        (issubclass, 2, True),
    ),
)
def test_does_callable_have_poa_more_than(obj: object, threshold: int, expected: bool) -> None:
    assert util.does_callable_have_poa_more_than(obj, poa_threshold=threshold) is expected


class TestListPosOnlyCallables:
    TEMP_MODULE_NAME: Final[str] = 'test_module'

    @pytest.mark.parametrize(
        ('source_code', 'poa_threshold', 'expected'),
        (
            (
                dedent(
                    '''
                     def func_with_var_args(*args):
                         pass
                     '''
                ),
                0,
                {'func_with_var_args', f'{TEMP_MODULE_NAME}.func_with_var_args'},
            ),
            (
                dedent(
                    '''
                     def func_with_var_args(*args):
                         pass
                     '''
                ),
                1,
                {'func_with_var_args', f'{TEMP_MODULE_NAME}.func_with_var_args'},
            ),
        ),
    )
    def test_simple(self, source_code: str, poa_threshold: int, expected: Set[str], register_module) -> None:
        module = register_module(module_name=self.TEMP_MODULE_NAME, source_code=source_code)
        actual = set(
            util.list_pos_only_callables(
                m=module,
                parent_module_qualifier=self.TEMP_MODULE_NAME,
                poa_threshold=poa_threshold,
            )
        )
        assert actual == expected

    @pytest.mark.parametrize(
        ('source_code', 'poa_threshold', 'qualifier_option', 'expected'),
        (
            (
                dedent(
                    '''
                     def func_with_var_args(*args):
                         pass
                     '''
                ),
                0,
                util.QualifierOption.BOTH,
                {'func_with_var_args', f'{TEMP_MODULE_NAME}.func_with_var_args'},
            ),
            (
                dedent(
                    '''
                     def func_with_var_args(*args):
                         pass
                     '''
                ),
                1,
                util.QualifierOption.ONLY_WITH_QUALIFIER,
                {f'{TEMP_MODULE_NAME}.func_with_var_args'},
            ),
            (
                dedent(
                    '''
                     def func_with_var_args(*args):
                         pass
                     '''
                ),
                0,
                util.QualifierOption.ONLY_NAME,
                {'func_with_var_args'},
            ),
        ),
    )
    def test_qualifier_option(
        self,
        source_code: str,
        poa_threshold: int,
        qualifier_option: util.QualifierOption,
        expected: Set[str],
        register_module,
    ) -> None:
        module = register_module(module_name=self.TEMP_MODULE_NAME, source_code=source_code)
        actual = set(
            util.list_pos_only_callables(
                m=module,
                parent_module_qualifier=self.TEMP_MODULE_NAME,
                poa_threshold=poa_threshold,
                qualifier_option=qualifier_option,
            )
        )
        assert actual == expected

    @pytest.mark.skipif(sys.version_info < (3, 8), reason='requires python3.8 or higher')
    @pytest.mark.parametrize(
        ('source_code', 'poa_threshold', 'expected'),
        (
            (
                dedent(
                    '''
                     def func_with_poa(a, b, /):
                         pass
                     '''
                ),
                1,
                {'func_with_poa', f'{TEMP_MODULE_NAME}.func_with_poa'},
            ),
            (
                dedent(
                    '''
                     def func_with_poa(a, b, /):
                         pass
                     '''
                ),
                2,
                {'func_with_poa', f'{TEMP_MODULE_NAME}.func_with_poa'},
            ),
            (
                dedent(
                    '''
                     def func_with_poa(a, b, /):
                         pass
                     '''
                ),
                3,
                set(),
            ),
        ),
    )
    def test_pos_only_args(self, source_code: str, poa_threshold: int, expected: Set[str], register_module) -> None:
        module = register_module(module_name=self.TEMP_MODULE_NAME, source_code=source_code)
        actual = set(
            util.list_pos_only_callables(
                m=module,
                parent_module_qualifier=self.TEMP_MODULE_NAME,
                poa_threshold=poa_threshold,
            )
        )
        assert actual == expected

    @pytest.mark.parametrize(
        ('source_code', 'poa_threshold', 'py38', 'expected'),
        (
            (
                dedent(
                    '''
                     l_callable = lambda a: None
                     l_callable2 = lambda *args: None
                     '''
                ),
                0,
                False,
                {'l_callable', 'l_callable2', f'{TEMP_MODULE_NAME}.l_callable', f'{TEMP_MODULE_NAME}.l_callable2'},
            ),
            (
                dedent(
                    '''
                     l_callable = lambda a: None
                     l_callable2 = lambda *args: None
                     '''
                ),
                1,
                False,
                {'l_callable2', f'{TEMP_MODULE_NAME}.l_callable2'},
            ),
            (
                dedent(
                    '''
                     l_callable = lambda a, /: None
                     l_callable2 = lambda *args: None
                     l_callable3 = lambda a, b, /: None
                     '''
                ),
                2,
                True,
                {'l_callable2', f'{TEMP_MODULE_NAME}.l_callable2', 'l_callable3', f'{TEMP_MODULE_NAME}.l_callable3'},
            ),
        ),
    )
    def test_lambda(
        self,
        source_code: str,
        poa_threshold: int,
        py38: bool,
        expected: Set[str],
        register_module,
    ) -> None:
        if py38 and sys.version_info < (3, 8):
            pytest.skip('requires python3.8 or higher')

        module = register_module(module_name=self.TEMP_MODULE_NAME, source_code=source_code)
        actual = set(
            util.list_pos_only_callables(
                m=module,
                parent_module_qualifier=self.TEMP_MODULE_NAME,
                poa_threshold=poa_threshold,
            )
        )
        assert actual == expected

    def test_builtins_ignore_only_name_qualifier_option(self, register_module) -> None:
        m = register_module(
            module_name=self.TEMP_MODULE_NAME,
            source_code=dedent(
                '''
                 def func_with_var_args(*args):
                     pass
                 '''
            ),
        )
        actual = set(
            util.list_pos_only_callables(
                m=m,
                parent_module_qualifier='builtins',
                poa_threshold=0,
                qualifier_option=util.QualifierOption.ONLY_WITH_QUALIFIER,
            )
        )
        assert actual == {'func_with_var_args', 'builtins.func_with_var_args'}

    def test_nested_module(self, register_module) -> None:
        m = register_module(module_name='parent', source_code='l_callable = lambda a: None')
        register_module(module_name='child', source_code='l_callable2 = lambda *args: None', parent_module=m)

        actual = set(
            util.list_pos_only_callables(
                m=m,
                parent_module_qualifier='parent',
                poa_threshold=0,
            )
        )
        assert actual == {
            'l_callable',
            'l_callable2',
            'child.l_callable2',
            'parent.l_callable',
            'parent.child.l_callable2',
        }
