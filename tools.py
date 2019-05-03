from datetime import timedelta
from time import time
from functools import wraps

def cache(duration=None, **kwargs):
    if duration is not None:
        assert not kwargs

    else:
        duration = timedelta(**kwargs)

    if isinstance(duration, timedelta):
        duration = duration.total_seconds()

    def wrapper(function):
        memo = {}

        @wraps(function)
        def wrapped(*args):
            try:
                memo_time, memo_rv = memo[args]
            except KeyError:
                pass
            else:
                if memo_time + duration > time():
                    print('Using cached value')
                    return memo_rv

            rv = function(*args)
            memo[args] = (time(), rv)
            return rv
        return wrapped
    return wrapper
