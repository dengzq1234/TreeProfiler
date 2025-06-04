from collections import OrderedDict, namedtuple
from math import pi
import random, string
from treeprofiler.src.utils import random_color, add_suffix
from .custom_faces import BoxFace

from ete4.smartview import Layout, TextFace, LegendFace

from ete4.smartview.faces import Face
import ete4.smartview.graphics as gr
from ete4.smartview.coordinates import Size, Box, make_box

from collections import  OrderedDict
from treeprofiler.src import utils 
from functools import lru_cache

#collapse in layout
#kingdom, phylum, class, order, family, genus, species, subspecies
DEFAULT_COLLAPSED_STYLE = {
    'shape': 'outline',
    #'stroke': '#0000FF',
    #'stroke-width': 1,
    'fill': '#303030',
    'opacity': 0.5,
}

@lru_cache(maxsize=5000)
def memoized_string_to_dict(s):
    return utils.string_to_dict(s)

def get_level(node, level=0):
    if node.is_root:
        return level
    else:
        return get_level(node.up, level + 1)

def summary(nodes):
    "Return a list of names summarizing the given list of nodes"
    return list(OrderedDict((first_name(node), None) for node in nodes).keys())

def first_name(tree):
    "Return the name of the first node that has a name"
    
    sci_names = []
    for node in tree.traverse('preorder'):
        if node.is_leaf:
            sci_name = node.props.get('sci_name')
            sci_names.append(sci_name)

    return next(iter(sci_names))

class TaxonClade(Layout):
    def __init__(self, name, level, rank, color_dict, active=True, legend=True):
        super().__init__(name, aligned_faces=True, active=active)

        # self.activate = False
        self.name = name
        self.column = level
        self.rank = rank
        self.color_dict = color_dict
        self.legend = legend

    def set_tree_style(self, tree, tree_style):
        super().set_tree_style(tree, tree_style)
        if self.legend:
            if self.color_dict:
                tree_style.add_legend(title=self.rank,
                                    variable='discrete',
                                    colormap=self.color_dict,
                                    )

    def set_node_style(self, node):
        named_lineage = node.props.get('named_lineage', None)

        if named_lineage:
            if isinstance(named_lineage, str):
                named_lineage = named_lineage.split('|')

            for clade, color in self.color_dict.items():
                if clade in named_lineage:
                    node.sm_style["hz_line_color"] = color
                    node.sm_style["hz_line_width"] = 2
                    node.sm_style["vt_line_color"] = color
                    node.sm_style["vt_line_width"] = 2
                    #node.sm_style["draw_descendants"] = False
                    node.sm_style["outline_color"] = color
                    break

        if not node.is_leaf:
            # Collapsed face
            if node.props.get('rank') == self.rank:
                if node.props.get('sci_name') is not None:
                    sci_name = node.props.get('sci_name')
                    color = self.color_dict.get(sci_name, 'gray')
                    node.add_face(TextFace(sci_name, padding_x=2, color = color),
                        position="branch_right", column=1, collapsed_only=True)
            
