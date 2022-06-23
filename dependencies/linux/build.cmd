docker build . -t qgis-ee-ubuntu
docker run qgis-ee-ubuntu --name qgis-ee-ubuntu-container
docker cp qgis-ee-ubuntu-container:/tmp/qgis-earthengine-plugin/ee_plugin.zip .
