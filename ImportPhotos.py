# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ImportPhotos
                                 A QGIS plugin
 Import photos jpegs
                              -------------------
        begin                : February 2018
        copyright            : (C) 2019 by KIOS Research Center
        email                : mariosmsk@gmail.com
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.PyQt.QtWidgets import (QAction, QFileDialog, QMessageBox)
from qgis.PyQt.QtGui import (QIcon)
from qgis.PyQt import (uic)
from qgis.PyQt.QtWidgets import (QDialog)
from qgis.PyQt.QtCore import (QSettings, QTranslator, qVersion, QCoreApplication, Qt, QVariant)
from qgis.core import (QgsRectangle, QgsVectorFileWriter, QgsCoordinateReferenceSystem, QgsVectorLayer,
    QgsLayerTreeLayer, QgsProject, QgsTask, QgsApplication, QgsMessageLog, QgsFields, QgsField,
    QgsWkbTypes, QgsFeature, QgsPointXY, QgsGeometry)
from qgis.utils import (Qgis)

# Initialize Qt resources from file resources.py
from . import resources
# Import the code for the dialog
from .code.MouseClick import MouseClick
import os
import platform
import json

import traceback

# Import python module
CHECK_MODULE = ''
try:
    from .import exif_exifread
    CHECK_MODULE = 'exifread'
except:
    pass

#try:
#    from qgis.utils import plugins
#    import sys
#    sys.path.append(':/plugins')
#    import processing
#except:
#    pass

try:
    if CHECK_MODULE == '':
        from . import exif_PIL
        CHECK_MODULE = 'PIL'
except:
    pass

#FORM_CLASS, _ = uic.loadUiType(os.path.join(
#    os.path.dirname(__file__), 'ui/impphotos.ui'))
from .ui.impphotos import Ui_photosImp

# Import ui file
#class ImportPhotosDialog(QDialog, FORM_CLASS):
class ImportPhotosDialog(QDialog, Ui_photosImp):

    def __init__(self, parent=None):
        # """Constructor."""
        QDialog.__init__(self, None, Qt.WindowStaysOnTopHint)
        super(ImportPhotosDialog, self).__init__(parent)
        self.setupUi(self)


class ImportPhotos:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'ImportPhotos_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr('&ImportPhotos')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(self.tr('ImportPhotos'))
        self.toolbar.setObjectName('ImportPhotos')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('ImportPhotos', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = ':/plugins/ImportPhotos/icons/ImportImage.svg'
        self.add_action(
            icon_path,
            text=self.tr('Import Photos'),
            callback=self.run,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/ImportPhotos/icons/SelectImage.svg'
        self.clickPhotos = self.add_action(
            icon_path,
            text=self.tr('Click Photos'),
            callback=self.mouseClick,
            parent=self.iface.mainWindow())

        self.dlg = ImportPhotosDialog()
        self.dlg.load_style_path.setPlaceholderText( "e.g." + os.path.join(self.plugin_dir, 'icons', "photos.qml"))
        self.dlg.ok.clicked.connect(self.ok)
        self.dlg.closebutton.clicked.connect(self.close)
        self.dlg.toolButtonImport.clicked.connect(self.toolButtonImport)
        self.dlg.toolButtonOut.clicked.connect(self.toolButtonOut)
        self.dlg.input_load_style.clicked.connect(self.loadstyle)

        self.clickPhotos.setCheckable(True)
        self.clickPhotos.setEnabled(True)

        self.listPhotos = []
        self.layernamePhotos = []
        self.canvas = self.iface.mapCanvas()
        self.toolMouseClick = MouseClick(self.canvas, self)

        self.fields = ['ID', 'Name', 'Date', 'Time', 'Lon', 'Lat', 'Altitude', 'North', 'Azimuth', 'Camera Maker',
                       'Camera Model', 'Title', 'Comment', 'Path', 'RelPath', 'Timestamp', 'Images']

        self.extension_switch = {
            ".gpkg": "GPKG",
            ".shp": "ESRI Shapefile",
            ".geojson": "GeoJSON",
            ".csv": "CSV",
            ".kml": "KML",
            ".tab": "MapInfo File"
        }

        self.extension_switch2 = {
            "GeoPackage (*.gpkg *.GPKG)": ".gpkg",
            "ESRI Shapefile (*.shp *.SHP)": ".shp",
            "GeoJSON (*.geojson *.GEOJSON)": ".geojson",
            "Comma Separated Value (*.csv *.CSV)": ".csv",
            "Keyhole Markup Language (*.kml *.KML)": ".kml",
            "Mapinfo TAB (*.tab *.TAB)": ".tab"
        }

    def mouseClick(self):
        try:
            self.iface.setActiveLayer(self.canvas.layers()[0])
        except:
            pass
        self.canvas.setMapTool(self.toolMouseClick)
        self.clickPhotos.setChecked(True)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr('&ImportPhotos'),
                action)
            self.iface.removeToolBarIcon(action)
            # remove the toolbar
        del self.toolbar

    def run(self):
        self.dlg.ok.setEnabled(True)
        self.dlg.closebutton.setEnabled(True)
        self.dlg.toolButtonImport.setEnabled(True)
        self.dlg.toolButtonOut.setEnabled(True)
        self.dlg.input_load_style.setEnabled(True)
        self.clickPhotos.setEnabled(True)
        self.dlg.out.setText('')
        self.dlg.imp.setText('')
        self.dlg.load_style_path.setText('')
        self.dlg.canvas_extent.setChecked(False)
        self.dlg.show()

    def close(self):
        self.dlg.close()

    def toolButtonOut(self):
        typefiles = 'GeoPackage (*.gpkg *.GPKG);; ESRI Shapefile (*.shp *.SHP);; GeoJSON (*.geojson *.GEOJSON);; Comma Separated Value (*.csv *.CSV);; Keyhole Markup Language (*.kml *.KML);; Mapinfo TAB (*.tab *.TAB)'

        outputPath, ext = QFileDialog.getSaveFileName(caption = self.tr('Save File'), filter = typefiles)

        if outputPath:
            if ('.' + outputPath.split('.')[-1]).lower() in self.extension_switch:
                self.outputPath = outputPath
            else:
                self.outputPath = outputPath + self.extension_switch2[ext]

            self.dlg.out.setText(self.outputPath)

    def toolButtonImport(self):
        self.directoryPhotos = QFileDialog.getExistingDirectory(caption = self.tr('Select a folder:'), options = QFileDialog.ShowDirsOnly)
        self.dlg.imp.setText(self.directoryPhotos)

    def loadstyle(self):
        self.load_style = QFileDialog.getOpenFileName(caption = self.tr('Load style'),
                                                      filter = "(*.qml)")
        if self.load_style[0] == "":
            return
        else:
            self.load_style = self.load_style[0]

        self.dlg.load_style_path.setText(self.load_style)

    def selectDir(self):
        title = 'Warning'
        msg = self.tr('Please select a directory photos.')
        self.showMessage(title, msg, 'Warning')
        return True

    def selectOutp(self):
        title = 'Warning'
        msg = self.tr('Please define output file location.')
        self.showMessage(title, msg, 'Warning')
        return True

    def noImageFound(self):
        title = 'Warning'
        msg = self.tr('No image path found.')
        self.showMessage(title, msg, 'Warning')
        return True

    def ok(self):
        if self.dlg.imp.text() == '':
            if self.selectDir():
                return
        if not os.path.isdir(self.dlg.imp.text()):
            if self.selectDir():
                return
        if self.dlg.out.text() == '':
            if self.selectOutp():
                return
        if not os.path.isabs(self.dlg.out.text()):
            if self.selectOutp():
                return

        self.outputPath = self.dlg.out.text()
        self.directoryPhotos = self.dlg.imp.text()

        self.selected_folder = self.directoryPhotos[:]
        self.selected_folder = './' + os.path.basename(os.path.normpath(self.selected_folder)) + '/'

        if self.dlg.input_load_style.text() == '':
            self.load_style = os.path.join(self.plugin_dir, 'icons', "photos.qml")
        else:
            self.load_style = self.dlg.load_style_path.text()

        if self.load_style != '':
            if not os.path.exists(self.load_style):
                title = 'Warning'
                msg = self.tr('No style path found.')
                self.showMessage(title, msg, 'Warning')
                return

        showMessageHide = True
        self.import_photos(self.directoryPhotos, self.outputPath, self.load_style, showMessageHide)

    def import_photos(self, directoryPhotos, outputPath, load_style, showMessageHide=True):

        if load_style == '':
            self.load_style = os.path.join(self.plugin_dir, 'icons', "photos.qml")
        else:
            self.load_style = load_style
        self.showMessageHide = showMessageHide
        self.outputPath = outputPath
        self.directoryPhotos = directoryPhotos

        if platform.system() == 'Linux':
            self.lphoto = os.path.basename(self.outputPath)
            self.extension = '.' + self.outputPath.split('.')[-1].lower()
        else:
            _ , self.extension = os.path.splitext(self.outputPath)
            basename = os.path.basename(self.outputPath)
            self.lphoto = basename[:-len(self.extension)]

        self.outDirectoryPhotosGeoJSON = os.path.join(self.plugin_dir, 'tmp.geojson')

        self.dlg.ok.setEnabled(False)
        self.dlg.closebutton.setEnabled(False)
        self.dlg.toolButtonImport.setEnabled(False)
        self.dlg.toolButtonOut.setEnabled(False)
        self.dlg.input_load_style.setEnabled(False)

        # get paths of photos
        extens = ['jpg', 'jpeg', 'JPG', 'JPEG']
        self.photos = []
        self.photos_names = []
        for root, dirs, files in os.walk(self.directoryPhotos):
            files.sort()
            for name in files:
                if name.lower().endswith(tuple(extens)):
                    self.photos.append(os.path.join(root, name))
                    self.photos_names.append(name)

        self.initphotos = len(self.photos)

        if self.initphotos == 0 and self.showMessageHide:
            title = self.tr('Warning')
            msg = self.tr('No photos.')
            self.showMessage(title, msg, 'Warning')
            self.dlg.ok.setEnabled(True)
            self.dlg.closebutton.setEnabled(True)
            self.dlg.toolButtonImport.setEnabled(True)
            self.dlg.toolButtonOut.setEnabled(True)
            self.dlg.input_load_style.setEnabled(True)
            self.clickPhotos.setChecked(True)
            return

        self.canvas.setMapTool(self.toolMouseClick)

        self.truePhotosCount = 0
        self.out_of_extent_photos = 0

        self.Qpr_inst = QgsProject.instance()
        if platform.system() == 'Darwin':
            self.layernamePhotos.append(self.lphoto+' OGRGeoJSON Point')
        else:
            self.layernamePhotos.append(self.lphoto)

        self.outputDriver = self.extension_switch[self.extension.lower()]

        self.exifread_module = False
        self.pil_module = False

        if CHECK_MODULE == '' and self.showMessageHide:
            self.showMessage('Python Modules', 'Please install python module "exifread" or "PIL".' , 'Warning')

        #self.import_photos_task('', '')
        self.call_import_photos()
        self.dlg.close()

    def refresh(self):  # Deselect features
        mc = self.canvas
        for layer in mc.layers():
            if layer.type() == layer.VectorLayer:
                layer.removeSelection()
        mc.refresh()

    def showMessage(self, title, msg, icon):
        if icon == 'Warning':
            icon = QMessageBox.Warning
        elif icon == 'Information':
            icon = QMessageBox.Information

        msgBox = QMessageBox()
        msgBox.setIcon(icon)
        msgBox.setWindowTitle(title)
        msgBox.setText(msg)
        msgBox.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)
        msgBox.exec_()

    def completed(self, exception, result=None):
        geojson = {"type": "FeatureCollection",
                   "name": self.lphoto,
                   "crs": {"type": "name", "properties": {"name": "crs:OGC:1.3:CRS84"}},
                   "features": self.geoPhotos}

        geofile = open(self.outDirectoryPhotosGeoJSON, 'w')
        json.dump(geojson, geofile)
        geofile.close()
        del self.geoPhotos, geojson

        try:
            for layer in self.canvas.layers():
                if layer.publicSource() == self.outputPath:
                    self.Qpr_inst.instance().removeMapLayer(layer.id())
                    os.remove(self.outputPath)
        except:
            pass

        self.layerPhotos = QgsVectorLayer(self.outDirectoryPhotosGeoJSON, self.lphoto, "ogr")
        QgsVectorFileWriter.writeAsVectorFormat(self.layerPhotos, self.outputPath, "utf-8",
                                                    QgsCoordinateReferenceSystem(self.layerPhotos.crs().authid()),
                                                    self.outputDriver)
        self.layerPhotos_final = QgsVectorLayer(self.outputPath, self.lphoto, "ogr")

        # clear temp.geojson file
        try:
            f = open(self.outDirectoryPhotosGeoJSON, 'r+')
            f.truncate(0)  # need '0' when using r+
        except:
            pass

        try:
            self.layerPhotos_final.loadNamedStyle(self.load_style)
        except:
            title = 'Warning'
            msg = self.tr('No geo-tagged images were detected.')
            self.showMessage(title, msg, 'Warning')
            self.taskPhotos.destroyed()
            return

        self.layerPhotos_final.setReadOnly(False)
        self.layerPhotos_final.reload()
        self.layerPhotos_final.triggerRepaint()

        try:
            xmin = min(self.lon)
            ymin = min(self.lat)
            xmax = max(self.lon)
            ymax = max(self.lat)
            self.canvas.zoomToSelected(self.layerPhotos_final)
            self.canvas.setExtent(QgsRectangle(xmin, ymin, xmax, ymax))
        except:
            pass

        ###########################################
        self.dlg.ok.setEnabled(True)
        self.dlg.closebutton.setEnabled(True)
        self.dlg.toolButtonImport.setEnabled(True)
        self.dlg.toolButtonOut.setEnabled(True)
        self.dlg.input_load_style.setEnabled(True)
        self.clickPhotos.setChecked(True)

        noLocationPhotosCounter = self.initphotos - self.truePhotosCount - self.out_of_extent_photos
        if (self.truePhotosCount == noLocationPhotosCounter == 0 or self.truePhotosCount == 0 ) and self.showMessageHide:
            title = self.tr('ImportPhotos')
            msg = '{}\n\n{}\n  {}'.format(
                self.tr('Import Completed.'),
                self.tr('Details:'),
                self.tr('No new photos were added.')
            )
            self.showMessage(title, msg, self.tr('Information'))
            self.taskPhotos.destroyed()
            return
        elif ((self.truePhotosCount == self.initphotos) or ((noLocationPhotosCounter + self.truePhotosCount + self.out_of_extent_photos) == self.initphotos) )and self.showMessageHide:
            title = self.tr('ImportPhotos')
            msg = '{}\n\n{}\n  {} {}\n  {} {}\n  {} {}\n'.format(
                self.tr('Import Completed.'),
                self.tr('Details:'),
                str(int(self.truePhotosCount)),
                self.tr('photo(s) added without error.'),
                str(int(noLocationPhotosCounter)),
                self.tr('photo(s) skipped (because of missing location).'),
                str(int(self.out_of_extent_photos)),
                self.tr('photo(s) skipped (because not in canvas extent).')
            )
            self.showMessage(title, msg, self.tr('Information'))

        #g = self.Qpr_inst.layerTreeRoot().insertGroup(0, self.lphoto)
        self.Qpr_inst.addMapLayer(self.layerPhotos_final)
        #nn = QgsLayerTreeLayer(self.layerPhotos_final)
        #g.insertChildNode(0, nn)

    def stopped(self, task):
        QgsMessageLog.logMessage(
            'Task "{name}" was canceled'.format(
                name=task.description()),
            'ImportPhotos', Qgis.Info)

    def import_photos_task(self, task, wait_time):
        self.geoPhotos = []
        self.lon = []
        self.lat = []
        for count, imgpath in enumerate(self.photos):
            try:
                RelPath = self.selected_folder + self.photos_names[count]
                ImagesSrc = '<img src = "' + RelPath + '" width="300" height="225"/>'

                self.taskPhotos.setProgress(count/self.initphotos)

                if CHECK_MODULE == 'exifread':
                    lon, lat, geo_info = exif_exifread.get_geo_info(imgpath, RelPath, ImagesSrc)

                if CHECK_MODULE == 'PIL':
                    lon, lat, geo_info = exif_PIL.get_geo_info(imgpath, RelPath, ImagesSrc)

                if self.dlg.canvas_extent.isChecked():
                    if not (self.canvas.extent().xMaximum() > lon > self.canvas.extent().xMinimum() \
                            and self.canvas.extent().yMaximum() > lat > self.canvas.extent().yMinimum()):
                        self.out_of_extent_photos = self.out_of_extent_photos + 1
                        continue

                self.lon.append(lon)
                self.lat.append(lat)

                self.truePhotosCount = self.truePhotosCount + 1

                self.geoPhotos.append(geo_info)

                if self.taskPhotos.isCanceled():
                    self.stopped(self.taskPhotos)
                    self.taskPhotos.destroyed()
                    return None
            except:
                traceback.print_exc()

        return True

    def call_import_photos(self):
        #self.import_photos_task('', '')
        #self.completed('', '')
        self.taskPhotos = QgsTask.fromFunction('ImportPhotos', self.import_photos_task,
                                 on_finished=self.completed, wait_time=4)
        QgsApplication.taskManager().addTask(self.taskPhotos)

