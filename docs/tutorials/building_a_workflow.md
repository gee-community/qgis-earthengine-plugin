---
title: Building a Workflow
---

# Building a Workflow

The processing algorithms provided by the Google Earth Engine plugin can be used in the QGIS Model Designer to automate workflows that combine data from the Earth Engine Data Catalog with processing algorithms from QGIS. 

In this tutorial, we will learn how to use a data layer of Cocoa Probability from Forest Data Partnership to calculate plot-level statistics of cocoa plantations. We will build a workflow to automate the following tasks to calculate the percentage of a farm plot covered with cocoa plantation.

1. Load the Forest Data Partnership [Cocoa Probability model 2025a](https://developers.google.com/earth-engine/datasets/catalog/projects_forestdatapartnership_assets_cocoa_model_2025a) layer.
2. Download the data for the region of interest.
3. Apply a threshold to select pixels with a high probability of cocoa.
4. Calculate the cocoa and total pixels within the plot.
5. Calculate the percentage of cocoa pixels in the plot.

![](../images/workflow_model.png)

This tutorial is aimed at demonstrating the use of the Google Earth Engine plugin in QGIS Model Designer. For a more comprehensive solution for compliance with deforestation-related regulations using QGIS, please check the [Whisp analysis QGIS plugin](https://github.com/forestdatapartnership/whisp-plugin).

## Datasets

Visit the [Forest Data Partnership](https://developers.google.com/earth-engine/datasets/publisher/forestdatapartnership) page in the Earth Engine Data Catalog. Select the [Cocoa Probability model 2025a](https://developers.google.com/earth-engine/datasets/catalog/projects_forestdatapartnership_assets_cocoa_model_2025a) dataset. 

![](../images/workflow_data1.png)

Note the Image Collection ID `projects/forestdatapartnership/assets/cocoa/model_2025a`. We will use this in our model.

![](../images/workflow_data2.png)

For the plot polygon, we will use a single plot polygon in Ghana supplied as a GeoJSON file [`plot.geojson`](../data/plot.geojson). This plot is one of the test polygons from [WHISP](https://github.com/forestdatapartnership/whisp).

## Procedure

1. Open QGIS. From the QGIS Browser Panel, locate the downloaded `plot.geojso`n file and double-click to open it. This file contains a single polygon for a farm plot in Ghana. We will calculate the percentage of the plot that has cocoa plantations.

    ![](../images/workflow1.png)

2. To help us select a region of interest, it will be helpful to have a basemap. From the QGIS Browser Panel, locate the *XYZ Tiles → OpenStreetMap* layer and drag it to the canvas.

    ![](../images/workflow2.png)

3. Open the Processing Toolbox from *Processing → Toolbox*. From the toolbar, select *Models → Create New Model..*

    ![](../images/workflow3.png)

4. In the Model Designer dialog, enter the model Name as `Calculate Cocoa Percentage` and click *Save model* button. When prompted to enter the file name, enter `calculate_cocoa_percentage.model3`.

    ![](../images/workflow4.png)

5. We will now start building the model. The first input to the model will be the layer with the plot polygon. From the Inputs tab, scroll down to find the *+ Vector* Layer input. Drag it to the canvas. In the *Vector Layer Parameter Definition* dialog, enter `Plot Polygons` as the *Description* and select `Polygon` as the *Geometry type*. Click OK. 

    ![](../images/workflow5.png)

6. Next, we will add another input for the user to select the extent of analysis. This is helpful if the input layer contains multiple polygons, but we want to restrict the analysis to a smaller region. Find the *+ Extent* parameter and drag it to the canvas. Enter `Analysis Extent` as the Description and click OK.

    ![](../images/workflow6.png)

7. Once the inputs are configured, let’s start building the workflow. First step is to load the dataset from Earth Engine. Switch to the *Algorithms* tab. Scroll down to the *Google Earth Engine* provider and locate the `Add Image Collection` algorithm. Drag it to the canvas.

    ![](../images/workflow7.png)

8. Enter the Earth Engine Image Collection ID for the Cocoa Probability model 2025a dataset `projects/forestdatapartnership/assets/cocoa/model_2025a`. For the *Extent*, switch to *Model Input* and select `Analysis Extent`. Fill the *Start date* and *End date* for filtering as `01-01-2023 00:00` and `01-01-2024 00:00`, respectively. The dataset is a single-band image of cocoa probability at each pixel with the range of values from 0 to 1. So enter the following *Visualization Parameter (JSON)* `{'min':0, 'max':1, 'palette': ['brown', 'white', 'green']}` which will be used to visualize the layer in a Brown-Green palette. Set the *Clip to extent* to `Yes` and click *OK*.

    ![](../images/workflow8.png)

9. The next step is to connect the *Export Image to GeoTIFF* algorithm. Locate it and drag it to the canvas.

    ![](../images/workflow9.png)

10. In the *Export Image to GeoTIFF* dialog box, for the *EE Image Name*, switch to *Using algorithm output* and select `"Layer Name"from algorithm "Add Image Collection"`. For *Extent*, switch to *Using model input* and select `Analysis Extent`. The spatial resolution of the dataset is 10m, so enter `10` as the *Scale (meters)*. Click OK.

    ![](../images/workflow10.png)

11. The previous step will download the data for the given extent as a GeoTIFF file. The pixel values of this image will be the probability values from 0 to 1. We can apply a threshold to select pixels with high probability of being cocoa. Search and locate the  *GDAL → Raster miscellaneous → Raster calculator* algorithm. Drag it to the canvas.

    ![](../images/workflow11.png)

    > Tip: The GDAL Raster Calculator algorithm is preferred over the native Raster Calculator in the Model Designer since it is easier to configure correctly.

12. In the Raster calculator dialog, change the *Description* to `Probability Thresholding`. For *Input layer A* switch to *Using algorithm output* and select `"Output File" from algorithm "Export Image to GeoTIFF"`. Since this is a one-band image, enter `1` as the *Number of raster band for A*. With this configuration, we can now write an expression using the variable **A** which will refer to the first band of the selected image.

    ![](../images/workflow12.png)

13. For the Calculation, enter the expression `A > 0.96`. According to the [model documentation](https://github.com/google/forest-data-partnership/tree/main/models), a threshold of *0.96* has precision and recall of ~87% for cocoa accuracy. The result of the expression will be a binary image. We can mask the 0 value pixels by specifying *Set output NoData value* as `0`. Click OK.

    ![](../images/workflow13.png)

14. We can now count the number of cocoa pixels within the plot polygons. For the next step, select the *Zonal statistics* algorithm and drag it to the canvas.

    ![](../images/workflow14.png)

15. We will be using the Zonal Statistics algorithm twice, so we can change the name to be more descriptive. Enter `Cocoa Count` as the *Description*. For the *Input layer*, switch to *Using model input* and select `Plot Polygons`. For the *Raster layer*, switch to *Using algorithm output* and select `"Calculated" from algorithm "Probability Thresholding"`. For the *Output column prefix*, enter `cocoa_`. We only need the count of pixels, so for *Statistics to calculate*, select only `Count`. Click *OK*.

    ![](../images/workflow15.png)

16. Having computed the number of cocoa pixels, we can now fill the masked values and count the total number of pixels. Locate the *Fill NoData cells* algorithm and drag it to the canvas.

    ![](../images/workflow16.png)

17. For the *Raster input*, switch to *Using algorithm output* and select `"Calculated" from algorithm "Probability Thresholding"`. Enter `1` as the *Fill value*.

    ![](../images/workflow17.png)

18. We now add one more Zonal Statistics step to calculate the total pixels. Select the *Zonal statistics* algorithm and drag it to the canvas.

    ![](../images/workflow18.png)

19. Change the *Description* to `Total Count`. For the *Input layer*, switch to *Using algorithm output* and select `"Zonal Statistics" from algorithm "Cocoa Count"`. For the *Raster layer*, switch to *Using algorithm output* and select `"Output raster" from algorithm "Fill NoData cells"`. This time, for the *Output column* prefix, use `total_`. Select only `Count` as the *Statistics to calculate*.

    ![](../images/workflow19.png)

20. The computed layer now has the count of both total and cocoa pixels within each plot. We can use the Field Calculator to calculate and add a new field with the percentage. Search and locate the *Field Calculator* algorithm and drag it to the canvas.

    ![](../images/workflow20.png)

21. Change the *Description* to `Percentage Calculation`. For the *Input layer*, switch to *Using algorithm output* and select `"Zonal Statistics" from algorithm "Total Count"`. Enter `percentage_cocoa` as the *Field name*. For the expression enter `100*("cocoa_count"/"total_count")`.

    ![](../images/workflow21.png)

22. This being our final result, we will add a layer name that will load the result in QGIS once the model has completed. Enter the name `output` for *Calculated*.

    ![](../images/workflow22.png)

23. The model is now complete. Click the *Run model* button.

    ![](../images/workflow23.png)

24. In the *Calculate Cocoa Percentage* dialog, set the *Analysis Extent*. You can zoom to the region around the plot of interest and select *Use Current Map Canvas Extent*. Select `plot` as the layer for *Plot Polygons*. For the *output*, browse to a folder on your computer and enter the name `plots_with_cocoa_percentage.gpkg`. Click *Run*.

    ![](../images/workflow24.png)

25. Once the model run completes, a new layer `plots_with_cocoa_percentage` will be added to the Layers panel. Open the attribute table and you will see new column with statistics computed from the cocoa probability dataset.

    ![](../images/workflow25.png)


The completed model can be downloaded as a model3 file from [`calculate_cocoa_percentage.model3`](../data/calculate_cocoa_percentage.model3). To open this model, go to *Models → Open Existing Model…* from the Processing Toolbox bar and browse to the downloaded model3 file.
