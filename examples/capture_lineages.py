
from segmentation_viz_workflow.csv_segmentation import Segmentation
from H5Gizmos import serve

lineage_to_color = {
    1: [1,0,0],
    2: [0,1,0],
    3: [0,1,1],
}
csv_file = "./stack_2_tree_cell_association.csv"
array_template = "./segmentation/%05d_rescaled_low_cp_masks.tif"
json_out_file = "lineages.json"

S = Segmentation(csv_file, array_template)

async def task():
    await S.capture_lineages_as_json(lineage_to_color, json_out_file, link=True)

serve(task())
