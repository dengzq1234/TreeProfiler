import matplotlib as mpl
import numpy as np
from treeprofiler.src.utils import random_color, add_suffix
import colorsys

from .custom_faces import BoxFace, RotatedTextRectFace
from ete4.smartview import Layout, TextFace, LegendFace
from ete4.smartview.faces import Face
import ete4.smartview.graphics as gr
from ete4.smartview.coordinates import Size, Box, make_box

from ete4 import Tree



__all__ = [ "LayoutBarplot" ]

def heatmap_gradient(hue, intensity, granularity):
    min_lightness = 0.35 
    max_lightness = 0.9
    base_value = intensity

    # each gradient must contain 100 lightly descendant colors
    colors = []   
    rgb2hex = lambda rgb: '#%02x%02x%02x' % rgb
    l_factor = (max_lightness-min_lightness) / float(granularity)
    l = min_lightness
    while l <= max_lightness:
        l += l_factor
        rgb =  rgb2hex(tuple(map(lambda x: int(x*255), colorsys.hls_to_rgb(hue, l, base_value))))
        colors.append(rgb)
        
    colors.append("#ffffff")
    return list(reversed(colors))

def color_gradient(c1, c2, mix=0):
    """ Fade (linear interpolate) from color c1 (at mix=0) to c2 (mix=1) """
    # https://stackoverflow.com/questions/25668828/how-to-create-colour-gradient-in-python
    c1 = np.array(mpl.colors.to_rgb(c1))
    c2 = np.array(mpl.colors.to_rgb(c2))
    return mpl.colors.to_hex((1-mix)*c1 + mix*c2)

def swap_pos(pos, angle):
    if abs(angle) >= pi / 2:
        if pos == 'branch_top':
            pos = 'branch_bottom'
        elif pos == 'branch_bottom':
            pos = 'branch_top'
    return pos

class LayoutBranchScore(Layout):
    def __init__(self, name, color_dict, score_prop, internal_rep=None, \
    value_range=None, color_range=None, show_score=False, legend=True, active=True):

        self.score_prop = score_prop
        if internal_rep:
            self.internal_prop = add_suffix(score_prop, internal_rep)
        else:
            self.internal_prop = None
        self.color_dict = color_dict
        self.legend = legend
        self.absence_color = "black"
        self.value_range = value_range
        self.color_range = color_range
        self.show_score = show_score
        self.line_width = 3
        self.line_opacity = 0.8
        self.active = active

        super().__init__(name=name,
                         draw_node=self.draw_node,
                         draw_tree=self.draw_tree,
                         active=active)
    
    def draw_tree(self, tree):
        if self.legend:
            if self.color_dict:
                yield LegendFace(title=self.name,
                    variable='continuous',
                    value_range=self.value_range,
                    color_range=self.color_range,
                    )
    
    def _get_color(self, search_value):
        num = len(self.color_dict)
        
        index_values = np.linspace(self.value_range[0], self.value_range[1], num)
        index = np.abs(index_values - search_value).argmin() + 1
        
        return self.color_dict.get(index, self.absence_color)

    def draw_node(self, node, collapsed):
        # Try to get score from primary prop
        score = node.props.get(self.score_prop)

        # If not available, check internal_prop (with leaf priority)
        if score is None and node.is_leaf:
            score = node.props.get(self.internal_prop)
        if score is None:
            score = node.props.get(self.internal_prop)

        # If still not found, exit
        if score is None:
            return

        # Convert to float
        score = float(score)
        color = self._get_color(score)
        
        # Apply styles
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
