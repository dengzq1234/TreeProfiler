from ete4.smartview import Layout, TextFace, LegendFace
from .custom_faces import BoxFace
from .custom_faces import get_heatmapface, get_aggregated_heatmapface
from treeprofiler.src.utils import to_code, call, counter_call, check_nan
try:
    from distutils.util import strtobool
except ImportError:
    from treeprofiler.src.utils import strtobool

# Global default for collapsed nodes
DEFAULT_COLLAPSED_STYLE = {
    'shape': 'outline',
    #'stroke': '#0000FF',
    #'stroke-width': 1,
    'fill': '#303030',
    'opacity': 0.5,
}

class LayoutBinary(Layout):
    def __init__(self, name, column, color='#E60A0A', \
            prop=None, reverse=False, aggregate=False, \
            max_count=0, \
            radius=25, padding_x=1, padding_y=0, width=70, \
            legend=True, active=True):
        
        self.column = column
        self.color = color
        self.negative_color = '#EBEBEB'
        self.internal_prop = prop+'_counter'
        self.prop = prop
        self.reverse = reverse
        self.aggregate = aggregate
        self.max_count = max_count
        self.radius = radius
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.width = width
        self.legend = legend
        self.active = active
        self.min_fsize = 5
        self.max_fsize = 10
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
        
        if self.legend:
                
            if self.reverse:
                title = 'ReverseBinary_' + self.prop
                colormap = {
                    "False": self.color,
                    "True" : self.negative_color,
                    "NA": 'white'
                }
                tree_style.add_legend(title=title,
                                    variable='discrete',
                                    colormap=colormap,
                                    )
            else:
                title = 'Binary_' + self.prop
                colormap = {
                    "True": self.color,
                    "False" : self.negative_color,
                    "NA": 'white'
                }
            
            yield LegendFace(title=title,
                variable='discrete',
                colormap=colormap
                )

    def draw_node(self, node, collapsed):
        if node.is_leaf and node.props.get(self.prop):
            prop_bool = node.props.get(self.prop)
            if not check_nan(prop_bool):
                str2bool = strtobool(prop_bool)
                if bool(str2bool):
                    yield BoxFace(
                        wmax=self.width, hmax=None,
                        style={'fill': self.color, 'opacity': 1},
                        #text=to_code(prop_bool), fontsize=self.max_fsize,
                        position='aligned', column=self.column
                    )
                else: # False
                    yield BoxFace(
                        wmax=self.width, hmax=None,
                        style={'fill': self.negative_color, 'opacity': 1},
                        #text=to_code(prop_bool), fontsize=self.min_fsize,
                        position='aligned', column=self.column
                    )

            else: # missing
                yield BoxFace(
                    wmax=self.width, hmax=None,
                    style={'fill': self.negative_color, 'opacity': 1},
                    #text='NA' 
                    position='aligned', column=self.column
                )
        elif node.is_leaf and node.props.get(self.internal_prop):
            if self.aggregate:
                heatmapFace = get_aggregated_heatmapface(node, self.internal_prop, 
                max_color=self.color, width=self.width, column=self.column,
                max_count=self.max_count)
            else:
                heatmapFace = get_heatmapface(node, self.internal_prop, 
                max_color=self.color, width=self.width, column=self.column)
            yield heatmapFace

        elif collapsed and node.props.get(self.internal_prop):
            if self.aggregate:
                heatmapFace = get_aggregated_heatmapface(node, self.internal_prop, 
                max_color=self.color, width=self.width, column=self.column,
                max_count=self.max_count)
            else:    
                heatmapFace = get_heatmapface(node, self.internal_prop, 
                max_color=self.color, width=self.width, column=self.column)
            yield heatmapFace
        
         