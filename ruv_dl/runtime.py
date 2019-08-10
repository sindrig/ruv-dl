class SettingsContainer:
    __writable__ = False

    dryrun = False

    def __enter__(self):
        self.__writable__ = True

    def __exit__(self, *args, **kwargs):
        self.__writable__ = False

    def __setattr__(self, key, value):
        if key != '__writable__':
            if not hasattr(self, key):
                raise AttributeError(f'Unknown settings key: {key}')
            if not self.__writable__:
                raise RuntimeError(
                    f'Settings not writable unless inside context manager'
                )
            if not isinstance(value, type(getattr(self, key))):
                raise TypeError(
                    f'Settings key {key} currently has type '
                    f'{type(getattr(self, key))} but you passed in '
                    f'{value} which is {type(value)}'
                )
        super().__setattr__(key, value)


settings = SettingsContainer()
