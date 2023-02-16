import typing

TException = typing.TypeVar('TException', bound=Exception)


def with_context(
        exc: TException,
        context: typing.Mapping[typing.Text, typing.Any],
) -> TException:
    """
    Attaches a context dict to an exception, so that it can be captured by
    loggers.

    This lets you keep the exception message fairly short/generic, while making
    useful troubleshooting information accessible to debuggers and loggers.

    Example:

    .. code-block:: python

       raise with_context(
         ValueError('Failed validation.'),

         context = {
            'errors': filter_runner.get_context(True),
         },
       )
    """
    if not hasattr(exc, 'context'):
        exc.context = {}

    if not isinstance(exc.context, typing.MutableMapping):
        exc.context = {'_context': exc.context}

    exc.context.update(context)

    return exc
