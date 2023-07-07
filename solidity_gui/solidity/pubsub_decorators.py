"""Provides a decorator for catching and forwarding errors via pubsub."""
import logging
import traceback
from collections.abc import Callable
from typing import Any

from decorator import decorator
from pubsub import pub


def _error_occurred(error_topic: str, error: BaseException) -> None:
    """Signal that an error occurred."""
    traceback_str = "".join(traceback.format_tb(error.__traceback__))

    # Write details including stack trace to program log
    logging.error(f"Caught error ({error_topic}): {str(error)}\n\n{traceback_str}")

    # Notify listeners
    pub.sendMessage(error_topic, error=error)


def pubsub_broadcast(
    error_topic: str, success_topic: str, *return_value_names: str
) -> Callable:
    """Broadcast success or failure of function via pubsub.

    If the function returns without error, the returned values are sent as arguments to
    the success_topic message.

    Args:
        error_topic: The topic name on which to broadcast errors
        success_topic: The topic name on which to broadcast function result(s)
        return_value_names: The names of each of the returned values
    """

    def wrapped(func: Callable, *args: Any, **kwargs: Any) -> None:
        try:
            result = func(*args, **kwargs)
        except Exception as error:
            _error_occurred(error_topic, error)
        else:
            # Convert result to a tuple of the right size
            if result is None:
                result = ()
            elif not isinstance(result, tuple):
                result = (result,)

            # Make sure we have the right number of return values
            assert len(result) >= len(return_value_names)

            # Send message with arguments
            msg_kwargs = {name: res for name, res in zip(return_value_names, result)}
            pub.sendMessage(success_topic, **msg_kwargs)

    return decorator(wrapped)
