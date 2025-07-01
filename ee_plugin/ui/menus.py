from dataclasses import dataclass, field
from typing import Optional, List, Callable
from PyQt5.QtWidgets import QMenu, QAction


MenuItem = Callable[[QMenu], None]


class Separator:
    """A separator in a menu."""

    def __call__(self, menu: QMenu):
        """Render the separator in the given QMenu."""
        menu.addSeparator()


@dataclass
class SubMenu:
    """A submenu in a menu."""

    label: Optional[str] = None
    subitems: Optional[List[MenuItem]] = field(default_factory=list)

    def __call__(self, menu: QMenu):
        """Render the submenu in the given QMenu."""
        sub_menu = menu.addMenu(self.label or "")
        populate_menu(menu=sub_menu, items=self.subitems)


@dataclass
class Action:
    """An action in a menu."""

    action: Optional[QAction] = None

    def __call__(self, menu: QMenu):
        """Render the action in the given QMenu."""
        menu.addAction(self.action)


def populate_menu(*, menu: QMenu, items: List[MenuItem]):
    """Populate a QMenu with the given list of MenuItem objects."""
    for item in items:
        item(menu)
