import functools
import inspect
from collections import defaultdict

PARAMETERS = defaultdict(defaultdict)
"""Global default dictionary holding a multi-level dictionary with the Autosubmit
parameters. At the first level we have the paramete groups.

  - ``JOB``

  - ``PLATFORM``
  
  - ``PROJECT``
  
Each entry in the ``PARAMETERS`` dictionary holds another default dictionary. Finally,
the lower level in the dictionary has a ``key=value`` where ``key`` is the parameter
name, and ``value`` the parameter documentation.

These values are used to create the Sphinx documentation for variables, as well as
to populate the comments in the Autosubmit YAML configuration files.
"""


def autosubmit_parameters(cls=None, /, *, parameters: dict):
    """Decorator for Autosubmit configuration parameters defined in a class.

    This is useful for parameters that are not defined in a single function or
    class (e.g. parameters that are created on-the-fly in functions)."""

    def wrap(cls):
        parameters = wrap.parameters

        for group, group_parameters in parameters.items():
            group = group.upper()

            if group not in PARAMETERS:
                PARAMETERS[group] = defaultdict(defaultdict)

            for parameter_name, parameter_value in group_parameters.items():
                if parameter_name not in PARAMETERS[group]:
                    PARAMETERS[group][parameter_name] = parameter_value.strip()

        return cls

    wrap.parameters = parameters

    if cls is None:
        return wrap

    return wrap(cls)


def autosubmit_parameter(func=None, *, name, group=None):
    """Decorator for Autosubmit configuration parameters.

    Used to annotate properties of classes

    Attributes:
        func (Callable): wrapped function.
        name (Union[str, List[str]]): parameter name.
        group (str): group name. Default to caller module name.
    """
    if group is None:
        stack = inspect.stack()
        group: str = stack[1][0].f_locals['__qualname__'].rsplit('.', 1)[-1]

    group = group.upper()

    if group not in PARAMETERS:
        PARAMETERS[group] = defaultdict(defaultdict)

    names = name
    if type(name) is not list:
        names = [name]

    for parameter_name in names:
        if parameter_name not in PARAMETERS[group]:
            PARAMETERS[group][parameter_name] = None

    def parameter_decorator(func):
        group = parameter_decorator.group
        names = parameter_decorator.names
        for name in names:
            if func.__doc__:
                PARAMETERS[group][name] = func.__doc__.strip().split('\n')[0]

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    parameter_decorator.group = group
    parameter_decorator.names = names

    return parameter_decorator
