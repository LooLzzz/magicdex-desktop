class Singleton(type):
    _instances = {}
    def __call__(cls, *args, always_init=True, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        elif always_init:
            cls._instances[cls].__init__(*args, **kwargs)
        return cls._instances[cls]