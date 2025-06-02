from ete4.smartview import Layout, TextFace, LegendFace
from .custom_faces import BoxFace
from .custom_faces import get_heatmapface, get_aggregated_heatmapface
from treeprofiler.src.utils import to_code, call, counter_call, check_nan
try:
    from distutils.util import strtobool
except ImportError:
    from treeprofiler.src.utils import strtobool

# def too_deep(node):
#     support = node.props.get('support', None)
#     if support:
#         return node.support > 0.50

def make_is_leaf_fn(conditional_output, prop2type):
    """
    Return a function that will be assigned to 'is-leaf-fn'.
    This function receives a node and returns True if all conditions are satisfied.
    """

    def is_leaf_fn(node):
        for condition in conditional_output:
            op = condition[1]
            if op == 'in':
                value = condition[0]
                prop = condition[2]
                datatype = prop2type.get(prop)
                result = call(node, prop, datatype, op, value)

            elif ':' in condition[0]:
                internal_prop, leaf_prop = condition[0].split(':')
                value = condition[2]
                datatype = prop2type.get(internal_prop)
                result = counter_call(node, internal_prop, leaf_prop, datatype, op, value)
            else:
                prop = condition[0]
                value = condition[2]
                datatype = prop2type.get(prop)
                result = call(node, prop, datatype, op, value)

            if not result:
                return False  # if any condition fails, do not collapse
        return True  # all conditions passed

    return is_leaf_fn

# Global default for collapsed nodes
DEFAULT_COLLAPSED_STYLE = {
    'shape': 'outline',
    #'stroke': '#0000FF',
    #'stroke-width': 1,
    'fill': '#303030',
    'opacity': 0.5,
}

DEFAULT_TREE_STYLE = {
    'collapsed': DEFAULT_COLLAPSED_STYLE,
    #"is_leaf_fn": too_deep,
}

def collapsed_by_layout(conditions, color2conditions, level=1, prop2type={}):
    for color, conditions in color2conditions.items():
        conditional_output = to_code(conditions)
        DEFAULT_TREE_STYLE['is-leaf-fn'] = make_is_leaf_fn(conditional_output, prop2type)
        DEFAULT_TREE_STYLE['collapsed']['fill'] = color
        return DEFAULT_TREE_STYLE

class LayoutHighlight(Layout):
    def __init__(self, name, color2conditions, column, prop2type=None, legend=True, width=70, padding_x=1, padding_y=0, active=True):
        self.name = name
        self.prop2type = prop2type
        self.color2conditions = color2conditions

        self.min_fsize = 5 
        self.max_fsize = 15
        self.width = 70
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.legend = legend
        self.active = active
        
        super().__init__(name=name,
                        draw_node=self.draw_node,
                        draw_tree=self.draw_tree,
                        active=active)

    def draw_tree(self, tree):
        yield DEFAULT_TREE_STYLE

        if self.legend:
            colormap = {','.join(v) if isinstance(v, list) else v: k for k, v in self.color2conditions.items()}
            yield LegendFace(title=self.name,
                variable='discrete',
                colormap=colormap
                )

        for color, conditions in self.color2conditions.items():
            conditional_output = to_code(conditions)
            for node in tree.traverse():
                final_call = False
                for condition in conditional_output:
                    op = condition[1]
                    if op == 'in':
                        value = condition[0]
                        prop = condition[2]
                        datatype = self.prop2type.get(prop)
                        final_call = call(node, prop, datatype, op, value)

                    elif ':' in condition[0] :
                        internal_prop, leaf_prop = condition[0].split(':')
                        value = condition[2]
                        datatype = self.prop2type[internal_prop]
                        final_call = counter_call(node, internal_prop, leaf_prop, datatype, op, value)
                    else:
                        prop = condition[0]
                        value = condition[2]
                        datatype = self.prop2type.get(prop)
                        final_call = call(node, prop, datatype, op, value)
                    if final_call == False:
                        break
                    else:
                        continue
                
                if final_call:
                    #prop_face = SelectedRectFace(name='prop')
                    node.add_prop(f'hl_{conditions}', color)  # highligh clade
                    node.add_prop(f'hl_{conditions}_endnode', True)
                    while (node):
                        node = node.up
                        if node:
                            node.add_prop(f'hl_{conditions}', True)
                
                            #node.sm_style["hz_line_width"] = 5
        return
    
    def draw_node(self, node, collapsed):
        for color, conditions in self.color2conditions.items():
            if not node.is_root:
                if node.props.get(f'hl_{conditions}'):
                    line_style = {
                            # "hz-line": {
                            #     "stroke": "red",
                            #     "stroke-width": 5,
                            #     "stroke-opacity": 1,
                            # }, 
                            "hz-line": {
                                "stroke": "black",
                                "stroke-width": 5,
                                "stroke-opacity": 1,
                            }
                    }
                    yield line_style
                    
                    if node in collapsed:
                        fgopacity = {
                            'fill': color,
                            'opacity': 0.6,
                        }
                        yield {'collapsed': fgopacity}

                    if node.props.get(f'hl_{conditions}_endnode'):
                        yield {
                                'box': 
                                    {
                                    'fill': color,
                                    'opacity': 0.6,
                                }
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
        
