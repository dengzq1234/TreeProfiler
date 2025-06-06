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
DEFAULT_TREE_STYLE = {
    'collapsed': DEFAULT_COLLAPSED_STYLE,
}

TAXONOMIC_RANK_ORDER = [
    "no rank",  # for root if needed
    "superkingdom",
    "kingdom",
    "subkingdom",
    "superphylum",
    "phylum",
    "subphylum",
    "superclass",
    "class",
    "subclass",
    "infraclass",
    "cohort",
    "superorder",
    "order",
    "suborder",
    "infraorder",
    "parvorder",
    "superfamily",
    "family",
    "subfamily",
    "tribe",
    "subtribe",
    "genus",
    "subgenus",
    "species_group",
    "species_subgroup",
    "species",
    "subspecies",
    "varietas",
    "forma"
]

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

class TaxaClade(Layout):
    def __init__(self, name, level, rank, color_dict, active=True, legend=True):

        # self.activate = False
        self.name = name
        self.column = level
        self.rank = rank
        self.color_dict = color_dict
        self.legend = legend
        self.line_width = 2
        self.line_opacity = 0.8
        self.default_collapsed_style = DEFAULT_COLLAPSED_STYLE
        
        super().__init__(name=name,
                         draw_node=self.draw_node,
                         draw_tree=self.draw_tree,
                         active=active)

    def draw_tree(self, tree):
        # Provide collapsed node style
        yield {"collapsed": self.default_collapsed_style}
        if self.color_dict:
            colormap = self.color_dict
        else:
            colormap = {}
        
        yield LegendFace(title=self.rank,
            variable='discrete',
            colormap=colormap
            )

    def draw_node(self, node, collapsed):
        named_lineage = node.props.get('named_lineage', None)
        if named_lineage:
            if isinstance(named_lineage, str):
                named_lineage = named_lineage.split('|')

            for clade, color in self.color_dict.items():
                if clade in named_lineage:
                    line_style = {
                        "hz-line": {
                        "stroke": color,
                        "stroke-width": self.line_width,
                        "stroke-opacity": self.line_opacity,
                        }, 
                        "vt-line": {
                            "stroke": color,
                            "stroke-width": self.line_width,
                            "stroke-opacity": self.line_opacity,
                        }
                    }
                    yield line_style
                    if collapsed:
                        yield {
                            "collapsed": {
                                'shape': 'outline',
                                'stroke': color,
                                'stroke-width': self.line_width,
                                'fill': color,
                                'opacity': self.line_opacity,
                            }
                        }

class TaxaRectangular(Layout):
    def __init__(self, name="Last common ancestor", rank=None, color_dict={}, rect_width=20, column=0, padding_x=1, padding_y=0, legend=True, active=True):
        self.rank = rank
        self.color_dict = color_dict
        self.rect_width = rect_width
        self.column = column
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.active = active
        
        self.default_collapsed_style = DEFAULT_COLLAPSED_STYLE
        
        super().__init__(name=name,
                         draw_node=self.draw_node,
                         draw_tree=self.draw_tree,
                         active=active)

    def draw_tree(self, tree):
        # Provide collapsed node style
        yield {"collapsed": self.default_collapsed_style}
        if self.color_dict:
            colormap = self.color_dict
        else:
            colormap = {}
        
        yield LegendFace(title=self.rank,
            variable='discrete',
            colormap=colormap
            )
    
    def draw_node(self, node, collapsed):
        lca_value = node.props.get('lca')
        if not lca_value:
            return

        lca_dict = memoized_string_to_dict(lca_value)
        lca = lca_dict.get(self.rank, None)
        if not lca:
            return

        # Check if parent has the same LCA
        parent = node.up
        parent_lca = None
        if parent and parent.props.get('lca'):
            parent_lca_dict = memoized_string_to_dict(parent.props['lca'])
            parent_lca = parent_lca_dict.get(self.rank, None)

        # Skip drawing if parent's LCA is the same
        if parent_lca == lca:
            return
        
        # Draw LCA band since parent is different (or missing)
        color = self.color_dict.get(lca, 'lightgray')
        lca_face = TextFace(lca, rotation=90, style={'fill': 'black'}, position = 'aligned')
        
        yield BoxFace(
            wmax=self.rect_width,
            hmax=None,
            text=lca_face, 
            column=self.column,
            position='aligned',
            style={'fill': color, 'opacity': 1},
            zoomable=False
        )

def make_is_leaf_fn(collapse_rank):
    """
    Returns a function used by 'is-leaf-fn' that collapses nodes at or below a given rank.
    """
    def is_leaf_fn(node):
        node_rank = node.props.get("rank")
        lca_str = node.props.get("lca", "")
        if not node_rank or not lca_str:
            return False  # Do not collapse if missing info

        # Convert "lca" string to dict, e.g. {"phylum": "p__X", ...}
        lca_dict = memoized_string_to_dict(lca_str)
        lca = lca_dict.get(collapse_rank, None)
        # Determine if node's lineage includes the target rank
        if collapse_rank in lca_dict:
            # Compare rank positions
            try:
                node_rank_idx = TAXONOMIC_RANK_ORDER.index(node_rank)
                collapse_rank_idx = TAXONOMIC_RANK_ORDER.index(collapse_rank)
                # Collapse nodes at or below the desired rank
                return node_rank_idx >= collapse_rank_idx
            except ValueError:
                return False  # If unknown rank, don’t collapse
        return False  # Not even in the lineage

    return is_leaf_fn

def make_draw_tree_collapse(rank, color_dict):
    def draw_tree(tree):
        style = DEFAULT_TREE_STYLE.copy() # otherwise it will be modified in place
        style['is-leaf-fn'] = make_is_leaf_fn(rank)
        yield style
        if color_dict:
            yield LegendFace(title='TaxaCollapse_'+rank,
                    variable='discrete',
                    colormap=color_dict,
                    )
        
    return draw_tree

def draw_collapsed_node(rank, color_dict, rect_width=20, column=0):
    def draw_node(node, collapsed):
        node_rank = node.props.get('rank')
        node_sciname = node.props.get('sci_name')
        named_lineage = node.props.get('named_lineage', None)
        
        lca_value = node.props.get('lca')
        if lca_value:
            lca_dict = memoized_string_to_dict(lca_value)
            lca = lca_dict.get(rank, None)
            if lca:
                color = color_dict.get(lca, 'lightgray')
        
                if node.is_leaf or collapsed:
                    lca_face = TextFace(lca, rotation=90, style={'fill': 'black'}, position = 'aligned')
        
                    yield BoxFace(
                        wmax=rect_width,
                        hmax=None,
                        text=lca_face, 
                        column=column,
                        position='aligned',
                        style={'fill': color, 'opacity': 1},
                        zoomable=False
                    )
        return
    return draw_node

# class TaxaCollapse(Layout):
#     def __init__(self, name="Taxa collapsed", rank=None, color_dict={}, rect_width=20, column=0, padding_x=1, padding_y=0, legend=True, active=True):
#         self.rank = rank
#         self.color_dict=color_dict
#         self.rect_width = rect_width
#         self.column = column
#         self.padding_x = padding_x
#         self.padding_y = padding_y
#         self.active = active

class LayoutSciName(Layout):
    def __init__(self, name="Scientific name", color_dict={}, sci_prop='sci_name', active=True):
        self.color_dict = color_dict
        self.sci_prop = sci_prop
        self.default_collapsed_style = DEFAULT_COLLAPSED_STYLE
        
        super().__init__(name=name,
                         draw_node=self.draw_node,
                         active=active)

    def draw_node(self, node, collapsed):
        if node.is_leaf:
            sci_name = node.props.get(self.sci_prop)
            prot_id = node.name

            rank_colordict = self.color_dict.get(node.props.get('rank'),'')
            if rank_colordict:
                color = rank_colordict.get(sci_name, 'gray')
            else:
                color = 'gray'
            style = {'fill': color}

            # node.add_face(TextFace(sci_name, color = color, padding_x=2, min_fsize=4, max_fsize=25),
            #     column=0, position="branch_right")

            yield TextFace(
                sci_name,
                style=style,
                fs_min=4,
                fs_max=25,
                position="right",
                
            )
            
            if prot_id:
                if len(prot_id) > 40:
                    prot_id = prot_id[0:37] + " ..."
           
            #node.add_face(TextFace(prot_id, color = 'Gray', padding_x=2), column = 2, position = "aligned")
        if collapsed:
            # Collapsed face
            names = summary(node.children)
            texts = names if len(names) < 6 else (names[:3] + ['...'] + names[-2:])
            for i, text in enumerate(texts):
                sci_name = node.props.get(self.sci_prop)
                rank_colordict = self.color_dict.get(node.props.get('rank'),'')
                if rank_colordict:
                    color = rank_colordict.get(sci_name, 'gray')
                else:
                    color = 'gray'
                style = {'fill': color}
                yield TextFace(
                    text,
                    style=style,
                    fs_min=4,
                    fs_max=25,
                    position="right",                    
                )

class LayoutEvolEvents(Layout):
    def __init__(self, name="Evolutionary events", 
            prop="evoltype",
            speciation_color="blue", 
            duplication_color="red", node_size=5,
            active=True, legend=True):

    
        self.prop = prop
        self.speciation_color = speciation_color
        self.duplication_color = duplication_color
        self.node_size = node_size
        self.legend = legend
        self.active = active

        self.default_collapsed_style = DEFAULT_COLLAPSED_STYLE
        
        super().__init__(name=name,
                         draw_node=self.draw_node,
                         draw_tree=self.draw_tree,
                         active=active)

    def draw_tree(self, tree):
        # Provide collapsed node style
        yield {"collapsed": self.default_collapsed_style}
        colormap = { 
            "Speciation event": self.speciation_color,
            "Duplication event": self.duplication_color 
            }
        yield LegendFace(title=self.name,
            variable='discrete',
            colormap=colormap
            )
    
    def draw_node(self, node, collapsed):
        
        if not node.is_leaf:
            if node.props.get(self.prop, "") == "S":
                style_dot = {
                    'fill': self.speciation_color,
                    'radius': self.node_size,
                }
            elif node.props.get(self.prop, "") == "D":
                style_dot = {
                    'fill': self.duplication_color,
                    'radius': self.node_size,
                }
            else:
                style_dot = {}
            yield {
                'dot': style_dot,
            }

class TaxaLCA(Layout):
    def __init__(self, name="LCA", rank=None, color_dict={}, rect_width=20, column=0, padding_x=1, padding_y=0, legend=True, active=True):
        self.rank = rank
        self.color_dict = color_dict
        self.rect_width = rect_width
        self.column = column
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.active = active

        self.default_collapsed_style = DEFAULT_COLLAPSED_STYLE
        super().__init__(name=name,
                         draw_node=self.draw_node,
                         draw_tree=self.draw_tree,
                         active=active)
    
    def draw_tree(self, tree):
        # Provide collapsed node style
        yield {"collapsed": self.default_collapsed_style}
        if self.color_dict:
            colormap = self.color_dict
        else:
            colormap = {}
        yield TextFace(
                " ",
                fs_min=4,
                fs_max=25,
            )
        yield LegendFace(title='TaxaLCA_'+self.rank,
            variable='discrete',
            colormap=colormap
            )
    
    def draw_node(self, node, collapsed):
        lca_value = node.props.get('lca')
        if not lca_value:
            return

        lca_dict = memoized_string_to_dict(lca_value)
        lca = lca_dict.get(self.rank, None)
        if not lca:
            return

        # Draw LCA band since parent is different (or missing)
        color = self.color_dict.get(lca, 'lightgray')
        style = {'fill': color}
        if collapsed:
            yield TextFace(
                lca,
                style=style,
                fs_min=4,
                fs_max=25,
                position="right",                    
            )