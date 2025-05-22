from collections import OrderedDict, namedtuple
from math import pi
import random, string
from treeprofiler.src.utils import random_color, add_suffix


from ete4.smartview import Layout, TextFace, LegendFace

class LayoutText(Layout):
    def __init__(self, name, column, color_dict, prop, width=70, min_fsize=5, max_fsize=15, padding_x=1, padding_y=0, legend=True, active=True):

        self.name = name
        self.column = column
        self.color_dict = color_dict
        self.prop = prop
        self.width = width
        self.min_fsize = min_fsize
        self.max_fsize = max_fsize
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.legend = legend
        self.active = active

        def draw_node(node, collapsed=False):
            if node.is_leaf and node.props.get(self.prop) != '':
                prop_text = node.props.get(self.prop)
                if type(prop_text) == list:
                    prop_text = ",".join(prop_text)
                else:
                    prop_text = str(prop_text)
                font_color = self.color_dict.get(prop_text, 'black') 
                style={'fill': font_color}
                yield TextFace(prop_text,
                        style=style,
                        fs_min=self.min_fsize, fs_max=self.max_fsize,
                        position='aligned', column=self.column)
        
        super().__init__(name=name,
                         draw_node=draw_node,
                         draw_tree=self.draw_tree,
                         active=active)
                         
    def draw_tree(self, tree):
        yield TextFace(self.prop, rotation=-45, position='header', column=self.column)
        yield LegendFace(title=self.name,
                    variable='discrete',
                    colormap=self.color_dict
                    )
