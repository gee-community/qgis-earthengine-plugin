import inspect
from typing import Callable

from qgis.PyQt.QtWidgets import QDialog
from .widget_parsers import get_dialog_values


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
