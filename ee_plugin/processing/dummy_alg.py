from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterString,
    QgsProcessingOutputString,
)
from qgis.PyQt.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QPushButton, QDialog


class ReverseStringDialog(QDialog):
    def __init__(self, alg, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reverse String")
        self.alg = alg

        layout = QVBoxLayout(self)

        self.input_label = QLabel("Enter string:")
        self.input_field = QLineEdit()
        self.result_label = QLabel("")
        self.reverse_button = QPushButton("Reverse")

        layout.addWidget(self.input_label)
        layout.addWidget(self.input_field)
        layout.addWidget(self.reverse_button)
        layout.addWidget(self.result_label)

        self.reverse_button.clicked.connect(self.reverse_string)

    def reverse_string(self):
        text = self.input_field.text()
        self.result_label.setText(text[::-1])


class DummyReverseAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

    def name(self):
        return "reverse_dummy"

    def displayName(self):
        return "Dummy Reverse Algorithm"

    def group(self):
        return "Test"

    def groupId(self):
        return "test"

    def shortHelpString(self):
        return "Reverses a string using a dummy dialog"

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterString(self.INPUT, "Input String"))
        self.addOutput(QgsProcessingOutputString(self.OUTPUT, "Reversed Output"))

    def createInstance(self):
        return DummyReverseAlgorithm()

    def createCustomParametersWidget(self, parent=None):
        return ReverseStringDialog(self, parent)

    def processAlgorithm(self, parameters, context, feedback):
        input_text = parameters[self.INPUT]
        return {self.OUTPUT: input_text[::-1]}
