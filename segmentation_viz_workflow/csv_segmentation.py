
import csv
from cv2 import line
from mouse_embryo_labeller import color_list, tools
from feedWebGL2 import surfaces_sequence
import numpy as np
import os
import json

class Segmentation:

    def __init__(
        self,
        csv_file_path,   # like stack_2_tree_cell_association.csv
        label_array_path_template,   # like "./segmentation/%05d_rescaled_low_cp_masks.tif"
        stride=2,   # subsample array stride to save some space
        ):
        self.csv_file_path = csv_file_path
        self.label_array_path_template = label_array_path_template
        self.stride = stride
        self.parse_csv()

    def parse_csv(self):
        fn = self.csv_file_path
        self.ts_cell_info_list = list(csv.DictReader(open(fn), skipinitialspace=True))
        self.branches = set(d["Branch"] for d in self.ts_cell_info_list)
        self.timestamps = sorted(set(int(d["Time"]) for d in self.ts_cell_info_list))
        float_colors = np.array(color_list.color_arrays) / 255.0
        self.branch_to_color = {b: float_colors[i] for (i, b) in enumerate(self.branches)}

    def color_dict(self, ts, lineage, color):
        "Mapping of label to color for timestamp and lineage."
        result = {}
        ts = int(ts)
        lineage = int(lineage)
        for d in self.ts_cell_info_list:
            if int(d["Lineage"]) == lineage and int(d["Time"]) == ts:
                b = d["Branch"]
                #ln = d["label_num"] wrong
                ln = int(d['Cell_Label'])
                if color is None:
                    result[ln] = self.branch_to_color[b].tolist()
                else:
                    result[ln] = list(color)
        return result

    def labels_array(self, ts):
        "Get subsampled label array for timestamp, or return None if no such file."
        ts = int(ts)
        file_path = self.label_array_path_template % (ts,)
        if not os.path.isfile(file_path):
            print ("WARNING: No file found for timestamp %s : %s" % (ts, file_path))
            return None
        s = self.stride
        A = tools.load_tiff_array(file_path)
        return A[::s, ::s, ::s]

    def label_dict(self, ts, lineage):
        "Dictionary of labels in lineage at a timestamp."
        result = {}
        ts = int(ts)
        lineage = int(lineage)
        for d in self.ts_cell_info_list:
            if int(d["Lineage"]) == lineage and int(d["Time"]) == ts:
                ln = int(d['Cell_Label'])
                result[ln] = ln
        return result

    async def capture_surfaces_as_json(
        self, 
        for_lineage, 
        to_json_path, 
        blur=0.7, 
        exit_when_done=True,
        link=False,
        ):
        """
        Capture surfaces for cells in a single lineage
        """
        return await self.capture_lineages_as_json(
            lineage_to_color={for_lineage: None},
            to_json_path=to_json_path,
            blur=blur,
            exit_when_done=exit_when_done,
            link=link,
        )

    async def capture_lineages_as_json(
        self, 
        lineage_to_color, 
        to_json_path, 
        blur=0.7, 
        exit_when_done=True,
        link=False,
        ):
        # sanity check
        colors = list(c for c in lineage_to_color.values() if c is not None)
        if colors:
            colors = np.array(colors)
            assert colors.min() >= 0, "colors must be non-negative " + repr(colors)
            assert colors.max() <= 1, "colors must be between 0 and 1 " + repr(colors)
            (nr, nc) = colors.shape
            assert nc == 3, "colors must be rgb between 0 and 1 " + repr(colors)
        SM = surfaces_sequence.SurfaceMaker(blur=blur, link=link)
        self.surface_maker = SM
        print("Using browser interface for capturing surface geometries.")
        count = 0
        for ts in self.timestamps:
            print()
            print("processing timestamp", ts)
            la = self.labels_array(ts)
            if la is None:
                print ("    WARNING:::: Stopping because label array was not found for ts", ts)
                break
            print("array", la.shape)
            all_cd = {}
            all_ld = {}
            for (lineage, color) in lineage_to_color.items():
                print("    lineage", (lineage, color))
                cd = self.color_dict(ts, lineage, color)
                all_cd.update(cd)
                ld = self.label_dict(ts, lineage)
                all_ld.update(ld)
            print("    labels", list(all_cd.items()))
            await SM.add_surfaces(la, all_ld, all_cd)
            count += 1
        assert count > 1, "No labels arrays found."
        print()
        print("Processed", count, "timestamps.  Saving JSON to", to_json_path)
        f = open(to_json_path, "w")
        json_ob = SM.sequence.json_repr()
        json.dump(json_ob, f)
        f.close()
        print ("wrote", repr(to_json_path))
        if exit_when_done:
            SM.V.shutdown()
        return SM

