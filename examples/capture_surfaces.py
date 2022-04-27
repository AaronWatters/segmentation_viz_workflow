
from segmentation_viz_workflow.csv_segmentation import Segmentation
from H5Gizmos import serve

lineage = 1
csv_file = "./stack_2_tree_cell_association.csv"
array_template = "./segmentation/%05d_rescaled_low_cp_masks.tif"
json_out_file = "surfaces.json"

S = Segmentation(csv_file, array_template)

async def task():
    await S.capture_surfaces_as_json(lineage, json_out_file, link=True)

serve(task())
