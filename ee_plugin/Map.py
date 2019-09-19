import ee_plugin.utils

def addLayer(image, vis=None, name=None, visibility=None, opacity=None):
    if vis:
        image = image.visualize(**vis)
    if not name:
        name = 'untitled'

    if not opacity:
        opacity = 1.0
    
    ee_plugin.utils.add_or_update_ee_image_layer(image, name, visibility, opacity)
