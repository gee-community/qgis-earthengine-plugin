"""Dock widget for browsing the Earth Engine catalog."""

import html
import webbrowser
from typing import List, Optional

from qgis.PyQt.QtCore import Qt, QThread, QTimer, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDockWidget,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
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
from .client import (
    COMMUNITY_SOURCE,
    OFFICIAL_SOURCE,
    CatalogItem,
    load_catalog,
    load_community_catalog,
    search_catalog,
)

MAX_VISIBLE_RESULTS = 500


class CatalogLoadThread(QThread):
    finished = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, refresh: bool = False, community_only: bool = False):
        super().__init__()
        self.refresh = refresh
        self.community_only = community_only

    def run(self):
        try:
            if self.community_only:
                self.finished.emit(load_community_catalog(refresh=self.refresh))
            else:
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
        self._is_loading = False
        self._loaded_sources = set()
        self._pending_source = ""
        self._filter_timer = QTimer(self)
        self._filter_timer.setSingleShot(True)
        self._filter_timer.timeout.connect(self.apply_filters)

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

        filters = QGridLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Search datasets, asset IDs, providers, tags"
        )
        self.type_combo = QComboBox()
        self.type_combo.addItems(
            ["All types", "Image", "ImageCollection", "FeatureCollection"]
        )
        self.source_combo = QComboBox()
        self.source_combo.addItems(["Official", "Community", "All sources"])
        self.provider_combo = QComboBox()
        self.provider_combo.addItem("All providers")
        self.category_combo = QComboBox()
        self.category_combo.addItem("All categories")
        self.refresh_button = QPushButton("Refresh")
        self.clear_filters_button = QPushButton("Clear")

        filters.addWidget(self.search_edit, 0, 0, 1, 4)
        filters.addWidget(self.type_combo, 1, 0)
        filters.addWidget(self.source_combo, 1, 1)
        filters.addWidget(self.provider_combo, 1, 2)
        filters.addWidget(self.category_combo, 1, 3)
        filters.addWidget(self.refresh_button, 1, 4)
        filters.addWidget(self.clear_filters_button, 1, 5)
        filters.setColumnStretch(0, 1)
        filters.setColumnStretch(1, 1)
        filters.setColumnStretch(2, 1)
        layout.addLayout(filters)

        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.results_table = QTableWidget(0, 6)
        self.results_table.setHorizontalHeaderLabels(
            ["Dataset", "Type", "Source", "Provider", "Category", "Date range"]
        )
        self.results_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.results_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setSortingEnabled(True)
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
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

        self.search_edit.textChanged.connect(self._schedule_filter)
        self.type_combo.currentTextChanged.connect(self.apply_filters)
        self.source_combo.currentTextChanged.connect(self._on_source_filter_changed)
        self.provider_combo.currentTextChanged.connect(self.apply_filters)
        self.category_combo.currentTextChanged.connect(self.apply_filters)
        self.refresh_button.clicked.connect(self._refresh_current_source)
        self.clear_filters_button.clicked.connect(self.clear_filters)
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
        self._is_loading = True
        self._pending_source = OFFICIAL_SOURCE
        self._set_loading_state("Loading catalog...")
        self._set_controls_enabled(False)
        self._loader = CatalogLoadThread(refresh=refresh)
        self._loader.finished.connect(self._catalog_loaded)
        self._loader.failed.connect(self._catalog_failed)
        self._loader.finished.connect(self._clear_loader)
        self._loader.failed.connect(self._clear_loader)
        self._loader.start()

    def apply_filters(self) -> None:
        source = self._selected_source_filter()
        self.filtered_items = search_catalog(
            self.items,
            query=self.search_edit.text(),
            asset_type=self._combo_filter_value(self.type_combo, "All types"),
            source=source,
            provider=self._combo_filter_value(self.provider_combo, "All providers"),
            category=self._combo_filter_value(self.category_combo, "All categories"),
        )
        self._populate_results()

    def _schedule_filter(self) -> None:
        self._filter_timer.start(250)

    def clear_filters(self) -> None:
        self.search_edit.clear()
        self.type_combo.setCurrentIndex(0)
        self.source_combo.setCurrentText("Official")
        self.provider_combo.setCurrentIndex(0)
        self.category_combo.setCurrentIndex(0)

    def selected_item(self) -> Optional[CatalogItem]:
        selected_rows = self.results_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        first_item = self.results_table.item(row, 0)
        if first_item is None:
            return None
        item_index = first_item.data(Qt.ItemDataRole.UserRole)
        if (
            item_index is None
            or item_index < 0
            or item_index >= len(self.filtered_items)
        ):
            return None
        return self.filtered_items[item_index]

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
                defaults={
                    "image_collection_id": item.asset_id,
                    "start_date": item.start_date,
                    "end_date": item.end_date,
                },
            )
        elif item.asset_type == "FeatureCollection":
            dialog = AddFeatureCollectionAlgorithmDialog(
                AddFeatureCollectionAlgorithm(),
                parent=self.iface.mainWindow(),
                defaults={
                    "feature_collection_id": item.asset_id,
                    "start_date": item.start_date,
                    "end_date": item.end_date,
                },
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
        self._is_loading = False
        if self._pending_source == COMMUNITY_SOURCE:
            self.items = [
                item for item in self.items if item.source != COMMUNITY_SOURCE
            ] + items
        else:
            self.items = [
                item for item in self.items if item.source != OFFICIAL_SOURCE
            ] + items
        if self._pending_source:
            self._loaded_sources.add(self._pending_source)
        self._pending_source = ""
        self._refresh_filter_options()
        self._set_controls_enabled(True)
        self.apply_filters()

    def _catalog_failed(self, error: str) -> None:
        self._is_loading = False
        failed_source = self._pending_source
        self._pending_source = ""
        self._set_controls_enabled(True)
        if failed_source == COMMUNITY_SOURCE and self.items:
            self.apply_filters()
            self._update_status("Could not load community catalog.")
            return
        self._set_loading_state(f"Could not load catalog:\n{error}")

    def _clear_loader(self) -> None:
        self._loader = None

    def _populate_results(self) -> None:
        visible_items = self.filtered_items[:MAX_VISIBLE_RESULTS]
        self.results_table.setSortingEnabled(False)
        self.results_table.setUpdatesEnabled(False)
        self.results_table.clearSelection()
        self.results_table.setRowCount(len(visible_items))
        for row, item in enumerate(visible_items):
            date_range = self._date_range_label(item)
            values = [
                item.title,
                item.asset_type,
                item.source,
                item.provider or "Unknown",
                item.category or "Unknown",
                date_range,
            ]
            for column, value in enumerate(values):
                table_item = QTableWidgetItem(value)
                table_item.setData(Qt.ItemDataRole.UserRole, row)
                self.results_table.setItem(row, column, table_item)
        self.results_table.setUpdatesEnabled(True)
        self.results_table.setSortingEnabled(True)
        self._update_status()
        self._update_details()

    def _update_details(self) -> None:
        item = self.selected_item()
        if item is None:
            if self._is_loading:
                self.details.setPlainText("Loading catalog...")
            elif self.items and not self.filtered_items:
                self.details.setPlainText("No datasets match the current filters.")
            else:
                self.details.setPlainText("Select a dataset to view details.")
            self._update_action_buttons()
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
            "{links}".format(
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
                links=self._details_links_html(item),
            )
        )
        self._update_action_buttons()

    def _set_loading_state(self, message: str) -> None:
        self.filtered_items = []
        self.results_table.setRowCount(0)
        self.details.setPlainText(message)
        self._update_status(message)
        self._update_action_buttons()

    def _refresh_filter_options(self) -> None:
        self._set_combo_values(
            self.provider_combo,
            "All providers",
            sorted({item.provider for item in self.items if item.provider}),
        )
        self._set_combo_values(
            self.category_combo,
            "All categories",
            sorted({item.category for item in self.items if item.category}),
        )

    def _set_combo_values(
        self,
        combo: QComboBox,
        all_label: str,
        values: List[str],
    ) -> None:
        current = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(all_label)
        combo.addItems(values)
        if current in values:
            combo.setCurrentText(current)
        combo.blockSignals(False)

    def _combo_filter_value(self, combo: QComboBox, all_label: str) -> Optional[str]:
        value = combo.currentText()
        if value == all_label:
            return None
        return value

    def _selected_source_filter(self) -> Optional[str]:
        value = self.source_combo.currentText()
        if value == "Official":
            return OFFICIAL_SOURCE
        if value == "Community":
            return COMMUNITY_SOURCE
        return None

    def _on_source_filter_changed(self) -> None:
        source = self._selected_source_filter()
        if (
            source in (COMMUNITY_SOURCE, None)
            and COMMUNITY_SOURCE not in self._loaded_sources
        ):
            self._load_community_catalog()
            return
        self.apply_filters()

    def _load_community_catalog(self, refresh: bool = False) -> None:
        if self._loader is not None:
            return
        self._is_loading = True
        self._pending_source = COMMUNITY_SOURCE
        self._set_controls_enabled(False)
        self._update_status("Loading community catalog...")
        self._loader = CatalogLoadThread(refresh=refresh, community_only=True)
        self._loader.finished.connect(self._catalog_loaded)
        self._loader.failed.connect(self._catalog_failed)
        self._loader.finished.connect(self._clear_loader)
        self._loader.failed.connect(self._clear_loader)
        self._loader.start()

    def _refresh_current_source(self) -> None:
        if self.source_combo.currentText() == "Community":
            self._load_community_catalog(refresh=True)
        else:
            self.load_catalog(refresh=True)

    def _date_range_label(self, item: CatalogItem) -> str:
        if item.start_date and item.end_date:
            return f"{item.start_date} to {item.end_date}"
        if item.start_date:
            return f"{item.start_date} onward"
        if item.end_date:
            return f"Until {item.end_date}"
        return "Unknown"

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.search_edit.setEnabled(enabled)
        self.type_combo.setEnabled(enabled)
        self.source_combo.setEnabled(enabled)
        self.provider_combo.setEnabled(enabled)
        self.category_combo.setEnabled(enabled)
        self.clear_filters_button.setEnabled(enabled)
        self.refresh_button.setEnabled(enabled)

    def _update_status(self, message: Optional[str] = None) -> None:
        if message:
            self.status_label.setText(message)
            return
        total = len(self.items)
        filtered = len(self.filtered_items)
        if total == 0:
            self.status_label.setText("No catalog datasets loaded.")
        elif filtered > MAX_VISIBLE_RESULTS:
            self.status_label.setText(
                f"Showing first {MAX_VISIBLE_RESULTS} of {filtered} match(es)."
            )
        elif filtered == total:
            self.status_label.setText(f"Showing {total} dataset(s).")
        else:
            self.status_label.setText(f"Showing {filtered} of {total} dataset(s).")

    def _update_action_buttons(self) -> None:
        has_selection = self.selected_item() is not None
        self.load_button.setEnabled(has_selection)
        self.copy_button.setEnabled(has_selection)
        self.open_button.setEnabled(
            bool(has_selection and self.selected_item() and self.selected_item().url)
        )

    def _details_links_html(self, item: CatalogItem) -> str:
        links = []
        if item.url:
            escaped_url = html.escape(item.url)
            links.append(f"<a href='{escaped_url}'>Dataset page</a>")
        if item.sample_code_url:
            escaped_sample_url = html.escape(item.sample_code_url)
            links.append(f"<a href='{escaped_sample_url}'>Sample code</a>")
        if item.catalog_url:
            escaped_catalog_url = html.escape(item.catalog_url)
            links.append(f"<a href='{escaped_catalog_url}'>Catalog metadata</a>")
        if not links:
            return ""
        return "<p>{}</p>".format(" &nbsp; ".join(links))
