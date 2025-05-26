import inspect
from typing import Callable

from qgis.PyQt.QtWidgets import QDialog
from .widget_parsers import get_dialog_values


from qgis.core import (
    QgsGradientColorRamp,
    QgsColorBrewerColorRamp,
    QgsLimitedRandomColorRamp,
    QgsPresetSchemeColorRamp,
    QgsCptCityColorRamp,
)


def call_func_with_values(func: Callable, dialog: QDialog):
    """
    Call a function with values from a dialog. Prior to the call, the function signature
    is inspected and used to filter out any values from the dialog that are not expected
    by the function.
    """
    func_signature = inspect.signature(func)
    func_kwargs = set(func_signature.parameters.keys())
    dialog_values = get_dialog_values(dialog)
    kwargs = {k: v for k, v in dialog_values.items() if k in func_kwargs}
    return func(**kwargs)


def serialize_color_ramp(viz_params):
    result = {}
    k = "palette"
    if "palette" in viz_params:
        v = viz_params[k]
        if isinstance(v, QgsGradientColorRamp):
            result[k] = [stop.color.name() for stop in v.stops()]
        elif isinstance(v, QgsColorBrewerColorRamp):
            result[k] = [v.color(i).name() for i in range(v.count())]
        elif isinstance(v, QgsLimitedRandomColorRamp):
            result[k] = [v.color(i).name() for i in range(v.count())]
        elif isinstance(v, QgsPresetSchemeColorRamp):
            result[k] = [c.name() for c in v.colors()]
        elif isinstance(v, QgsCptCityColorRamp):
            result[k] = [c.name() for c in v.colors()]
        else:
            result[k] = []
    else:
        result[k] = []
    return result
