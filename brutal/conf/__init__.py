import importlib
import os
from brutal.conf import global_config

ENV_VAR = 'BRUTAL_CONFIG_MODULE'

# big ups to django for the config design
class LazyConfig(object):
    def __init__(self):
        self._config = None

    def __getattr__(self, item):
        if self._config is None:
            self._build()
        if item == '__members__':
            return self._config.get_all_members()
        return getattr(self._config, item)

    def __setattr__(self, key, value):
        if key == '_config':
            self.__dict__['_config'] = value
        else:
            if self._config is None:
                self._build()
            setattr(self._config, key, value)

    def configure(self, default_config=global_config, **options):
        if self._config is not None:
            raise RuntimeError, 'config already setup'
        user_config = UserConfig(default_config)
        for key, value in options.items():
            setattr(user_config, key, value)
        self._config = user_config

    def _build(self):
        try:
            config_module = os.environ[ENV_VAR]
            if not config_module:
                raise KeyError
        except KeyError:
            raise ImportError, 'no config defined.'

        self._config = BrutalConfig(config_module)

class BrutalConfig(object):
    def __init__(self, config_module):

        for setting in dir(global_config):
            if setting == setting.upper():
                setattr(self, setting, getattr(global_config, setting))

        self.CONFIG_MODULE = config_module

        try:
            config = importlib.import_module(self.CONFIG_MODULE)
        except ImportError, e:
            raise ImportError, '{0} module cannot be found in sys.path'.format(self.CONFIG_MODULE)

        for setting in dir(config):
            if setting == setting.upper():
                setattr(self, setting, getattr(config, setting))

        INSTALLED_PLUGINS = getattr(self, 'INSTALLED_PLUGINS', [])
        self.PLUGINS = []
        for plugin in INSTALLED_PLUGINS:
            try:
                module = importlib.import_module(plugin)
            except ImportError, e:
                raise ImportError,'"{0} module cannot be found in sys.path'.format(plugin)
            else:
                self.PLUGINS.append(module)

    def get_all_members(self):
        return dir(self)

class UserConfig(object):
    CONFIG = None

    def __init__(self, default_config):
        self.default_config = default_config

    def __getattr__(self, item):
        return getattr(self.default_config, item)

    def get_all_members(self):
        return dir(self) + dir(self.default_config)


config = LazyConfig()