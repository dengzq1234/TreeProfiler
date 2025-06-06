from io import StringIO 
from collections import OrderedDict, namedtuple
import numpy as np
import math
import re

from ete4 import Tree
from ete4.smartview.faces import HeatmapFace, LegendFace, TextArrayFace
from ete4.smartview import BASIC_LAYOUT, Layout

# Global default for collapsed nodes
DEFAULT_COLLAPSED_STYLE = {
    'shape': 'outline',
    #'stroke': '#0000FF',
    #'stroke-width': 1,
    'fill': '#303030',
    'opacity': 0.5,
}

class ProfileLayout(Layout):
    def __init__(self, name='Profile Layout', 
        matrix={}, matrix_props=[], 
        value_range=(0,1), color_range=('#FFFFFF', '#f00'), 
        poswidth=15, active=True, legend=True):
        
        self.name = name
        self.matrix = matrix
        self.matrix_props = matrix_props
        self.value_range = value_range
        self.color_range = color_range
        self.poswidth = poswidth
        self.active = active
        self.legend = legend
        self.default_collapsed_style = DEFAULT_COLLAPSED_STYLE

        super().__init__(name=name, 
                        draw_tree=self.draw_tree,
                        draw_node=self.draw_node,
                        active=active)

    def draw_tree(self, tree):
        # Provide collapsed node style
        yield {"collapsed": self.default_collapsed_style}
        yield TextArrayFace(
            self.matrix_props, 
            hmax=30, 
            rotation=-90,
            position='header'
        )
        if self.legend:
            yield LegendFace(title=self.name,
                variable='continuous',
                value_range=self.value_range,
                color_range=tuple(reversed(self.color_range)),
                )

    def draw_node(self, node, collapsed):
        values = self.matrix.get(node.name, None)
        if values:
            if node.is_leaf:
                yield HeatmapFace(values,
                                value_range=self.value_range,
                                color_range=self.color_range,
                                position='aligned')
            if collapsed:
                yield HeatmapFace(values,
                                value_range=self.value_range,
                                color_range=self.color_range,
                                position='aligned')