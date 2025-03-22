import logging

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterString,
)

from ..ui.forms.add_ee_image import (
    form as AddEEImageDialog,
    callback as AddEEImageCallback,
)
from ..ui.forms.add_feature_collection import (
    form as AddFeatureCollectionDialog,
    callback as AddFeatureCollectionCallback,
)


logger = logging.getLogger(__name__)


class AddEEImageAlgorithm(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterString("image_id", "Image ID", optional=False)
        )
        pass

    def shortHelpString(self):
        return (
            "Loads a Google Earth Engine image into QGIS.\n\n"
            "Provide the Earth Engine Image ID and optional visualization parameters (as JSON) "
            "to display the image using Earth Engine's data directly in your map."
        )

    def processAlgorithm(self, parameters, context, feedback):
        form = AddEEImageDialog(accepted=AddEEImageCallback)
        form.exec_()

        # Call the existing callback with inputs
        layer = getattr(form, "added_layer", None)

        if not layer:
            logger.error("Failed to add EE layer.")
            raise QgsProcessingException("Failed to add EE layer.")

        return {"OUTPUT": layer.id()}

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


class AddFeatureCollectionAlgorithm(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):
        pass

    def processAlgorithm(self, parameters, context, feedback):
        form = AddFeatureCollectionDialog(accepted=AddFeatureCollectionCallback)
        form.exec_()

        return {}

    def name(self):
        return "add_feature_collection"

    def displayName(self):
        return "Add Feature Collection"

    def group(self):
        return "Add Layer"

    def groupId(self):
        return "gee"

    def createInstance(self):
        return AddFeatureCollectionAlgorithm()
