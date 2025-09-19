import typing
from abc import abstractmethod
from datetime import datetime
from typing import Optional, Dict
import os
import sip

from osgeo import gdal
from qgis.core import (
    Qgis,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingAlgorithm,
    QgsTask,
    QgsApplication,
)
from qgis.PyQt.QtCore import Qt, QT_VERSION_STR, QTimer
from qgis.PyQt.QtCore import QObject, pyqtSignal
from qgis.PyQt.QtWidgets import QWidget
from qgis import gui, processing


from ..logging import local_context


class _RunSignals(QObject):
    finished = pyqtSignal(dict)  # results
    failed = pyqtSignal(Exception)  # error
    canceled = pyqtSignal()


class BaseAlgorithmDialog(gui.QgsProcessingAlgorithmDialogBase):
    def __init__(
        self,
        algorithm: QgsProcessingAlgorithm,
        parent: Optional[QWidget] = None,
        title: Optional[str] = None,
    ):
        super().__init__(
            parent,
            flags=Qt.WindowFlags(),
            mode=gui.QgsProcessingAlgorithmDialogBase.DialogMode.Single,
        )
        self.context = self.createContext()
        QTimer.singleShot(0, lambda: self.setAlgorithm(algorithm))
        self.setModal(True)
        self.setWindowTitle(title or algorithm.displayName())

        # Hook up layout
        self.panel = gui.QgsPanelWidget()
        layout = self.buildDialog()
        self.panel.setLayout(layout)
        self.setMainWidget(self.panel)

        # Don't destroy the dialog on close; we hide while tasks run
        try:
            self.setAttribute(Qt.WA_DeleteOnClose, False)
        except Exception:
            pass
        self._reopen_widget = None

        self.cancelButton().clicked.connect(self.reject)

    @abstractmethod
    def buildDialog(self) -> QWidget:
        """
        Build the dialog layout."
        """
        raise NotImplementedError("buildDialog() not implemented")

    @abstractmethod
    def getParameters(self) -> Dict:
        """
        Get the parameters from the dialog.
        """
        raise NotImplementedError("getParameters() not implemented")

    def processingContext(self) -> QgsProcessingContext:
        return self.context

    def createContext(self) -> QgsProcessingContext:
        return QgsProcessingContext()

    def createFeedback(self) -> QgsProcessingFeedback:
        return super().createFeedback()

    def runAlgorithm(self) -> None:
        """Run the algorithm asynchronously via QgsTask (with an optional sync fallback for tests)."""
        # Synchronous fallback for headless/unit tests
        if os.environ.get("EE_PLUGIN_SYNC_RUN") == "1":
            context = self.processingContext()
            feedback = self.createFeedback()
            feedback.setProgress(0)
            # Keep a handle so we can propagate UI cancel to processing feedback
            self._active_feedback = feedback
            self._cancel_requested = False
            local_context.set_feedback(feedback)

            params = self.getParameters()
            params = (
                self.transformParameters(params)
                if hasattr(self, "transformParameters")
                else params
            )

            # Environment/info logging (preserve existing behavior)
            self.pushDebugInfo(f"QGIS version: {Qgis.QGIS_VERSION}")
            self.pushDebugInfo(f"QGIS code revision: {Qgis.QGIS_DEV_VERSION}")
            self.pushDebugInfo(f"Qt version: {QT_VERSION_STR}")
            self.pushDebugInfo(f"GDAL version: {gdal.VersionInfo('--version')}")
            try:
                from shapely import geos

                self.pushInfo(f"GEOS version: {geos.geos_version_string}")
            except Exception:
                self.pushInfo("GEOS version: not available")
            self.pushCommandInfo(
                f"Algorithm started at: {datetime.now().isoformat(timespec='seconds')}"
            )
            self.pushCommandInfo(
                f"Algorithm '{self.algorithm().displayName()}' starting…"
            )
            self.pushCommandInfo("Input parameters:")
            for k, v in params.items():
                self.pushCommandInfo(f"  {k}: {v}")

            # Switch to the Log tab as soon as the run begins so users see progress
            try:
                self.showLog()
            except Exception:
                pass

            try:
                if hasattr(self, "beforeRun"):
                    self.beforeRun(params)
                results = processing.run(
                    self.algorithm(), params, context=context, feedback=feedback
                )
                self.setResults(results)
                if hasattr(self, "afterRun"):
                    self.afterRun(results)
            except Exception as e:
                # Centralized progress reset on failure
                try:
                    if feedback:
                        feedback.setProgress(0)
                except Exception:
                    pass
                if hasattr(self, "onError"):
                    self.onError(e)
                self.pushInfo(f"Algorithm failed: {e}")
            finally:
                self.showLog()
            return

        # Asynchronous path using QgsTask
        # Keep a strong reference while running to avoid premature deletion
        self._keepalive = self
        context = self.processingContext()
        feedback = self.createFeedback()
        # Force a UI repaint so the progress bar visibly resets before the task starts
        try:
            QgsApplication.processEvents()
        except Exception:
            pass

        # Keep a handle so we can propagate UI cancel to processing feedback
        self._active_feedback = feedback
        self._cancel_requested = False
        local_context.set_feedback(feedback)

        params = self.getParameters()
        params = (
            self.transformParameters(params)
            if hasattr(self, "transformParameters")
            else params
        )

        # Environment/info logging (preserve existing behavior)
        self.pushDebugInfo(f"QGIS version: {Qgis.QGIS_VERSION}")
        self.pushDebugInfo(f"QGIS code revision: {Qgis.QGIS_DEV_VERSION}")
        self.pushDebugInfo(f"Qt version: {QT_VERSION_STR}")
        self.pushDebugInfo(f"GDAL version: {gdal.VersionInfo('--version')}")
        try:
            from shapely import geos

            self.pushInfo(f"GEOS version: {geos.geos_version_string}")
        except Exception:
            self.pushInfo("GEOS version: not available")
        self.pushCommandInfo(
            f"Algorithm started at: {datetime.now().isoformat(timespec='seconds')}"
        )
        self.pushCommandInfo(f"Algorithm '{self.algorithm().displayName()}' starting…")
        self.pushCommandInfo("Input parameters:")
        for k, v in params.items():
            self.pushCommandInfo(f"  {k}: {v}")

        self.pushInfo("Queued task…")
        # Switch to the Log tab immediately so progress/messages are visible
        self.showLog()

        if hasattr(self, "beforeRun"):
            self.beforeRun(params)

        alg = self.algorithm()
        signals = _RunSignals()

        def _on_finished(results: dict):
            # If dialog object got deleted, bail out safely
            try:
                if sip.isdeleted(self):
                    return
            except Exception:
                pass
            try:
                self.setResults(results)
                try:
                    after = getattr(self, "afterRun", None)
                except RuntimeError:
                    return
                if callable(after):
                    after(results)
                try:
                    self.showLog()
                except Exception:
                    pass
            finally:
                self._teardown_task_ui()

        def _on_failed(exc: Exception):
            # If dialog object got deleted, bail out safely
            try:
                if sip.isdeleted(self):
                    return
            except Exception:
                pass
            try:
                # Centralized progress reset on failure
                try:
                    fb = getattr(self, "_active_feedback", None)
                    if fb:
                        fb.setProgress(0)
                except Exception:
                    pass
                try:
                    on_err = getattr(self, "onError", None)
                except RuntimeError:
                    return
                if callable(on_err):
                    on_err(exc)
                self.pushInfo(f"Algorithm failed: {exc}")
                try:
                    self.showLog()
                except Exception:
                    pass
            finally:
                self._teardown_task_ui()

        def _on_canceled():
            # If dialog object got deleted, bail out safely
            try:
                if sip.isdeleted(self):
                    return
            except Exception:
                pass
            try:
                # Centralized progress reset on cancel
                try:
                    fb = getattr(self, "_active_feedback", None)
                    if fb:
                        fb.setProgress(0)
                except Exception:
                    pass
                self.pushInfo("Algorithm canceled by user.")
                try:
                    self.showLog()
                except Exception:
                    pass
            finally:
                self._teardown_task_ui()

        signals.finished.connect(_on_finished)
        signals.failed.connect(_on_failed)
        signals.canceled.connect(_on_canceled)

        class _ProcTask(QgsTask):
            def __init__(self, description, alg, params, context, feedback, signals):
                super().__init__(description, QgsTask.CanCancel)
                self._alg = alg
                self._params = params
                self._context = context
                self._feedback = feedback
                self._signals = signals
                self._results = None
                self._exc = None

            def run(self):
                if self.isCanceled() or self._feedback.isCanceled():
                    return False
                try:
                    # small progress pulse so the bar moves
                    if self.isCanceled() or self._feedback.isCanceled():
                        return False
                    res = processing.run(
                        self._alg,
                        self._params,
                        context=self._context,
                        feedback=self._feedback,
                    )
                    if self.isCanceled():
                        return False
                    self._results = res
                    # near-complete pulse
                    return True
                except Exception as e:
                    self._exc = e
                    return False

            def finished(self, ok):
                # This runs on the main thread
                if self.isCanceled():
                    self._signals.canceled.emit()
                elif ok:
                    self._signals.finished.emit(self._results or {})
                else:
                    self._signals.failed.emit(self._exc or Exception("Unknown error"))

        self._current_task = _ProcTask(
            description=f"Run {alg.displayName()}",
            alg=alg,
            params=params,
            context=context,
            feedback=feedback,
            signals=signals,
        )

        # Keep Close enabled; only repurpose Cancel to stop the task
        if self.cancelButton():
            try:
                self.cancelButton().clicked.disconnect()
            except Exception:
                pass
            self.cancelButton().clicked.connect(self._cancel_task)
            self.cancelButton().setEnabled(True)
        # Optionally disable the Run/OK button if present, but do NOT disable Close
        try:
            if hasattr(self, "buttonBox") and self.buttonBox():
                from qgis.PyQt.QtWidgets import QDialogButtonBox

                bb = self.buttonBox()
                run_btn = (
                    bb.button(QDialogButtonBox.Ok) if hasattr(bb, "button") else None
                )
                if run_btn:
                    run_btn.setEnabled(False)
        except Exception:
            pass

        QgsApplication.taskManager().addTask(self._current_task)

    def _task_body(
        self,
        task: QgsTask,
        alg: QgsProcessingAlgorithm,
        params: Dict,
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> Dict:
        try:
            results = processing.run(alg, params, context=context, feedback=feedback)
            if task.isCanceled():
                raise RuntimeError("Canceled")
            return results
        except Exception as e:
            # Re-raise to be handled by on_failed
            raise e

    def _cancel_task(self):
        task = getattr(self, "_current_task", None)
        self._cancel_requested = True
        # Try to cancel the feedback first so inner loops can stop
        fb = getattr(self, "_active_feedback", None)
        try:
            if fb:
                fb.cancel()
        except Exception:
            pass
        # Give algorithm-specific dialogs a chance to cancel remote jobs (e.g., EE export)
        try:
            if hasattr(self, "onCancelRequested"):
                self.onCancelRequested()
        except Exception:
            # best-effort; do not crash the UI
            pass
        if not task:
            return
        try:
            task.cancel()
            self.pushInfo("Cancel requested…")
        except RuntimeError:
            # Task object may already be finalized/deleted by QGIS; restore UI.
            self._teardown_task_ui()

    def _teardown_task_ui(self):
        # If dialog object got deleted, bail out safely
        try:
            if sip.isdeleted(self):
                return
        except Exception:
            pass
        try:
            # Accessing QWidget API can raise RuntimeError if underlying C++ is gone
            _ = self.cancelButton
        except RuntimeError:
            return
        # Ensure progress is reset after finish/cancel/failure
        try:
            fb = getattr(self, "_active_feedback", None)
            if fb:
                fb.setProgress(0)
        except Exception:
            pass
        self._active_feedback = None
        self._current_task = None
        # Restore default cancel behavior
        try:
            if self.cancelButton():
                try:
                    self.cancelButton().clicked.disconnect()
                except Exception:
                    pass
                self.cancelButton().clicked.connect(self.reject)
        except RuntimeError:
            return
        # Re-enable Run/OK button; Close remains enabled already
        try:
            if hasattr(self, "buttonBox") and self.buttonBox():
                from qgis.PyQt.QtWidgets import QDialogButtonBox

                bb = self.buttonBox()
                run_btn = (
                    bb.button(QDialogButtonBox.Ok) if hasattr(bb, "button") else None
                )
                if run_btn:
                    run_btn.setEnabled(True)
        except Exception:
            pass
        try:
            if self._reopen_widget:
                self._reopen_widget.close()
                self._reopen_widget = None
        except Exception:
            pass
        try:
            self._keepalive = None
        except Exception:
            pass

    def closeEvent(self, event):
        """If a task is running, hide instead of closing to keep signals/objects alive."""
        task = getattr(self, "_current_task", None)
        try:
            running = bool(task) and not task.isCanceled()
        except Exception:
            running = bool(task)
        if running:
            # Do not destroy the dialog while the background task is active
            self.pushInfo(
                "Task is running in background. Closing the window will not stop it."
            )
            event.ignore()
            try:
                self._post_reopen_message()
            except Exception:
                pass
            self.hide()
            return
        super().closeEvent(event)

    def reject(self):
        task = getattr(self, "_current_task", None)
        try:
            running = bool(task) and not task.isCanceled()
        except Exception:
            running = bool(task)
        if running:
            # mirror closeEvent behavior
            self.pushInfo(
                "Task is running in background. Closing the window will not stop it."
            )
            try:
                self._post_reopen_message()
            except Exception:
                pass
            self.hide()
            return
        super().reject()

    def _post_reopen_message(self):
        try:
            from qgis.utils import iface
            from qgis.PyQt.QtWidgets import QPushButton
        except Exception:
            return
        try:
            if self._reopen_widget:
                # already posted
                return
            bar = iface.messageBar()
            msg = bar.createMessage(
                "Earth Engine Export", "Task running in background."
            )
            btn = QPushButton("Show")

            def _show_again():
                try:
                    if not sip.isdeleted(self):
                        self.show()
                        self.raise_()
                        self.activateWindow()
                except Exception:
                    pass
                # close the message once shown
                try:
                    if self._reopen_widget:
                        self._reopen_widget.close()
                        self._reopen_widget = None
                except Exception:
                    pass

            btn.clicked.connect(_show_again)
            msg.layout().addWidget(btn)
            bar.pushWidget(msg, Qgis.Info)
            self._reopen_widget = msg
        except Exception:
            pass

    def createProcessingParameters(self, flags) -> typing.Dict[str, typing.Any]:
        # TODO: We are currently unable to copy parameters from the algorithm to the dialog.
        #   See: https://github.com/gee-community/qgis-earthengine-plugin/issues/251
        return {}
