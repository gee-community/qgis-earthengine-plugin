"""Dock widget for browsing the Earth Engine catalog."""

import html
import webbrowser
from typing import List, Optional

from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDockWidget,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..processing.add_ee_image import AddEEImageAlgorithm, AddImageAlgorithmDialog
from ..processing.add_feature_collection import (
    AddFeatureCollectionAlgorithm,
    AddFeatureCollectionAlgorithmDialog,
)
from ..processing.add_image_collection import (
    AddImageCollectionAlgorithm,
    AddImageCollectionAlgorithmDialog,
)
from .client import CatalogItem, load_catalog, search_catalog


class CatalogLoadThread(QThread):
    finished = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, refresh: bool = False):
        super().__init__()
        self.refresh = refresh

    def run(self):
        try:
            self.finished.emit(load_catalog(refresh=self.refresh))
        except Exception as exc:
            self.failed.emit(str(exc))


class CatalogDockWidget(QDockWidget):
    """Dockable Earth Engine catalog browser."""

    def __init__(self, iface, parent=None):
        super().__init__("Earth Engine Catalog", parent)
        self.iface = iface
        self.items: List[CatalogItem] = []
        self.filtered_items: List[CatalogItem] = []
        self._loader: Optional[CatalogLoadThread] = None

        self.setObjectName("EarthEngineCatalogDock")
        self.setWidget(self._build_widget())
        self._set_loading_state("Catalog not loaded.")

    def showEvent(self, event):
        super().showEvent(event)
        if not self.items and self._loader is None:
            self.load_catalog()

    def _build_widget(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Search datasets, asset IDs, providers, tags"
        )
        self.type_combo = QComboBox()
        self.type_combo.addItems(
            ["All types", "Image", "ImageCollection", "FeatureCollection"]
        )
        self.refresh_button = QPushButton("Refresh")
        toolbar.addWidget(self.search_edit, 1)
        toolbar.addWidget(self.type_combo)
        toolbar.addWidget(self.refresh_button)
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Dataset", "Type", "Provider"])
        self.results_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.results_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        splitter.addWidget(self.results_table)

        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        self.details = QTextBrowser()
        self.details.setOpenExternalLinks(True)
        details_layout.addWidget(self.details)

        buttons = QHBoxLayout()
        self.load_button = QPushButton("Load")
        self.copy_button = QPushButton("Copy Asset ID")
        self.open_button = QPushButton("Open Dataset Page")
        buttons.addWidget(self.load_button)
        buttons.addWidget(self.copy_button)
        buttons.addWidget(self.open_button)
        details_layout.addLayout(buttons)
        splitter.addWidget(details_widget)
        splitter.setSizes([320, 220])
        layout.addWidget(splitter)

        self.search_edit.textChanged.connect(self.apply_filters)
        self.type_combo.currentTextChanged.connect(self.apply_filters)
        self.refresh_button.clicked.connect(lambda: self.load_catalog(refresh=True))
        self.results_table.itemSelectionChanged.connect(self._update_details)
        self.results_table.itemDoubleClicked.connect(
            lambda _: self.load_selected_item()
        )
        self.load_button.clicked.connect(self.load_selected_item)
        self.copy_button.clicked.connect(self.copy_selected_asset_id)
        self.open_button.clicked.connect(self.open_selected_dataset_page)

        return widget

    def load_catalog(self, refresh: bool = False) -> None:
        if self._loader is not None:
            return
        self._set_loading_state("Loading catalog...")
        self._loader = CatalogLoadThread(refresh=refresh)
        self._loader.finished.connect(self._catalog_loaded)
        self._loader.failed.connect(self._catalog_failed)
        self._loader.finished.connect(self._clear_loader)
        self._loader.failed.connect(self._clear_loader)
        self._loader.start()

    def apply_filters(self) -> None:
        asset_type = self.type_combo.currentText()
        if asset_type == "All types":
            asset_type = None
        self.filtered_items = search_catalog(
            self.items,
            query=self.search_edit.text(),
            asset_type=asset_type,
        )
        self._populate_results()

    def selected_item(self) -> Optional[CatalogItem]:
        selected_rows = self.results_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        if row >= len(self.filtered_items):
            return None
        return self.filtered_items[row]

    def load_selected_item(self) -> None:
        item = self.selected_item()
        if item is None:
            return

        if item.asset_type == "Image":
            dialog = AddImageAlgorithmDialog(
                AddEEImageAlgorithm(),
                parent=self.iface.mainWindow(),
                defaults={"IMAGE_ID": item.asset_id},
            )
        elif item.asset_type == "ImageCollection":
            dialog = AddImageCollectionAlgorithmDialog(
                AddImageCollectionAlgorithm(),
                parent=self.iface.mainWindow(),
                defaults={"image_collection_id": item.asset_id},
            )
        elif item.asset_type == "FeatureCollection":
            dialog = AddFeatureCollectionAlgorithmDialog(
                AddFeatureCollectionAlgorithm(),
                parent=self.iface.mainWindow(),
                defaults={"feature_collection_id": item.asset_id},
            )
        else:
            QMessageBox.warning(
                self,
                "Unsupported dataset type",
                f"Cannot load catalog item type: {item.asset_type}",
            )
            return
        dialog.exec()

    def copy_selected_asset_id(self) -> None:
        item = self.selected_item()
        if item is not None:
            QApplication.clipboard().setText(item.asset_id)

    def open_selected_dataset_page(self) -> None:
        item = self.selected_item()
        if item and item.url:
            webbrowser.open(item.url)

    def _catalog_loaded(self, items: list) -> None:
        self.items = items
        self.apply_filters()

    def _catalog_failed(self, error: str) -> None:
        self._set_loading_state(f"Could not load catalog:\n{error}")

    def _clear_loader(self) -> None:
        self._loader = None

    def _populate_results(self) -> None:
        self.results_table.setRowCount(len(self.filtered_items))
        for row, item in enumerate(self.filtered_items):
            for column, value in enumerate(
                [item.title, item.asset_type, item.provider]
            ):
                table_item = QTableWidgetItem(value)
                table_item.setData(Qt.ItemDataRole.UserRole, row)
                self.results_table.setItem(row, column, table_item)
        self.results_table.resizeColumnsToContents()
        self._update_details()

    def _update_details(self) -> None:
        item = self.selected_item()
        if item is None:
            self.details.setPlainText(
                f"{len(self.filtered_items)} dataset(s). Select a dataset to view details."
            )
            return

        self.details.setHtml(
            "<h3>{title}</h3>"
            "<p><b>Asset ID:</b> <code>{asset_id}</code></p>"
            "<p><b>Type:</b> {asset_type}<br>"
            "<b>Source:</b> {source}<br>"
            "<b>Provider:</b> {provider}<br>"
            "<b>Category:</b> {category}<br>"
            "<b>Date range:</b> {start_date} to {end_date}<br>"
            "<b>License:</b> {license}</p>"
            "<p><b>Keywords:</b> {keywords}</p>"
            "<p><a href='{url}'>{url}</a></p>".format(
                title=html.escape(item.title),
                asset_id=html.escape(item.asset_id),
                asset_type=html.escape(item.asset_type),
                source=html.escape(item.source),
                provider=html.escape(item.provider or "Unknown"),
                category=html.escape(item.category or "Unknown"),
                start_date=html.escape(item.start_date or "Unknown"),
                end_date=html.escape(item.end_date or "Unknown"),
                license=html.escape(item.license or "Unknown"),
                keywords=html.escape(", ".join(item.keywords) or "None"),
                url=html.escape(item.url or ""),
            )
        )

    def _set_loading_state(self, message: str) -> None:
        self.filtered_items = []
        self.results_table.setRowCount(0)
        self.details.setPlainText(message)
