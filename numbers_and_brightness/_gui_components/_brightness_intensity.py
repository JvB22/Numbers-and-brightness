# Imports
from pathlib import Path
import os

# External imports
import numpy as np
import pandas as pd
import tifffile
from scipy.stats import gaussian_kde
from cellpose import utils

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QComboBox,
    QPushButton, QHBoxLayout, QGridLayout, QFileDialog
)

from PyQt6.QtCore import pyqtSlot

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector
from mpl_toolkits.axes_grid1 import make_axes_locatable

# Package imports
from ._utils import show_error_message

class plot_widget(QWidget):
    def __init__(self, b_i_df, cellmask, brightness, intensity):
        super().__init__()

        self.b_i_df = b_i_df
        self.cellmask = cellmask
        self.brightness = brightness
        self.intensity = intensity

        main_layout = QVBoxLayout()

        # Figure
        self.scatter_figure = Figure(figsize=(10, 5), dpi=100)
        gs = self.scatter_figure.add_gridspec(1, 2)
        self.scatter_ax = self.scatter_figure.add_subplot(gs[0, 0])
        self.image_ax = self.scatter_figure.add_subplot(gs[0, 1])
        self.scatter_canvas = FigureCanvas(self.scatter_figure)
        self.scatter_toolbar = NavigationToolbar(self.scatter_canvas, self)

        # Plot layout
        scatter_layout = QVBoxLayout()
        scatter_layout.addWidget(self.scatter_toolbar)
        scatter_layout.addWidget(self.scatter_canvas)
        main_layout.addLayout(scatter_layout)

        # Background option menu
        self.combo = QComboBox()

        self.background_options = {
            "Apparent Brightness" : self.brightness,
            "Intensity" : self.intensity
        }

        self.combo.addItems(list(self.background_options.keys()))
        self.combo.currentTextChanged.connect(self.update_background)
        main_layout.addWidget(self.combo)
        self.setLayout(main_layout)

        # Set colors
        self.bg_color = self.palette().color(self.backgroundRole()).name()
        self.fg_color = "#949494"

        # Variables
        self.rect_coords = {'xmin': 0, 'xmax': 0, 'ymin': 0, 'ymax': 0}
        self.selected_points = []
        self.selected_background = list(self.background_options.keys())[0]

        # Create figures
        self.create_scatter_figure()
        self.create_image_figure()
        self.scatter_figure.tight_layout()

    def create_scatter_figure(self):        
        xy = np.vstack([self.b_i_df["Intensity"], self.b_i_df["Brightness"]])
        z = gaussian_kde(xy)(xy)
        self.scatter = self.scatter_ax.scatter(self.b_i_df["Intensity"], self.b_i_df["Brightness"], c=z, s=1, cmap='hsv_r')
        self.scatter_ax.set_title('Apparent Brightness - Intensity', color=self.fg_color)
        self.scatter_ax.set_xlabel('Intensity', color=self.fg_color)
        self.scatter_ax.set_ylabel('Apparent Brightness', color=self.fg_color)

        # Set colors
        self.scatter_figure.patch.set_facecolor(self.bg_color)
        self.scatter_ax.set_facecolor(self.bg_color)
        self.scatter_ax.tick_params(colors=self.fg_color)
        for spine in self.scatter_ax.spines.values():
            spine.set_color(self.fg_color)

        self.rect_selector = RectangleSelector(
            self.scatter_ax, self.onselect, useblit=True,
            button=[1],
            minspanx=5, minspany=5,
            spancoords='pixels',
            interactive=True,
            props=dict(facecolor='#52d9ff', edgecolor=self.fg_color, alpha=0.2, fill=True),
            drag_from_anywhere=True
        )

        self.scatter_canvas.draw()

    def onselect(self, eclick, erelease):
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata

        self.rect_coords['xmin'] = min(x1, x2)
        self.rect_coords['xmax'] = max(x1, x2)
        self.rect_coords['ymin'] = min(y1, y2)
        self.rect_coords['ymax'] = max(y1, y2)

        # update image
        self.create_image_figure()

    def create_image_figure(self):
        self.image_ax.clear()
        self.image_ax.set_title(self.selected_background, color=self.fg_color)

        # Calculate which pixels are in the selection
        intensity_mask = np.logical_and(self.intensity > self.rect_coords["xmin"], self.intensity < self.rect_coords["xmax"])
        brightness_mask = np.logical_and(self.brightness > self.rect_coords["ymin"], self.brightness < self.rect_coords["ymax"])

        combined_mask = np.logical_and(intensity_mask, brightness_mask)

        # Remove any values outside of cell
        temp_cellmask = self.cellmask>0
        combined_mask[np.logical_not(temp_cellmask)] = False

        combined_mask = np.ma.masked_where(combined_mask == 0, combined_mask)

        im = self.image_ax.imshow(self.background_options[self.selected_background], cmap='plasma')
        # Add colorbar
        if hasattr(self, 'cax') and self.cax in self.scatter_figure.axes:
            self.cax.remove()
        divider = make_axes_locatable(self.image_ax)
        self.cax = divider.append_axes("right", size="5%", pad=0.05)
        self.colorbar = self.scatter_figure.colorbar(im, cax=self.cax)
        self.colorbar.ax.tick_params(colors=self.fg_color)
        for spine in self.colorbar.ax.spines.values():
            spine.set_color(self.fg_color)

        # Show selection mask
        self.image_ax.imshow(combined_mask, cmap='summer', alpha=1)

        # Outline cellmask
        outlines = utils.outlines_list(self.cellmask)
        for o in outlines:
            self.image_ax.plot(o[:,0], o[:,1], color='r')

        # Set colors
        self.image_ax.set_facecolor(self.bg_color)
        self.image_ax.tick_params(colors=self.fg_color)
        for spine in self.image_ax.spines.values():
            spine.set_color(self.fg_color)

        self.scatter_canvas.draw()

    def update_background(self, text):
        self.selected_background=text
        self.create_image_figure()

class brightness_intensity_window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.b_i_df = None
        self.brightness = None
        self.cellmask = None
        self.intensity = None

        self.init_ui()


    def init_ui(self):
        self.setWindowTitle("Brightness - Intensity")

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.main_layout = QGridLayout(central_widget)

        # Select folder button
        self.folder_select_button = QPushButton("Select folder")
        self.folder_select_button.clicked.connect(self.get_folder)
        self.main_layout.addWidget(self.folder_select_button, 0, 0, 1, 2)

    @pyqtSlot()
    def init_graphs(self):
        plotwidget = plot_widget(b_i_df=self.b_i_df, cellmask=self.cellmask, brightness=self.brightness, intensity=self.intensity)
        self.main_layout.addWidget(plotwidget, 1, 0, 1, 1)

    @pyqtSlot()
    def get_folder(self):
        foldername = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not foldername:
            return
        
        foldername = Path(foldername)
        # Check if brightness-intensity csv file is present
        try:
            df_path = os.path.join(foldername, "brightness_intensity_values.csv")
            self.b_i_df = pd.read_csv(df_path)
        except:
            show_error_message(self, f"Could not open file: \"{df_path}\". Please make sure the file is still there.")
            return
        
        # Check if brightness.tif is present
        try:
            brightness_path = os.path.join(foldername, "apparent_brightness.tif")
            self.brightness = tifffile.imread(brightness_path)
        except:
            show_error_message(self, f"Could not open file: \"{brightness_path}\". Please make sure the file is still there.")
            return
        
        # Check if brightness.tif is present
        try:
            intensity_path = os.path.join(foldername, "intensity.tif")
            self.intensity = tifffile.imread(intensity_path)
        except:
            show_error_message(self, f"Could not open file: \"{intensity_path}\". Please make sure the file is still there.")
            return
        
        # Check if eroded mask is present, otherwise use non-eroded mask
        maskfile = "eroded_mask.npy" if os.path.isfile(os.path.join(foldername, "eroded_mask.npy")) else "cellmask.npy"
        try:
            cellmask_path = os.path.join(foldername, maskfile)
            self.cellmask = np.load(cellmask_path)
        except:
            show_error_message(self, f"Could not open file: \"{df_path}\". Please make sure the file is still there.")
            return

        self.folder = foldername
        self.folder_select_button.setText(foldername.name)
        self.setWindowTitle(f"Brightness - Intensity - {foldername.name}")

        self.init_graphs()