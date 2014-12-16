from threading import Thread


def async(f):
    """ This is our custom decorator for starting a function asynchronously in a separate thread.
    :param f: a function to be decorated
    :return: a wrapper
    """
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper
