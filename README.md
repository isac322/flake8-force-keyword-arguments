# flake8-force-keyword-arguments

[![PyPI](https://img.shields.io/pypi/v/flake8-force-keyword-arguments?label=pypi&logo=pypi&style=flat-square)](https://pypi.org/project/flake8-force-keyword-arguments/)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/flake8-force-keyword-arguments?style=flat-square&logo=pypi)](https://pypi.org/project/flake8-force-keyword-arguments/)
[![Python Version](https://img.shields.io/pypi/pyversions/flake8-force-keyword-arguments.svg?style=flat-square&logo=python)](https://pypi.org/project/flake8-force-keyword-arguments/)
[![PyPI - Implementation](https://img.shields.io/pypi/implementation/flake8-force-keyword-arguments?style=flat-square&logo=python)]((https://pypi.org/project/flake8-force-keyword-arguments/))
![Codecov](https://img.shields.io/codecov/c/gh/isac322/flake8-force-keyword-arguments?style=flat-square&logo=codecov)
![GitHub last commit (branch)](https://img.shields.io/github/last-commit/isac322/flake8-force-keyword-arguments/master?logo=github&style=flat-square)
![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/isac322/flake8-force-keyword-arguments/CI/master?logo=github&style=flat-square)
![Dependabot Status](https://flat.badgen.net/github/dependabot/isac322/flake8-force-keyword-arguments?icon=github)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)
___

A flake8 plugin that is looking for function calls and forces to use keyword arguments
if there are more than X (default=2) arguments.
And it can ignore positional only or variable arguments functions such as `setattr()` or `Logger.info()`.
The plugin inspects given modules (via `--kwargs-inspect-module`, `--kwargs-inspect-module-extend`)
to get signature and to determine whether it is positional only or variable arguments function.
The inspection runs only once at the start of the flake8 command and remembers ignore list through runtime.


## Installation

```
pip install flake8-force-keyword-arguments
```

## Usage

Run your `flake8` checker [as usual](http://flake8.pycqa.org/en/latest/user/invocation.html).

Example:

```bash
flake8 your_module.py
```

## Option

- `--kwargs-max-positional-arguments`: How many positional arguments are allowed (default: 2)
- `--kwargs-ignore-function-pattern`: Ignore pattern list (default: ('^logger.(:?log|debug|info|warning|error|exception|critical)$', '__setattr__$', '__delattr__$', '__getattr__$'))
- `--kwargs-ignore-function-pattern-extend`: Extend ignore pattern list.
- `--kwargs-inspect-module`: Inspect module level constructor of classes or functions to gather positional only callables and ignore it on lint. Note that methods are not subject to inspection. (default: ('builtins',))
- `--kwargs-inspect-module-extend`: Extend `--kwargs-inspect-module`
- `--kwargs-inspect-qualifier-option {only_name,only_with_qualifier,both}`: For detected positional only callables by inspection, option to append the qualifier or not. e.g. In case builtins.setattr(), `both` will register `builtins.setattr` and `setattr` as positional only function. `only_name` will register `setattr` and `only_with_qualifier` will register `builtins.setattr`. (default: QualifierOption.BOTH)

## Example

### code: `test.py`

```python
from functools import partial

def one_argument(one):
    pass

def two_arguments(one, two):
    pass

def pos_only_arguments(one, two, three, /):  # python 3.8 or higher required
    pass

def variable_arguments(*args):
    pass

variadic = lambda *args: None
curried = partial(variadic, 1)

one_argument(1)
one_argument(one=1)
two_arguments(1, 2)
two_arguments(one=1, two=2)
pos_only_arguments(1, 2, 3)
variadic(1, 2, 3)
curried(2, 3)
```

### Command

#### `flake8 test.py --select FKA1 --kwargs-inspect-module-extend test`

```
test.py:20:1: FKA100 two_arguments's call uses 2 positional arguments, use keyword arguments.
```

#### `flake8 test.py --select FKA1 --kwargs-inspect-module-extend test --kwargs-ignore-function-pattern-extend ^two_arguments$`

No error

#### `flake8 test.py --select FKA1`

```
test.py:16:11: FKA100 partial's call uses 2 positional arguments, use keyword arguments.
test.py:20:1: FKA100 two_arguments's call uses 2 positional arguments, use keyword arguments.
test.py:22:1: FKA100 pos_only_arguments's call uses 3 positional arguments, use keyword arguments.
test.py:23:1: FKA100 variadic's call uses 3 positional arguments, use keyword arguments.
test.py:24:1: FKA100 curried's call uses 2 positional arguments, use keyword arguments.
```

## Limitation

Currently it only inspects given modules and can not inspect (static, class or normal) methods.
Because inspection carries import, it is not safe to inspect all possible packages.
And method case, the plugin can inspect methods signature and also can determine whether it is positional only or not.
But it can not use the information on lint time.
Because python is a dynamic typed language and flake8 is basically a static analyzer.
That is, flake8 can not get type information of `logger.debug()`.
So even if I know that `logging.Logger::debug()` is a variadic function,
I can not assure that `logger` is a instance of `Logger`.

## Error codes

| Error code |                     Description                                |
|:----------:|:--------------------------------------------------------------:|
|   FKA100    | XXX's call uses N positional arguments, use keyword arguments. |
