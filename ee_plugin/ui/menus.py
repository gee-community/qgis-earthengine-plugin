from dataclasses import dataclass, field
from typing import Optional, List, Union
from PyQt5.QtWidgets import QMenu, QAction


MenuItem = Union["Separator", "SubMenu", "Action"]


@dataclass
class Separator:
    """A separator in a menu."""

    ...


@dataclass
class SubMenu:
    """A submenu in a menu."""

    label: Optional[str] = None
    subitems: Optional[List[MenuItem]] = field(default_factory=list)


@dataclass
class Action:
    """An action in a menu."""

    action: Optional[QAction] = None


def populate_menu(*, menu: QMenu, items: List[MenuItem]):
    """Populate a QMenu with the given list of MenuItem objects."""
    for item in items:
        if isinstance(item, Separator):
            menu.addSeparator()
        elif isinstance(item, SubMenu):
            sub_menu = menu.addMenu(item.label or "")
            populate_menu(menu=sub_menu, items=item.subitems)
        elif isinstance(item, Action):
            menu.addAction(item.action)
