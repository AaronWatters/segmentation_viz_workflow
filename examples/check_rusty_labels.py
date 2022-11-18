
"""
This script launches a lineage editor/viewer using data configured like awatters's laptop.
"""

from segmentation_viz_workflow import lineage_forest
#from segmentation_viz_workflow import images_gizmos
#from H5Gizmos import serve
import json

fn = "Combined.json"
json_ob = json.load(open(fn))
F = lineage_forest.make_forest_from_haydens_json_graph(json_ob)

trivialize = False

if trivialize:
    F.use_trivial_null_loaders()
else:
    #assert trivialize, "non-trivial implementation is not finished."
    #img_folder = "/Users/awatters/test/mouse_embryo_images/"
    #image_pattern = img_folder + "klbOut_Cam_Long_%(ordinal)05d.crop.klb"
    #label_pattern = img_folder + "klbOut_Cam_Long_%(ordinal)05d.crop_cp_masks.klb"
    label_pattern = "/mnt/home/awatters/ceph/220827_stack1/Segmentation/stack_1_channel_0_obj_left/cropped/klbOut_Cam_Long_%(ordinal)05d.crop_cp_masks.klb"
    image_pattern = "/mnt/home/awatters/ceph/220827_stack1/Segmentation/stack_1_channel_0_obj_left/membrane/cropped/klbOut_Cam_Long_%(ordinal)05d.crop.klb"
    F.load_klb_using_file_patterns(
            image_pattern=image_pattern,
            label_pattern=label_pattern,
        )
    test_ordinal = 29
    #img = F.load_image_for_timestamp(test_ordinal)
    #assert img is not None, "Could not load image for: " + repr(test_ordinal)
    #lab = F.load_labels_for_timestamp(test_ordinal)
    #assert lab is not None, "Could not load image for: " + repr(test_ordinal)
print()
print("CHECKING LABELS")
print()

import cProfile

cProfile.run("F.check_labels()")
