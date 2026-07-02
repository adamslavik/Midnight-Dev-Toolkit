from . import preferences
from . import operators
from . import panels
from . import properties
from . import tools


def register():
    preferences.register()
    properties.register()
    operators.register()
    tools.register()
    panels.register()


def unregister():
    panels.unregister()
    tools.unregister()
    operators.unregister()
    properties.unregister()
    preferences.unregister()
