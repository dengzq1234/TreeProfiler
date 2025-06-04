from ete4.smartview.faces import Face, TextFace
import ete4.smartview.graphics as gr
from ete4.smartview.coordinates import Size, Box, make_box

from treeprofiler.src.utils import to_code, call, counter_call, check_nan
from treeprofiler.src import utils
try:
    from distutils.util import strtobool
except ImportError:
    from treeprofiler.src.utils import strtobool

def get_aggregated_heatmapface(node, prop, min_color="#EBEBEB", max_color="#971919", tooltip=None,
                               width=70, height=None, column=0, padding_x=1, padding_y=0, count_missing=True, max_count=0):
    counter_props = node.props.get(prop).split('||')
    total = 0
    positive = 0
    for counter_prop in counter_props:
        k, v = counter_prop.split('--')
        if count_missing:
            if not check_nan(k):
                if strtobool(k):
                    positive += float(v)
            total += float(v)  # Consider missing data in total
        else:
            if not check_nan(k):
                total += float(v)  # Doesn't consider missing data in total
                if strtobool(k):
                    positive += float(v)
    
    total = int(total)
    # ratio = positive / total if total != 0 else 0
    # if ratio < 0.05 and ratio != 0:  # Show minimum color for too low
    #     ratio = 0.05
    
    # Adjust the maximum color based on 'total' to simulate darkening
    adjusted_max_color = utils.make_color_darker_scaled(max_color, positive, max_count, base=10, scale_factor=10)
    #adjusted_max_color = make_color_darker(max_color, darkening_factor=0.01)  # Example factor
    #gradient_color = color_gradient(min_color, adjusted_max_color, mix=ratio)

    if not tooltip:
        tooltip = f'<b>{node.name}</b><br>' if node.name else ''
        if prop:
            tooltip += f'<br>{prop}: {positive} / {total} <br>'
    if positive == 0:
        # aggregateFace = RectFace(width=width, 
        # text=int(positive), height=height, 
        # color=min_color, padding_x=padding_x, padding_y=padding_y, tooltip=tooltip)
        aggregateFace = BoxFace(
            wmax=width, hmax=None,
            text=str(positive),
            style={'fill': min_color, 'opacity': 1},
            position='aligned', column=column
        )
    else:
        aggregateFace = BoxFace(
            wmax=width, hmax=None,
            text=str(positive),
            style={'fill': adjusted_max_color, 'opacity': 1},
            position='aligned', column=column
        )
    return aggregateFace

def get_heatmapface(node, prop, 
    min_color="#EBEBEB", max_color="#971919", tooltip=None, 
    width=70, height=None, column=0, padding_x=1, padding_y=0, 
    count_missing=True, reverse=False, min_ratio=0.05):

    counter_props = node.props.get(prop).split('||')
    total = 0
    positive = 0
    for counter_prop in counter_props:
        k, v = counter_prop.split('--')
        if count_missing:
            if not check_nan(k):
                if strtobool(k):
                    positive = float(v)
            total += float(v) # here consider missing data in total
        else:
            if not check_nan(k):
                total += float(v) # here doesn't consider missing data in total
                if strtobool(k):
                    positive = float(v)
            
    total = int(total)
    if total != 0:
        ratio = positive / total
    else:
        ratio = 0
    
    if reverse:
        ratio = 1 - ratio

    if ratio < 0.05 and ratio != 0: # show minimum color for too low
        ratio = 0.05

    c1 = min_color
    c2 = max_color
    gradient_color = utils.color_gradient(c1, c2, mix=ratio)
    text = f"{positive} / {total}"
    # gradientFace = RectFace(width=100,height=50,text="%.1f" % (ratio*100), color=gradient_color, 
    #         padding_x=1, padding_y=1)

    
    # gradientFace = RectFace(width=width, height=height, 
    #                         #text=text, 
    #                         color=gradient_color, 
    #                         )
    gradientFace = BoxFace(
            wmax=width, hmax=None,
            style={'fill': gradient_color, 'opacity': 1},
            position='aligned', column=column
        )
    return gradientFace

class BoxedFace(Face):
    """A shape defined by a box (with optionally a text inside)."""
    # Base class for BoxFace and RectFace.

    def __init__(self, wmax=None, hmax=None, text=None,
                 position='top', column=0, anchor=None, zoomable=True):
        super().__init__(position, column, anchor)

        self.wmax = wmax  # maximum width in pixels
        self.hmax = hmax  # maximum height in pixels
        self.text = TextFace(text) if type(text) is str else text
        self.zoomable = zoomable  # whether to scale the size with zoom
        self.drawing_fn = None  # will be set by its subclasses

    def draw(self, nodes, size, collapsed, zoom=(1, 1), ax_ay=(0, 0), r=1):
        dx, dy = size
        zx, zy = zoom

        # Find the width and height so they are never bigger than the max.
        assert dx > 0 or self.wmax is not None, 'wmax needed'
        assert dy > 0 or self.hmax is not None, 'hmax needed'
        w, h = self.wmax, self.hmax
        if dx > 0:
            w = min(w, dx)     if w is not None else dx
        if dy > 0:
            h = min(h, zy * r * dy) if h is not None else zy * r * dy

        # Keep the ratio h/w if we had hmax in addition to wmax.
        if self.hmax:
            h_over_w = self.hmax / self.wmax

            if h / w > h_over_w:
                h = h_over_w * w
            else:
                w = h / h_over_w

        # Return the graphics and their size.
        if self.zoomable:
            size = Size(w, h/(r*zy))
        else:
            size = Size(w/zx, h/(r*zy))
        box = make_box((0, 0), size)
        graphics = [self.drawing_fn(box)]

        if self.text:
            # Draw the text centered in x (0.5). But we have to shift the y
            # "by hand" because faces let the caller anchor in y afterwards
            # (so several faces can be vertically stacked and then anchored).
            graphics_text, size_text = self.text.draw(nodes, size, collapsed,
                                                      zoom, (0.5, 0.5), r)
            circular = False
            shift = (0, (size.dy - size_text.dy) / 2)  # shift the y
            graphics += gr.draw_group(graphics_text, circular, shift)

        return graphics, size

class BoxFace(BoxedFace):
    """A box (with optionally a text inside)."""

    def __init__(self, wmax=None, hmax=None, style='', text=None,
                 position='top', column=0, anchor=None, zoomable=True):
        super().__init__(wmax, hmax, text, position, column, anchor, zoomable)

        self.drawing_fn = lambda box: gr.draw_box(box, style)


class RotatedTextRectFace(BoxedFace):
    """A rectangle face that allows text inside to be rotated."""

    def __init__(self, wmax, hmax=None, text="", rotation=0, style='',
                 font_size=12, text_fill="black", position='top', column=0, anchor=None):
        """
        :param wmax: Maximum width of the rectangle.
        :param hmax: Maximum height of the rectangle.
        :param text: Text to display inside the rectangle.
        :param rotation: Rotation angle (in degrees) of the text.
        :param style: Dictionary of styling options for the rectangle.
        :param font_size: Font size for the text.
        :param text_fill: Color of the text.
        :param position: Position of the face (aligned, header, etc.).
        :param column: Column position for alignment.
        :param anchor: Anchor point (controls positioning).
        """
        super().__init__(wmax, hmax, text, position, column, anchor)

        self.style = style
        self.font_size = font_size  # Custom font size
        self.text_fill = text_fill  # Text color
        self.rotation = rotation
        self.text = TextFace(text, rotation=self.rotation) if type(text) is str else text
        
        # Set the drawing function from BoxedFace
        self.drawing_fn = lambda box: gr.draw_box(box, self.style)

    def draw(self, nodes, size, collapsed, zoom=(1, 1), ax_ay=(0, 0), r=1):
        """
        Draws a rotated rectangle with text inside.
        """
        graphics, size = super().draw(nodes, size, collapsed, zoom, ax_ay, r)
        
        if self.text:
            #self.text.rotation = self.rotation
            # Draw the text centered in x (0.5). But we have to shift the y
            # "by hand" because faces let the caller anchor in y afterwards
            # (so several faces can be vertically stacked and then anchored).
            graphics_text, size_text = self.text.draw(nodes, size, collapsed,
                                                      zoom, (0.5, 0.5), r)
            circular = False
            shift = (0, (size.dy - size_text.dy) / 2)  # shift the y
            graphics += gr.draw_group(graphics_text, circular, shift)

        return graphics, size