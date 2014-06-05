from RegReplace.rr_plugin import Plugin
import traceback


def run(text, chain=[]):
    for c in chain:
        module_name = c.get("plugin", None)
        if module_name is not None:
            try:
                module = Plugin.load(module_name)
            except:
                print(str(traceback.format_exc()))
        if module is not None:
            text = module.run(text, c.get("args", {}))
    return text
