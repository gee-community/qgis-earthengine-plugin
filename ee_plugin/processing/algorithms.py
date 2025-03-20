from qgis.core import QgsProcessingAlgorithm

from ..ui.forms.add_ee_image import form as AddEEImageDialog


class AddEEImageAlgorithm(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):
        pass

    def processAlgorithm(self, parameters, context, feedback):
        form = AddEEImageDialog()
        form.exec_()
        # TODO: fetch the iface and add the layer

        return {}

    def name(self):
        return "add_ee_image"

    def displayName(self):
        return "Add EE Image"

    def group(self):
        return "Add Layer"

    def groupId(self):
        return "gee"

    def createInstance(self):
        return AddEEImageAlgorithm()
