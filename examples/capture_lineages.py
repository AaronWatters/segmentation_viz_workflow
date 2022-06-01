
from segmentation_viz_workflow.csv_segmentation import Segmentation
from H5Gizmos import serve


# The lineage to color mapping specifies the color (using [0,1] floating point color coordinates).
# A color of None will track each cell of the lineage with individual arbitrary colors.

lineage_to_color = {
    1: [1,0,0],  # lineage 1 in red
    2: [0,1,0],  # lineage 2 in green
    3: [0,1,1],  # lineage 3 in cyan
}
csv_file = "./stack_2_tree_cell_association.csv"
array_template = "./segmentation/%05d_rescaled_low_cp_masks.tif"
json_out_file = "lineages.json"

S = Segmentation(csv_file, array_template)

async def task():
    await S.capture_lineages_as_json(lineage_to_color, json_out_file, link=True)

serve(task())
