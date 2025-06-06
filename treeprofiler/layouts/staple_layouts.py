import matplotlib as mpl
import numpy as np
from treeprofiler.src.utils import random_color, add_suffix
import colorsys

from .custom_faces import BoxFace, RotatedTextRectFace 
from ete4.smartview import Layout, TextFace, LegendFace, RectFace
from ete4.smartview.faces import Face
import ete4.smartview.graphics as gr
from ete4.smartview.coordinates import Size, Box, make_box

from ete4 import Tree

__all__ = [ "LayoutBarplot" ]

# Global default for collapsed nodes
DEFAULT_COLLAPSED_STYLE = {
    'shape': 'outline',
    #'stroke': '#0000FF',
    #'stroke-width': 1,
    'fill': '#303030',
    'opacity': 0.5,
}


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
        self.default_collapsed_style = DEFAULT_COLLAPSED_STYLE


        super().__init__(name=name,
                         draw_node=self.draw_node,
                         draw_tree=self.draw_tree,
                         active=active)
    
    def draw_tree(self, tree):
        # Provide collapsed node style
        yield {"collapsed": self.default_collapsed_style}
        
        if self.legend:
            if self.color_dict:
                yield LegendFace(title=self.name,
                    variable='continuous',
                    value_range=self.value_range,
                    color_range=self.color_range,
                    )
    
    def _get_color(self, search_value):
        num = len(self.color_dict)
        return self.color_dict.get(search_value, self.absence_color)

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

class LayoutBarplot(Layout):
    def __init__(self, name="Barplot", prop=None, width=200, color_prop=None, 
        fill_color="red", column=0, size_range=[], 
        internal_rep='avg', scale=True, legend=True, active=True):

        self.name = name
        self.prop = prop
        self.width = width
        self.color_prop = color_prop
        self.fill_color = fill_color
        self.column = column
        self.width = width
        self.size_range = size_range    
        if internal_rep:
            self.internal_prop = add_suffix(prop, internal_rep)
        else:
            self.internal_prop = None

        self.active = active
        self.default_collapsed_style = DEFAULT_COLLAPSED_STYLE


        super().__init__(name=name,
                         draw_node=self.draw_node,
                         draw_tree=self.draw_tree,
                         active=active)
    
    def draw_tree(self, tree):
        max_width = self.size_range[1] * self.width
        yield TextFace(self.name, rotation=-45, position='header', column=self.column)
        # Provide collapsed node style
        yield {"collapsed": self.default_collapsed_style}

        yield LegendFace(title=self.name,
            variable='discrete',
            colormap={
                self.prop:  self.fill_color
            },
            )
    def get_size(self, value):
        minval, maxval = self.size_range
        
        if value:
            return value / maxval * self.width
        else:
            return 0
    
    def draw_node(self, node, collapsed):

        # Determine which property to use
        prop = None
        if node.props.get(self.prop) is not None and node.is_leaf:
            prop = self.prop
        elif node.is_leaf and node.props.get(self.internal_prop) is not None:
            prop = self.internal_prop
        elif node.props.get(self.internal_prop) is not None:
            prop = self.internal_prop
        else:
            return  # No valid property found, exit early
        value = node.props.get(prop)
        # Extract visual parameters
        bar_width = self.get_size(value)


        # Construct tooltip
        # tooltip = ""
        # if node.name:
        #     tooltip += f'<b>{node.name}</b><br>'
        # if self.size_prop:
        #     tooltip += f'<br>{self.size_prop}: {node.props.get(value)}<br>'
        # if self.color_prop:
        #     tooltip += f'<br>{self.color_prop}: {color}<br>'

        # Create and add face

        if node.is_leaf:
            yield BoxFace(wmax=bar_width,
            style={
                'fill': self.fill_color,
                "stroke-width": 1,
                "stroke": "white",
                }, 
            position='aligned', 
            column=self.column,
            zoomable=False
            )
        if collapsed:
            yield BoxFace(wmax=bar_width,
            style={
                'fill': self.fill_color,
                "stroke-width": 1,
                "stroke": "white",
                }, 
            position='aligned', 
            column=self.column,
            zoomable=False
            )

class LayoutBubble(Layout):
    def __init__(self, name=None, prop=None, position="aligned", 
            column=0, bubble_color=None, max_radius=10, abs_maxval=None,
            padding_x=2, padding_y=0, 
            scale=True, legend=True, active=True, 
            internal_rep='avg'):
        
        self.name = name
        self.num_prop = prop
        self.internal_prop = add_suffix(prop, internal_rep)
        
        self.column = column
        self.position = position
        self.bubble_color = bubble_color
        self.positive_color = "red"
        self.negative_color = "blue"
        self.internal_rep = internal_rep
        self.max_radius = float(max_radius)
        self.abs_maxval = float(abs_maxval)
        self.opacity = 0.8
        self.padding_x = padding_x
        self.padding_y = padding_y
        
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
        # if self.legend:
        #     yield LegendFace(title=self.name,
        #         variable='discrete',
        #         colormap={
        #             self.num_prop:  self.color
        #         },
        #         )
    
    def _get_bubble_size(self, search_value):
        search_value = abs(float(search_value))
        bubble_size = search_value / self.abs_maxval * self.max_radius
        return bubble_size

    def draw_node(self, node, collapsed):
        # Try to get the primary value
        number = node.props.get(self.num_prop)

        # Fallback to internal_prop if number is None and it's a leaf or internal with that prop
        if number is None and node.props.get(self.internal_prop):
            number = node.props.get(self.internal_prop)

        # If we have a valid number, apply style
        if number is not None:
            bubble_size = self._get_bubble_size(number)
            #bubble_color = self.positive_color if number > 0 else self.negative_color
            self.bubble_color

            style_dot = {
                    'fill': self.bubble_color,
                    'radius': bubble_size,
                    'opacity': self.opacity,      
                }
            
            yield {
                'dot': style_dot,
            }

            if collapsed:
                yield {
                    'dot': style_dot,
                }

class LayoutHeatmap(Layout):
    def __init__(self, name=None, column=0, width=70, height=None, 
            padding_x=1, padding_y=0, prop=None, internal_rep=None,
            value_color=None, value_range=[], color_range=None, minval=0, maxval=None, 
            absence_color="#EBEBEB", show_text=False,
            legend=True):

        self.aligned_faces = True

        self.prop = prop
        self.internal_prop = add_suffix(prop, internal_rep)
        self.column = column
        self.value_color = value_color
        self.value_range = value_range
        self.color_range = color_range
        self.absence_color = absence_color
        self.maxval = maxval
        self.minval = minval

        self.width = width
        self.height = height
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.show_text = show_text
        self.legend = legend
        self.active = True
        self.default_collapsed_style = DEFAULT_COLLAPSED_STYLE
        
        super().__init__(name=name,
                            draw_node=self.draw_node,
                            draw_tree=self.draw_tree,
                            active=self.active)

    def draw_tree(self, tree):
        first_key = min(self.color_range.keys())
        last_key = max(self.color_range.keys())
        middle_key = sorted(self.color_range.keys())[len(self.color_range) // 2]
        # Provide collapsed node style
        
        yield {"collapsed": self.default_collapsed_style}
        # yield TextFace(self.prop, rotation=-90, 
        # fs_min=6, #fs_max=12,
        # position='header', column=self.column)
        # # 
        yield BoxFace(
            wmax=self.width,
            hmax=self.width*2, 
            text=TextFace(self.prop, rotation=-90, fs_min=6, fs_max=20,
            column=self.column),
            column=self.column,
            position='header',
            style={'fill': 'white', 'opacity': 1},
            zoomable=True
        )
        if self.legend:
            yield LegendFace(title=self.name,
                variable='continuous',
                value_range=[self.minval, self.maxval],
                color_range=[
                    self.color_range[last_key],
                    self.color_range[middle_key],
                    self.color_range[first_key],
                ]
                )

    def draw_node(self, node, collapsed):
         # Determine value source
        heatmap_val = None
        prop_key = None
        
        if node.props.get(self.prop) not in (None, 'NaN') and node.is_leaf:
            heatmap_val = node.props[self.prop]
            prop_key = self.prop
        elif node.is_leaf and node.props.get(self.internal_prop) not in (None, 'NaN'):
            heatmap_val = node.props[self.internal_prop]
            prop_key = self.prop
            
        elif node.props.get(self.internal_prop) not in (None, 'NaN'):
            heatmap_val = node.props[self.internal_prop]
            prop_key = self.prop

        # # Construct tooltip
        # tooltip = ""
        # if node.name:
        #     tooltip += f"<b>{node.name}</b><br>"
        # if prop_key and heatmap_val not in (None, 'NaN'):
        #     tooltip += f"<br>{prop_key}: {heatmap_val}<br>"

        if heatmap_val not in (None, 'NaN'):
            try:
                val = float(heatmap_val)
                text = f"{val:.2f}" if self.show_text else ""
                color = self.value_color.get(val, self.absence_color)
            except ValueError:
                text = "NA"
                color = self.absence_color
        else:
            text = "NA"
            color = self.absence_color

        if node.is_leaf:
            yield BoxFace(
                wmax=self.width, hmax=self.height,   
                style={
                    'fill': color,
                    "stroke-width": self.padding_x,
                    "stroke": "white",
                    }, 
                position='aligned', 
                text=text,
                column=self.column,
                zoomable=True
            )
        if collapsed:
            yield BoxFace(
                wmax=self.width, hmax=self.height,
                style={
                    'fill': color,
                    "stroke-width": self.padding_x,
                    "stroke": "white",
                    }, 
                position='aligned', 
                text=text,
                column=self.column,
                zoomable=True
            )