from textwrap import dedent


def test_builtins_inspected(flake8_path):
    (flake8_path / 'example.py').write_text(
        'getattr(object(), \'test\')',
    )
    result = flake8_path.run_flake8(['--kwargs-max-positional-arguments', '2'])
    assert result.out_lines == []


def test_kwargs_inspect_module_overwrites(flake8_path):
    (flake8_path / 'example.py').write_text(
        'getattr(object(), \'test\')',
    )
    result = flake8_path.run_flake8(['--kwargs-max-positional-arguments', '2', '--kwargs-inspect-module', 'os'])
    assert result.out_lines == [
        './example.py:1:1: FKA100 getattr\'s call uses 2 positional arguments, use keyword arguments.'
    ]


def test_kwargs_inspect_module_extended(flake8_path):
    (flake8_path / 'example.py').write_text(
        'getattr(object(), os.path.join(\'test\', \'arg\'))',
    )
    result = flake8_path.run_flake8(['--kwargs-max-positional-arguments', '2', '--kwargs-inspect-module-extend', 'os'])
    assert result.out_lines == []


def test_default_ignore_function_pattern(flake8_path):
    (flake8_path / 'example.py').write_text(
        'object.__getattr__(object(), \'test\')',
    )
    result = flake8_path.run_flake8(['--kwargs-max-positional-arguments', '2'])
    assert result.out_lines == []


def test_default_ignore_function_pattern_typing_cast(flake8_path):
    (flake8_path / 'example.py').write_text(
        '''
        typing.cast(object, \'test\')
        cast(object, 1)
        ''',
    )
    result = flake8_path.run_flake8(['--kwargs-max-positional-arguments', '2'])
    assert result.out_lines == []


def test_ignore_function_pattern_extended(flake8_path):
    (flake8_path / 'example.py').write_text(
        'tt = lambda a, b, c: None',
    )
    result = flake8_path.run_flake8(
        ['--kwargs-max-positional-arguments', '2', '--kwargs-ignore-function-pattern-extend', '^tt$']
    )
    assert result.out_lines == []


def test_ignore_function_pattern_extended_multiple(flake8_path):
    (flake8_path / 'example.py').write_text(
        dedent(
            '''
            tt = lambda a, b, c: None
            o = object()
            o.test_function(1, 2, 3)
            '''
        ),
    )
    result = flake8_path.run_flake8(
        ['--kwargs-max-positional-arguments', '2', '--kwargs-ignore-function-pattern-extend', '(:?^tt$|test_function$)']
    )
    assert result.out_lines == []
