
"""
Displays for labels and images
"""

import numpy as np
from H5Gizmos import Stack, Slider, Image, Shelf, Button, Text, RangeSlider
from array_gizmos import colorizers, operations3d


class CompareTimeStamps:
    """
    Show image and labels for 2 time stamps.
    """

    def __init__(self, forest, side, title="Timeslices"):
        self.forest = forest
        self.side = side
        self.title = title
        # gizmo scaffolding
        self.title_area = Text(self.title)
        self.info_area = Text("Building scaffolding.")
        self.parent_display = ImageAndLabels2d(side, None)
        self.child_display = ImageAndLabels2d(side, None)
        self.displays = Stack([ 
            self.title_area,
            self.parent_display.gizmo,
            self.child_display.gizmo,
            self.info_area,
        ])
        sliders = self.get_sliders(side)
        self.gizmo = Shelf([ 
            self.displays,
            sliders,
        ])
        # array shape (maxima)
        self.slicing = None
        self.theta = 0
        self.phi = 0

    def get_sliders(self, side):
        limit = np.pi
        self.theta_slider = Slider(
            title="theta", 
            orientation="vertical",
            value=0, 
            minimum=-limit, 
            maximum=+limit, 
            step=0.02, 
            on_change=self.project_and_display)
        self.theta_slider.resize(height=side)
        self.phi_slider = Slider(
            title="theta", 
            orientation="vertical",
            value=0, 
            minimum=-limit, 
            maximum=+limit, 
            step=0.02, 
            on_change=self.project_and_display)
        self.phi_slider.resize(height=side)
        # dummy values for now
        I = 100
        self.I_slider = RangeSlider(
            orientation="vertical",
            minimum=0,
            maximum=I,
            low_value=0,
            high_value=I,
            step=1,
            title="I slider",
            on_change=self.project_and_display,
        )
        self.I_slider.resize(height=side)
        self.J_slider = RangeSlider(
            orientation="vertical",
            minimum=0,
            maximum=I,
            low_value=0,
            high_value=I,
            step=1,
            title="K slider",
            on_change=self.project_and_display,
        )
        self.J_slider.resize(height=side)
        self.K_slider = RangeSlider(
            orientation="vertical",
            minimum=0,
            maximum=I,
            low_value=0,
            high_value=I,
            step=1,
            title="K slider",
            on_change=self.project_and_display,
        )
        self.K_slider.resize(height=side)
        return [
            [
                ["ϕ", self.phi_slider],
                ["θ", self.theta_slider]
            ],
            [ 
                ["I", self.I_slider],
                ["J", self.J_slider],
                ["K", self.K_slider],
            ]
        ]

    def configure_gizmo(self):
        self.parent_display.configure_gizmo()
        self.child_display.configure_gizmo()
        self.gizmo.css({"background-color": "#ddd"})

    def set_parent_timestamp(self, ordinal):
        ts = self.forest.ordinal_to_timestamp.get(ordinal)
        if ts is None:
            self.info_area.text("No such parent timestamp ordinal: " + repr(ordinal))
        else:
            self.parent_display.reset(ts, self.forest, self)

    def set_child_timestamp(self, ordinal):
        ts = self.forest.ordinal_to_timestamp.get(ordinal)
        if ts is None:
            self.info_area.text("No such child timestamp ordinal: " + repr(ordinal))
        else:
            self.child_display.reset(ts, self.forest, self)

    def project_and_display(self, *ignored):
        self.theta = self.theta_slider.value
        self.phi = self.phi_slider.value
        s = [
            self.I_slider.values,
            self.J_slider.values,
            self.K_slider.values,
        ]
        self.slicing = np.array(s, dtype=np.int)
        self.project2d()
        self.display_images()

    def project2d(self):
        self.parent_display.project2d(self)
        self.child_display.project2d(self)

    def display_images(self):
        self.parent_display.create_mask()
        self.child_display.create_mask()
        self.parent_display.load_mask(self.child_display)
        self.child_display.load_mask(self.parent_display)
        self.parent_display.display_images()
        self.child_display.display_images()

    def rotate_image(self, img):
        sl = self.slicing
        simg = img
        if sl is not None:
            simg = operations3d.slice3(img, sl)
        buffer = operations3d.rotation_buffer(simg)
        rbuffer = operations3d.rotate3d(buffer, self.theta, self.phi)
        return rbuffer

class ImageAndLabels2d:

    """
    Fixed rotation view of image and labels for a timestamp.
    """

    def __init__(self, side, timestamp=None):
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

    def reset(self, timestamp=None, forest=None, comparison=None):
        self.timestamp = timestamp
        #self.color_mapping_array = timestamp.color_mapping_array()
        self.img = None
        self.labels = None
        self.focus_mask = None
        self.focus_color = None
        self.focus_label = None
        self.compare_mask = None
        self.compare_color = None
        self.volume_shape = None
        self.label_volume = None
        self.image_volume = None
        self.volume_shape = None
        if comparison is not None:
            assert type(comparison) is CompareTimeStamps
        self.comparison = comparison
        if forest is not None and timestamp is not None:
            ordinal = timestamp.ordinal
            label_volume = forest.load_labels_for_timestamp(ordinal)
            if label_volume is None:
                msg = "Timestamp %s has no label data" % ordinal
                print(msg)
                self.info(msg)
            else:
                image_volume = forest.load_image_for_timestamp(ordinal)
                if image_volume is None:
                    msg = "Timestamp %s has no image data" % ordinal
                    print(msg)
                    self.info(msg)
                else:
                    self.info("Loaded timestamp " + repr(ordinal))
                    self.load_volumes(label_volume, image_volume)

    def load_volumes(self, label_volume, image_volume):
        l_s = label_volume.shape
        i_s = image_volume.shape
        assert l_s == i_s, "volume shapes don't match: " + repr([l_s, i_s])
        # need to fix this so slicing is unified across timestamps! xxxxx
        slicing = operations3d.positive_slicing(label_volume)
        self.label_volume = operations3d.slice3(label_volume, slicing)
        self.image_volume = operations3d.slice3(image_volume, slicing)
        self.volume_shape = self.label_volume.shape

    def project2d(self, comparison):
        rlabels = comparison.rotate_image(self.label_volume)
        rimage = comparison.rotate_image(self.image_volume)
        labels2d = operations3d.extrude0(rlabels)
        image2d = rimage.max(axis=0)  # maximum value projection.
        self.load_images(image2d, labels2d)

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
        node = None
        self.info("clicked label: %s for node %s" % (label, node))
        if label:
            node = self.timestamp.label_to_node[label]
            self.info("clicked label: %s for node %s" % (label, node))
            self.focus_label = label
            self.focus_color = node.color_array
        else:
            self.focus_label = None
            self.focus_color = None
        if self.comparison is not None:
            self.comparison.display_images()

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
        maxlabel = labels.max()
        color_mapping_array = self.timestamp.color_mapping_array(maxlabel)
        self.color_mapping_array = color_mapping_array # for debug
        labels = colorizers.colorize_array(labels, color_mapping_array)
        img = self.img
        fmask = self.focus_mask
        #cmask = self.compare_mask
        if fmask is not None:
            white = [255,255,255]
            labels = colorizers.overlay_color(labels, fmask, white)
        for (mask, color) in [
            (self.focus_mask, self.focus_color),
            (self.compare_mask, self.compare_color)]:
            if mask is not None:
                assert color is not None, "no color for mask?"
                #assert img.shape == mask.shape, "shapes don't match: " + repr([img.shape, mask.shape])
                img = colorizers.overlay_color(img, mask, color, center=True)
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
