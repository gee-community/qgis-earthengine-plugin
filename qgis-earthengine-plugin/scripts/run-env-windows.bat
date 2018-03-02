rem @echo off
                  

@echo off

SET OSGEO4W_ROOT=C:\OSGeo4W64\
call %OSGEO4W_ROOT%\bin\o4w_env.bat
call %OSGEO4W_ROOT%\apps\grass\grass-7.4.0\etc\env.bat

path %PATH%;%OSGEO4W_ROOT%\apps\qgis\bin
path %PATH%;%OSGEO4W_ROOT%\apps\grass\grass-7.4.0\lib
path %PATH%;%OSGEO4W_ROOT%\apps\Qt5\bin
path %PATH%;%OSGEO4W_ROOT%\apps\Python36\Scripts

set PYTHONPATH=%PYTHONPATH%;%OSGEO4W_ROOT%\apps\qgis\python
set PYTHONHOME=%OSGEO4W_ROOT%\apps\Python36

SET PYCHARM="C:\Program Files\JetBrains\PyCharm 2017.3.3\bin\pycharm.bat"

start "PyCharm aware of QGIS" /B %PYCHARM% %*  

