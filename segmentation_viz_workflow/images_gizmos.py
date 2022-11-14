
"""
Displays for labels and images
"""

from H5Gizmos import Stack, Slider, Image, Shelf, Button, Text, RangeSlider
from array_gizmos import colorizers


class compareTimeStamps:
    """
    Show image and labels for 2 time stamps.
    """

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
        self.image_display.change_array(img)
        self.labels_display.change_array(labels)
