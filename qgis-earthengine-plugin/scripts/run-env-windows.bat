rem @echo off
SET OSGEO4W_ROOT="C:\OSGeo4W64\"

SET PYCHARM="C:\Program Files\JetBrains\PyCharm 2017.1.4\bin\pycharm.bat"

call "%OSGEO4W_ROOT%"\bin\o4w_env.bat  
call "%OSGEO4W_ROOT%"\apps\grass\grass-7.0.4\etc\env.bat  

rem @echo off

path %PATH%;%OSGEO4W_ROOT%\apps\qgis\bin  
path %PATH%;%OSGEO4W_ROOT%\apps\grass\grass-7.0.4\lib

set PYTHONPATH=%PYTHONPATH%;%OSGEO4W_ROOT%\apps\qgis\python  
set PYTHONPATH=%PYTHONPATH%;%OSGEO4W_ROOT%\apps\Python27\Lib\site-packages  
set QGIS_PREFIX_PATH=%OSGEO4W_ROOT%\apps\qgis


start "PyCharm aware of QGIS" /B %PYCHARM% %*  
