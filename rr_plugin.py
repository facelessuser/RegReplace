import sublime
import imp
import sys
import warnings
# import traceback
from os.path import join, normpath


class Plugin(object):
    loaded = []

    @classmethod
    def purge(cls):
        cls.loaded = []

    @classmethod
    def get_module(cls, module_name, path_name):
        module = None
        try:
            module = sys.modules[module_name]
        except:
            module = cls.load_module(module_name, path_name)
        return module

    @classmethod
    def load_module(cls, module_name, path_name):
        with warnings.catch_warnings(record=True) as w:
            # Ignore warnings about plugin folder not being a python package
            warnings.simplefilter("always")
            module = imp.new_module(module_name)
            sys.modules[module_name] = module
            source = None
            with open(path_name) as f:
                source = f.read().replace('\r', '')
            cls.__execute_module(source, module_name)
            w = filter(lambda i: issubclass(i.category, UserWarning), w)
        return module

    @classmethod
    def __execute_module(cls, source, module_name):
        exec(compile(source, module_name, 'exec'), sys.modules[module_name].__dict__)

    @classmethod
    def load(cls, module_name, loaded=None):
        if module_name.startswith("rr_modules."):
            path_name = join(sublime.packages_path(), "RegReplace", normpath(module_name.replace('.', '/')))
        else:
            path_name = join(sublime.packages_path(), normpath(module_name.replace('.', '/')))
        path_name += ".py"
        module = None
        if module_name in cls.loaded:
            module = cls.get_module(module_name, path_name)
        else:
            module = cls.load_module(module_name, path_name)
        return module

    @classmethod
    def load_from(cls, module_name, attribute):
        return getattr(cls.load_module(module_name), attribute)
