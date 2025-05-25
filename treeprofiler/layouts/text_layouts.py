from collections import OrderedDict, namedtuple
from math import pi
import random, string
from treeprofiler.src.utils import random_color, add_suffix
from .custom_faces import BoxFace

from ete4.smartview import Layout, TextFace, LegendFace

from ete4.smartview.faces import Face
import ete4.smartview.graphics as gr
from ete4.smartview.coordinates import Size, Box, make_box

# Global default for collapsed nodes
DEFAULT_COLLAPSED_STYLE = {
    'shape': 'outline',
    #'stroke': '#0000FF',
    #'stroke-width': 1,
    'fill': '#303030',
    'opacity': 0.5,
}

class LayoutText(Layout):
    def __init__(self, name, column, color_dict, prop, text_color="black", width=70, 
    min_fsize=5, max_fsize=15, padding_x=1, padding_y=0, position='aligned',
    legend=True, active=True):
        self.name = name
        self.column = column
        self.text_color = text_color
        self.color_dict = color_dict
        self.prop = prop
        self.internal_prop = prop+'_counter'
        self.width = width
        self.min_fsize = min_fsize
        self.max_fsize = max_fsize
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.position = position
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
        if self.position == 'aligned':
            yield TextFace(self.prop, rotation=-45, 
            fs_min=self.min_fsize, #fs_max=12,
            position='header', column=self.column)
        if self.color_dict:
            colormap = self.color_dict
        else:
            colormap = {self.prop: self.text_color}
        
        yield LegendFace(title=self.name,
                    variable='discrete',
                    colormap=colormap
                    )

    def draw_node(self, node, collapsed=False):
        # Get the property value
        prop_text = node.props.get(self.prop)

        # Skip if empty
        if not prop_text:
            return

        # Only draw if node is a leaf or collapsed
        if node.is_leaf or collapsed:
            
            # Convert list to comma-separated string
            if isinstance(prop_text, list):
                prop_text = ",".join(prop_text)
            else:
                prop_text = str(prop_text)

            if self.color_dict and self.color_dict.get(prop_text):
                font_color = self.color_dict.get(prop_text, 'black')
            elif self.text_color:
                font_color = self.text_color
            else:
                font_color = 'black'
            style = {'fill': font_color}

            # Yield a styled text face in the aligned column

            yield TextFace(
                prop_text,
                style=style,
                fs_min=self.min_fsize,
                fs_max=self.max_fsize,
                position=self.position,
                column=self.column
            )

class LayoutColorBranch(Layout):
    def __init__(self, name, column, color_dict, prop, legend=True, active=True, width=70, padding_x=1, padding_y=0):
        self.prop = prop
        self.column = column
        self.color_dict = color_dict
        self.internal_prop = prop+'_counter'
        self.legend = legend

        self.absence_color = "#EBEBEB"
        self.width = width
        self.line_width = 3
        self.line_style = "solid"
        self.line_opacity = 1.0
        
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.min_fsize = 5
        self.max_fsize = 12
        self.default_collapsed_style = DEFAULT_COLLAPSED_STYLE
        self.active = active

        super().__init__(name=name,
                         draw_node=self.draw_node,
                         draw_tree=self.draw_tree,
                         active=active)

    def draw_tree(self, tree):
        # Provide collapsed node style
        yield {"collapsed": self.default_collapsed_style}
        yield TextFace(self.prop, rotation=-45, position='header', column=self.column)
        if self.color_dict:
            colormap = self.color_dict
        else:
            colormap = {}
        
        yield LegendFace(title=self.name,
            variable='discrete',
            colormap=colormap
            )
    
    def draw_node(self, node, collapsed=False):
        prop_text = node.props.get(self.prop)
        # Skip if empty
        if not prop_text:
            return

        line_color = self.color_dict.get(prop_text, 'black')

        # Only draw if node is a leaf or collapsed
        if node.is_leaf or collapsed:
            # Convert list to comma-separated string
            if isinstance(prop_text, list):
                prop_text = ",".join(prop_text)
            else:
                prop_text = str(prop_text)

            yield TextFace(
                node.name,
                style={'fill': line_color},
                fs_min=self.min_fsize,
                fs_max=self.max_fsize,
                position="right",
                column=self.column
            )

        line_style = {
                "hz-line": {
                    "stroke": line_color,
                    "stroke-width": self.line_width,
                    "stroke-opacity": self.line_opacity,
                }, 
                "vt-line": {
                    "stroke": line_color,
                    "stroke-width": self.line_width,
                    "stroke-opacity": self.line_opacity,
                }
        }

        yield line_style

        if collapsed:
            yield {
                
                "collapsed": {
                    'shape': 'outline',
                    'stroke': line_color,
                    'stroke-width': 1,
                    'fill': line_color,
                    'opacity': 0.5,
                }
            }

class LayoutSymbolNode(Layout):
    def __init__(self, name=None, prop=None,
            column=0, symbol='circle', symbol_color=None, color_dict=None, 
            max_radius=1, symbol_size=5, fgopacity=0.8, 
            padding_x=2, padding_y=0, 
            scale=True, legend=True, active=True):
        
        self.name = name
        self.prop = prop
        self.column = column
        self.symbol = symbol
        self.symbol_color = symbol_color
        self.color_dict = color_dict
        self.max_radius = max_radius
        self.symbol_size = symbol_size
        self.fgopacity = fgopacity
        self.padding_x = padding_x
        self.padding_y = padding_y
        #self.position = position
        self.scale = scale
        self.legend = legend
        self.active = active

        self.default_collapsed_style = DEFAULT_COLLAPSED_STYLE

        super().__init__(name=name,
                         draw_node=self.draw_node,
                         draw_tree=self.draw_tree,
                         active=active)

    def draw_tree(self, tree):
        yield {"collapsed": self.default_collapsed_style}
        #yield TextFace(self.prop, rotation=-45, position='header', column=self.column)
        
        if self.color_dict:
            colormap = self.color_dict
        else:
            colormap = {}
        
        yield LegendFace(title=self.name,
            variable='discrete',
            colormap=colormap
            )
        
    
    def draw_node(self, node, collapsed=False):
        prop_text = node.props.get(self.prop)
        
        if prop_text is not None and prop_text != '':
            if type(prop_text) == list:
                prop_text = ",".join(prop_text)
            else:
                pass
            if self.color_dict and len(self.color_dict) >= 1:
                style_dot = {
                    'shape': self.symbol,
                    'fill': self.color_dict.get(prop_text, 'black'),
                    'radius': self.symbol_size,
                   
                }
            else:
                style_dot = {
                    'shape': self.symbol,
                    'fill': self.symbol_color,
                    'radius': self.symbol_size,
                    
                }
            
            yield {
                'dot': style_dot,
            }

class LayoutBackground(Layout):
    def __init__(self, name, color_dict, prop, width=70, column=0, 
        opacity=0.5, padding_x=1, padding_y=0, legend=True, active=True):
        
        self.name = name
        self.color_dict = color_dict
        self.prop = prop
        self.width = width
        self.column = column
        self.opacity = opacity
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
        yield {"collapsed": self.default_collapsed_style}
        #yield TextFace(self.prop, rotation=-45, position='header', column=self.column)
        
        if self.color_dict:
            colormap = self.color_dict
        else:
            colormap = {}
        
        yield LegendFace(title=self.name,
            variable='discrete',
            colormap=colormap
            )
        
    def draw_node(self, node, collapsed=False):
        prop_text = node.props.get(self.prop)

        if prop_text is not None and prop_text != '':
            if type(prop_text) == list:
                prop_text = ",".join(prop_text)
            else:
                pass

            if self.color_dict and len(self.color_dict) >= 1:
                fgopacity = {
                    'fill': self.color_dict.get(prop_text, ''),
                    'opacity': self.opacity,
                }

                yield {
                    'box': fgopacity,
                }

class LayoutRect(Layout):
    def __init__(self, name, prop, color_dict=None, 
                 width=70, column=0, opacity=0.7, padding_x=1, padding_y=0, 
                 legend=True, active=True):
        self.name = name
        self.prop = prop
        self.color_dict = color_dict
        self.absence_color = "#EBEBEB"
        self.width = width
        self.column = column
        self.opacity = opacity
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.min_fsize = 5
        self.max_fsize = 12
        self.legend = legend
        self.active = active
        self.default_collapsed_style = DEFAULT_COLLAPSED_STYLE
        

        super().__init__(name=name,
                         draw_node=self.draw_node,
                         draw_tree=self.draw_tree,
                         active=active)
    
    def draw_tree(self, tree):
        yield {"collapsed": self.default_collapsed_style}
        yield TextFace(self.prop, rotation=-45, 
        fs_min=self.min_fsize, #fs_max=12,
        position='header', column=self.column)
        
        if self.color_dict:
            colormap = self.color_dict
        else:
            colormap = {}
        
        yield LegendFace(title=self.name,
            variable='discrete',
            colormap=colormap
            )
    
    def draw_node(self, node, collapsed=False):
        prop_text = node.props.get(self.prop)
        if node.is_leaf:
            if prop_text is not None and prop_text != '':
                if type(prop_text) == list:
                    prop_text = ",".join(prop_text)
                else:
                    pass
                
                if self.color_dict and len(self.color_dict) >= 1:
                    color = self.color_dict.get(prop_text,"")
                    yield BoxFace(
                        wmax=self.width,
                        hmax=None,
                        style={'fill': color, 'opacity': self.opacity},
                        position='aligned',
                        column=self.column
                    )
            else:
                if self.color_dict and len(self.color_dict) >= 1:
                    color = self.color_dict.get(prop_text,"")
                    yield BoxFace(
                        wmax=self.width,
                        hmax=None,
                        text='NA',
                        style={'fill': self.absence_color, 'opacity': self.opacity},
                        position='aligned',
                        column=self.column
                    )

