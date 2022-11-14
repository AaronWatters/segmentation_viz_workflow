
"""
Displays for labels and images
"""

import numpy as np
from H5Gizmos import Stack, Slider, Image, Shelf, Button, Text, RangeSlider
from array_gizmos import colorizers, operations3d


class compareTimeStamps:
    """
    Show image and labels for 2 time stamps.
    """

    def __init__(self, forest):
        self.forest = forest

class ImageAndLabels2d:

    """
    Fixed rotation view of image and labels for a timestamp.
    """

    def __init__(self, side, timestamp):
        self.side = side
        #self.timestamp = timestamp
        self.image_display = Image(height=side, width=side)
        self.labels_display = Image(height=side, width=side)
        displays = Shelf([
            self.image_display,
            self.labels_display,
        ])
        self.info_area = Text("Image and Labels")
        self.gizmo = Stack([
            self.info_area,
            displays,
        ])
        self.img_volume = None
        self.label_volume = None
        self.reset(timestamp)

    def reset(self, timestamp):
        self.timestamp = timestamp
        self.img = None
        self.labels = None
        self.focus_mask = None
        self.focus_color = None
        self.focus_label = None
        self.compare_mask = None
        self.compare_color = None

    def load_volumes(self, label_volume, image_volume):
        l_s = label_volume.shape
        i_s = image_volume.shape
        assert l_s == i_s, "volume shapes don't match: " + repr([l_s, i_s])
        slicing = operations3d.positive_slicing(label_volume)
        self.label_volume = operations3d.slice3(label_volume)
        self.image_volume = operations3d.slice3(image_volume)

    def info(self, text):
        self.info_area.text(text)

    def configure_gizmo(self):
        self.labels_display.on_pixel(self.pixel_callback)

    def pixel_callback(self, event):
        row = event["pixel_row"]
        column = event["pixel_column"]
        labels = self.labels
        if labels is None:
            self.info("No labels to select")
            return 
        label = labels[row, column]
        self.info("clicked label: " + repr(label))
        if label:
            node = self.timestamp.label_to_node[label]
            self.focus_label = label
            self.focus_color = node.color_array

    def create_mask(self):
        label = self.focus_label
        labels = self.labels
        if label is None or labels is None:
            self.focus_mask = None
            return
        node = self.timestamp.label_to_node[label]
        assert node.color_array is not None, "color not assigned to node: " + repr(node)
        self.focus_mask = colorizers.boundary_image(labels, label)
        self.focus_color = node.color_array

    def load_images(self, img, labels):
        img = colorizers.scale256(img)  # ???? xxxx
        img = colorizers.to_rgb(img, scaled=False)
        self.img = img
        self.labels = labels

    def load_mask(self, other):
        self.compare_mask = other.focus_mask
        self.compare_color = other.focus_color

    def display_images(self):
        #label = self.focus_label
        labels = self.labels
        labels = colorizers.colorize_array(labels)
        img = self.img
        fmask = self.focus_mask
        cmask = self.compare_mask
        if fmask is not None:
            white = [255,255,255]
            labels = colorizers.overlay_color(labels, fmask, white)
        for (mask, color) in [
            (self.focus_mask, self.focus_color),
            (self.compare_mask, self.compare_color)]:
            if mask is not None:
                assert color is not None, "no color for mask?"
                img = colorizers.overlay_color(img, mask, color)
        img = self.pad_image(img)
        labels = self.pad_image(labels)
        self.image_display.change_array(img)
        self.labels_display.change_array(labels)

    def pad_image(self, img):
        shape = img.shape
        (w, h) = img.shape[:2]
        if w == h:
            return img
        if w < h:
            padding = int((h - w) / 2)
            new_shape = list(shape)
            new_shape[:2] = [h, h]
            imgp = np.zeros(new_shape, dtype=img.dtype)
            imgp[padding: w+padding] = img
            return imgp
        else:
            assert w > h
            padding = int((w - h) / 2)
            new_shape = list(shape)
            new_shape[:2] = [w, w]
            imgp = np.zeros(new_shape, dtype=img.dtype)
            imgp[:, padding: h+padding] = img
            return imgp
