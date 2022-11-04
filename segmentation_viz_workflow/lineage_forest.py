
"""
OO structure for cell lineage tracking.
"""


from array_gizmos import color_list


class Node:

    "A cell in a timestamp."

    def __init__(self, node_id, timestamp_ordinal, label=None):
        self.node_id = node_id
        self.timestamp_ordinal = timestamp_ordinal
        self.label = label
        self.parent = None
        self.id_to_child = {}
        self.reset()

    def reset(self):
        self._track = None
        self._lineage_root = None
        self._width = None
        self._offset = None
        self._is_isolated = None  # not determined
        self.color = None

    def json_object(self):
        parent_id = None
        if self.parent is not None:
            parent_id = self.parent.node_id
        isolated = (self.parent is None) and (len(self.id_to_child) < 1)
        return dict(
            identity=self.node_id,
            timestamp_ordinal=self.timestamp_ordinal,
            label=self.label,
            color=self.color,
            offset=self._offset,
            parent_id=parent_id,
            isolated=isolated,
        )

    def same(self, other):
        return (
            (self.label == other.label) and
            (self.timestamp_ordinal == other.timestamp_ordinal) and
            (self.node_id == other.node_id)
        )

    def track_ancestor(self):
        if self._track is not None:
            return self._track
        parent = self.parent
        if parent is None:
            result = self
        elif len(parent.id_to_child) > 1:
            result = self
        else:
            result = self.parent.track_ancestor()
        self._track = result
        return result

    def lineage_ancestor(self):
        if self._lineage_root is not None:
            return self._lineage_root
        if self.parent is not None:
            result = self.parent.track_ancestor().lineage_ancestor()
        else:
            result = self
        self._lineage_root = result
        return result

    def __repr__(self):
        pid = None
        if self.parent is not None:
            pid = self.parent.node_id
        return "Node" + repr((self.node_id, self.timestamp_ordinal, self.label, pid))

    def set_parent(self, parent):
        assert type(parent) is Node, "bad parent type: " + repr([parent, type(parent)])
        assert self.timestamp_ordinal > parent.timestamp_ordinal, (
            "Bad Node parent: " + repr([self, parent])
        )
        self.parent = parent

    def set_child(self, child):
        assert type(child) is Node, "bad child type: " + repr([child, type(child)])
        i2c = self.id_to_child
        # should have no more than 2 children? xxxx
        child.set_parent(self)
        i2c[child.node_id] = child

    def children_ids(self):
        return sorted(self.id_to_child.keys())

    '''def width(self):
        if self._width is not None:
            return self._width
        result = 1
        for c in self.id_to_child.values():
            result += c.width()
        self._width = result
        return result'''

    '''def offset(self, starting_from):
        if self._offset is not None:
            return self._offset
        result = starting_from + 1
        child_ids = self.children_ids()
        if child_ids:
            first = self.id_to_child[child_ids[0]]
            result = starting_from + first.width + 1
        self._offset = result
        return result'''

    def assign_offsets(self, starting_from=0, cursor_ref=None):
        assert starting_from is not None
        if cursor_ref is None:
            cursor_ref = [starting_from]
        child_ids = self.children_ids()
        i2c = self.id_to_child
        nc = len(child_ids)
        if nc < 1:
            #result = starting_from # + 1
            self._offset = cursor_ref[0]
            # no increment
        else:
            first_id = child_ids[0]
            first = i2c[first_id]
            remainder = child_ids[1:]
            if nc == 1:
                first.assign_offsets(cursor_ref=cursor_ref)
                self._offset = first._offset
            else:
                assert nc > 1
                first.assign_offsets(cursor_ref=cursor_ref)
                cursor_ref[0] += 1
                #self._offset = cursor_ref[0]
                #cursor_ref[0] += 1
                for r_id in remainder:
                    r = i2c[r_id]
                    result = r.assign_offsets(cursor_ref=cursor_ref)
                self._offset = 0.5 * (first._offset + r._offset)
        return cursor_ref[0]

class NodeGroup:

    "Superclass for node collection."

    id_to_node = None

    def add_node(self, node):
        self.check_node(node)
        if self.id_to_node is None:
            self.id_to_node = {}
        self.id_to_node[node.node_id] = node

    def reset(self):
        pass # by default do nothing

    def isolated(self):
        return len(self.id_to_node) < 2

    def mark_isolated(self):
        test = self.isolated()
        for node in self.id_to_node.values():
            node._is_isolated = test

class TimeStamp(NodeGroup):

    "A time reference point."

    def __init__(self, ordinal):
        self.ordinal = ordinal

    def check_node(self, node):
        ord = self.ordinal
        assert ord == node.timestamp_ordinal, "node not in timestamp: " + repr([ord, node])

    def farthest_parent_ordinal(self):
        result = None
        for node in self.id_to_node.values():
            if node.parent is not None:
                ordinal = node.parent.timestamp_ordinal
                if (result is None) or (result > ordinal):
                    result = ordinal
        return result

    def json_object(self):
        return dict(
            ordinal=self.ordinal,
            node_id=sorted(self.id_to_node.keys())
        )

class Lineage(NodeGroup):

    "A group of tracks originating at a single ancestor cell."

    def __init__(self, root):
        self.root = root

    def check_node(self, node):
        node_root = node.lineage_ancestor()
        assert node_root is self.root, "wrong lineage: " + repr([node, node_root, self.root])

class Track(Lineage):

    "A collection of nodes representing the same cell over many time steps."

    def check_node(self, node):
        node_root = node.track_ancestor()
        assert node_root is self.root, "wrong track: " + repr([node, node_root, self.root])

class Forest:

    "A collection of lineages"

    def __init__(self):
        self.id_to_node = {}
        self.ordinal_to_timestamp = {}
        self.reset()

    def reset(self):
        for node in self.id_to_node.values():
            node.reset()
        for ts in self.ordinal_to_timestamp.values():
            ts.reset()
        self.id_to_lineage = None
        self.id_to_track = {}

    def assign_colors_to_lineages(self):
        return self.assign_colors_to_tracks(id_to_collection=self.id_to_lineage)

    def assign_colors_to_tracks(self, id_to_collection=None):
        if id_to_collection is None:
            id_to_collection = self.id_to_track
        for (index, identifier) in enumerate(sorted(id_to_collection.keys())):
            collection = id_to_collection[identifier]
            color = color_list.rgbhtml(color_list.indexed_color(index))
            for node in collection.id_to_node.values():
                node.color = color

    def find_tracks_and_lineages(self):
        self.reset()
        i2l = {}
        i2t = {}
        for node in self.id_to_node.values():
            tr = node.track_ancestor()
            ln = node.lineage_ancestor()
            #print(node, tr, ln)
            i2t[tr.node_id] = Track(tr)
            i2l[ln.node_id] = Lineage(ln)
        for node in self.id_to_node.values():
            tr = node.track_ancestor()
            ln = node.lineage_ancestor()
            i2t[tr.node_id].add_node(node)
            i2l[ln.node_id].add_node(node)
        self.id_to_lineage = i2l
        self.id_to_track = i2t

    def assign_offsets(self, start_at=0):
        i2l = self.id_to_lineage
        assert i2l is not None, "lineages must be assigned first."
        cursor = start_at
        # assign isolated lineages after all non-isolated
        for rootid in i2l.keys():
            # mark isolated nodes for downstream testing
            lineage = i2l[rootid]
            lineage.mark_isolated()
        isolated_roots = []
        for rootid in sorted(i2l.keys()):
            if lineage.isolated():
                isolated_roots.append(rootid)
            else:
                lineage = i2l[rootid]
                cursor = lineage.root.assign_offsets(cursor) + 1
        # set isolated offsets higher...
        for rootid in isolated_roots:
            lineage = i2l[rootid]
            cursor = lineage.root.assign_offsets(cursor) + 1

    def add_node(self, node_id, ordinal, label=None):
        i2n = self.id_to_node
        assert node_id not in i2n, "duplicate node added: " + repr([node_id, ordinal, label])
        ts = self.get_or_add_timestamp(ordinal)
        n = Node(node_id, ordinal, label)
        i2n[node_id] = n 
        ts.add_node(n)
        return n

    def get_or_add_timestamp(self, ordinal):
        i2t = self.ordinal_to_timestamp
        if ordinal in i2t:
            result = i2t[ordinal]
        else:
            result = i2t[ordinal] = TimeStamp(ordinal)
        return result

    def json_ob(self, exclude_isolated=True):
        (width, height) = self.dimensions()
        id_to_node = self.id_to_node
        if exclude_isolated:
            id_to_node = {ident: node for (ident, node) in self.id_to_node.items() if not node._is_isolated}
        id_to_node_json = {ident: node.json_object() for (ident, node) in id_to_node.items()}
        return dict(
            width=width,
            height=height,
            id_to_node=id_to_node_json,
        )

    def timestamp_region_json(self, ordinal):
        """
        Node info for nodes in timestamp, its predecessor and all directly connected ancestor timestamps.
        """
        # always include isolated nodes (?)
        o2t = self.ordinal_to_timestamp
        ordinals = set([ordinal])
        all_ordinals = sorted(o2t.keys())
        index = all_ordinals.index(ordinal)
        if index > 0:
            pred = all_ordinals[index - 1]
            # always add any pred timestamp
            ordinals.add(pred)
        ts = o2t[ordinal]
        farthest = ts.farthest_parent_ordinal()
        # also add directly connected older timestamps
        for ord in all_ordinals:
            if (ord <= ordinal) and (ord >= farthest):
                ordinals.add(ord)
        # dump nodes and adjust geometry
        id_to_node = {}
        for ord in ordinals:
            this_ts = o2t[ord]
            #print("updating", list(this_ts.id_to_node.keys()))
            id_to_node.update(this_ts.id_to_node)
        id_to_node_json = {}
        offsets = sorted(set(node._offset for node in id_to_node.values()))
        sordinals = sorted(ordinals)
        height = len(sordinals)
        for (id, node) in id_to_node.items():
            json_ob = node.json_object()
            # patch in relative geometry
            json_ob["x"] = offsets.index(node._offset)
            json_ob["y"] = height - sordinals.index(node.timestamp_ordinal) - 1
            id_to_node_json[id] = json_ob
        return dict(
            id_to_node=id_to_node_json,
            width=len(offsets),
            height=height,
            ordinals=sordinals,
        )

    def dimensions(self):
        # assuming timestamps start at 0 or 1
        height = max(self.ordinal_to_timestamp.keys()) + 1
        width = max(n._offset for n in self.id_to_node.values()) + 1
        return (width, height)

def make_forest_from_haydens_json_graph(json_graph):
    """
    Read a JSON dump of matlab graph similar to "Gata6Nanog1.json".
    Return a forest.
    """
    edges = json_graph['G_based_on_nn_combined']['Edges']
    result = Forest()
    all_ids = set()
    parent_map = {}
    for thing in edges:
        [parent_id, child_id] = thing["EndNodes"]
        all_ids.add(parent_id)
        all_ids.add(child_id)
        parent_map[child_id] = parent_id
    parsed_strings = {}
    timestamps = set()
    node_map = {}
    for s in all_ids:
        [ts_string, label_string] = s.split("_")
        parsed = (ts, label) = (int(ts_string), int(label_string))
        timestamps.add(ts)
        parsed_strings[s] = parsed
        n = result.add_node(s, ts, label)
        node_map[s] = n
    for (child_id, parent_id) in parent_map.items():
        child = node_map[child_id]
        parent = node_map[parent_id]
        parent.set_child(child)
    return result


