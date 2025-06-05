
from ete4.smartview.faces import Face
import ete4.smartview.graphics as gr
from ete4.smartview.coordinates import Size, Box, make_box

from ete4 import Tree
from ete4.smartview import Layout, BASIC_LAYOUT, SeqFace

from pathlib import Path
from io import StringIO
import json
import re




__all__ = [ "LayoutAlignment" ]
DOMAIN2COLOR = 'pfam2color.json' # smart2color.json

def get_colormap():
    with open(Path(__file__).parent / DOMAIN2COLOR) as handle:
        _pfam2color = json.load(handle)
    return _pfam2color

class SeqMotifFaceNew(Face):
    """A face for visualizing sequence motifs as rounded rectangles with connecting lines."""

    def __init__(self, rects, len_alg=None, wmax=1800, hmax=30, 
                seq_format='()', box_corner_radius=10, 
                box_opacity=0.7, box_storke_width=0.1,
                fgcolor='black', bgcolor='#bcc3d0', 
                gap_color='grey', gap_linewidth=0.5,
                font_color='black', max_fsize=12, ftype='sans-serif',
                position='aligned', column=0, anchor=None):
        """
        :param rects: List of motif regions, each defined as (start, end, color, label).
        :param wmax: Total width of the sequence visualization.
        :param hmax: Height of the motif boxes.
        :param corner_radius: Radius for rounded corners.
        :param gap_color: Color of the connecting lines.
        :param gap_linewidth: Width of the connecting lines.
        :param position: Position of the face in the layout.
        :param column: Column index for alignment.
        :param anchor: Alignment anchor.
        """
        super().__init__(position, column, anchor)
        self.rects = rects
        self.len_alg = len_alg
        self.wmax = wmax
        self.hmax = hmax
        self.seq_format = seq_format
        self.box_corner_radius = box_corner_radius
        self.box_opacity = 0.7
        self.box_storke_width = 0.1
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        self.gap_color = gap_color
        self.gap_linewidth = gap_linewidth
        self.font_color = font_color
        self.max_fsize = max_fsize
        self.ftype = ftype
        
        #self.triangles = {'^': 'top', '>': 'right', 'v': 'bottom', '<': 'left'}

        #self.gaps = self._compute_gaps(rects, wmax)

    def _compute_gaps(self, rects, seq_start, seq_end):
        """Compute the gaps (empty spaces between domain)."""
        gaps = []
        prev_end = seq_start

        for start_x, end_x, _, _, _, _, _, _ in rects:
            if start_x > prev_end:
                gaps.append((prev_end, start_x))
            prev_end = end_x

        if prev_end < seq_end:
            gaps.append((prev_end, seq_end))

        return gaps

    def draw(self, nodes, size, collapsed, zoom=(1, 1), ax_ay=(0, 0), r=1):
        dx, dy = size
        zx, zy = zoom
        
        # Compute width and height with respect to zoom 
        if dx <= 0:
            w = self.wmax
        
        h = min(zy * r * dy, self.hmax) if dy > 0 else self.hmax
        
        graphics = []

        # Normalize per-node sequence range
        # Sort rects by start
        sorted_rects = sorted(self.rects, key=lambda x: x[0])
        if not sorted_rects:
            return graphics, Size(w, h / (r * zy))

        
        #seq_start = min(start for start, _, _, _, _, _, _, _ in sorted_rects)
        seq_start = 0
        max_domain_end = max(end for _, end, *_ in sorted_rects)
        seq_end = max(max_domain_end, self.len_alg or w)
        
        seq_length = seq_end - seq_start
        
        if seq_length == 0:
            seq_length = 1  # avoid division by zero

        scale = w / seq_length

        # Compute gaps per draw call
        gaps = self._compute_gaps(sorted_rects, seq_start, seq_end)
        
        # Draw connecting lines in the gaps
        for gap_start, gap_end in gaps:
            
            gap_width = (gap_end - gap_start) * scale

            if gap_width > 0:
                size_obj = Size(gap_width, h / (r * zy))
                line_height = h / (r * zy) / 2
                box = make_box(((gap_start - seq_start) * scale, line_height), size_obj)
                style = {
                    'stroke': self.gap_color, 
                    'stroke-width': self.gap_linewidth
                    }
                graphics.append(gr.draw_line((box.x, box.y), (box.x + box.dx, box.y), style))

        # Draw rectangles
        for start_x, end_x, seq_format, poswidth, heigh, fgcolor, bgcolor, label in sorted_rects:
            
            # config size for rect
            if poswidth:
                rect_width = float(poswidth) * scale
            else:
                rect_width = (end_x - start_x) * scale

            # config height for rect
            if heigh:
                h = float(heigh)
            
            box_x = (start_x - seq_start) * scale
            size_obj = Size(rect_width, h / (r * zy))
            box = make_box((box_x, 0), size_obj)
            
            if seq_format:
                if seq_format == '()':
                    box_corner_radius = 10
                elif seq_format == '[]':
                    box_corner_radius = 0
            else:
                seq_format = self.seq_format
                box_corner_radius = self.box_corner_radius
            
            graphics.append(gr.draw_rect(box, {
                'fill': fgcolor,
                'opacity': self.box_opacity,
                'stroke': bgcolor,
                'stroke-width': self.box_storke_width,
                'rx': box_corner_radius,
                'ry': box_corner_radius
            }))

            # Check if label fits
            if label:
                try:
                    ftype, fsize, fcolor, text = label.split("|")
                    fsize = int(fsize)
                except:
                    ftype = self.ftype
                    fsize = self.max_fsize
                    fcolor = self.font_color
                    text = label

                text_style = {
                    'fill': fcolor, 
                    'font-family': ftype,
                    'text-anchor': 'middle',
                    }
                text_element = gr.draw_text(box, (0.5, 0.5), text, fs_max=fsize, rotation=0, style=text_style)
                graphics.append(text_element)

        return graphics, Size(w, h / (r * zy))

class AlgFace(Face):
    """A face for visualizing sequence alignments in grey blocks instead of every aa."""

    def __init__(self, seq, width=400, seqtype='aa', draw_text=True,
                 hmax=10, fs_max=15, style='', render='auto', compact_seq=True,
                 compact_cutoff=0.5, position='top', column=0, anchor=None):
        super().__init__(position, column, anchor)
        self.seq = ''.join(seq)  # ensure flat string
        self.seqtype = seqtype
        self.draw_text = draw_text
        self.fs_max = fs_max
        self.hmax = hmax
        self.style = style
        self.render = render
        self.seqlength = len(self.seq)
        self.width = width
        self.poswidth = self.width / self.seqlength
        self.line_color = 'black'
        self.line_width = 0.5
        self.block_color = '#222222'
        self.block_opacity = 0.5
        self.blocks = self._build_blocks()
        self.compact_seq = compact_seq
        self.compact_cutoff = 1
        
    def _build_blocks(self):
        """Identify contiguous regions without gaps."""
        blocks = []
        pos = 0
        for segment in re.split('([^-]+)', self.seq):
            if segment and not segment.startswith("-"):
                blocks.append((pos, pos + len(segment)))
            pos += len(segment)
        return blocks


    def _compute_gaps(self, seq_start, seq_end):
        """Compute the gaps (empty spaces between domain)."""
        gaps = []
        prev_end = seq_start

        for start_x, end_x in self.blocks:
            if start_x > prev_end:
                gaps.append((prev_end, start_x))
            prev_end = end_x

        if prev_end < seq_end:
            gaps.append((prev_end, seq_end))

        return gaps    

    def draw(self, nodes, size, collapsed, zoom=(1, 1), ax_ay=(0, 0), r=1):
        dx, dy = size
        zx, zy = zoom
        
        if dx <= 0:  # no limit on dx? make it as big as possible
            dx = self.poswidth * self.seqlength 

        # Compute width and height with respect to zoom
        w = dx
        h = min(zy * r * dy, self.hmax) if dy > 0 else self.hmax
        
        avg_pixel_per_residue = dx / self.seqlength
        too_small = (w * zx) / self.seqlength < self.compact_cutoff
        use_blocks = self.compact_seq or too_small

        graphics = []
        scale = w / self.seqlength

        if use_blocks:
            seq_start, seq_end = 0, self.seqlength
            gaps = self._compute_gaps(seq_start, seq_end)
            sorted_blocks = sorted(self.blocks, key=lambda x: x[0])

            # Draw connecting lines
            for gap_start, gap_end in gaps:
                gap_width = (gap_end - gap_start) * scale
                if gap_width <= 0:
                    continue

                y_coord = h / (r * zy) / 2
                size_obj = Size(gap_width, y_coord)
                box = make_box((gap_start * scale, y_coord), size_obj)

                style = {'stroke': self.line_color, 'stroke-width': self.line_width}
                graphics.append(gr.draw_line((box.x, box.y), (box.x + box.dx, box.y), style))

            # Draw blocks
            for start, end in sorted_blocks:
                start_px = start * scale
                end_px = end * scale
                size_obj = Size(end_px - start_px, h / (r * zy))
                box = make_box((start_px, 0), size_obj)

                graphics.append(gr.draw_rect(box, {
                    'fill': self.block_color,
                    'opacity': self.block_opacity,
                    'rx': 5,
                    'ry': 5
                }))
        else:
            # Full sequence drawing
            if dy <= 0:
                assert self.hmax is not None, 'hmax needed if dy <= 0'
                dy = self.hmax / zy
            elif self.hmax is not None:
                dy = min(dy, self.hmax / zy)

            size_obj = Size(dx, dy)
            box = make_box((0, 0), size_obj)

            graphics.append(gr.draw_seq(box, self.seq, self.seqtype, self.draw_text,
                                        self.fs_max, self.style, self.render))

        return graphics, size_obj

def create_pfam(tree, len_alg=None, width=1000, column=0):
    colormap = get_colormap()
    def parse_dom_arq_string(dom_arq_string):
        rects = []
        if not dom_arq_string:
            return rects
        for dom_arq in dom_arq_string.split("||"):
            parts = dom_arq.split("@")
            if len(parts) == 3:
                domain_name, start, end = parts
                color = colormap.get(domain_name, "lightgray")
                rects.append([
                    int(start), int(end), 
                    "()", None, None, color, color, 
                    f"arial|15|black|{domain_name}"
                ])
        return rects

    # Get the maximum sequence length end from all nodes
    if len_alg is None:
        for node in tree.traverse():
            # Try to get len_alg directly
            val = node.props.get("len_alg", None)
            if val is not None:
                len_alg = int(val)
                break

            # Try to compute from dom_arq
            rects = parse_dom_arq_string(node.props.get("dom_arq", None))
            for r in rects:
                if len(r) >= 2:
                    len_alg = r[1]
                    break

            if len_alg is not None:
                break
            
    def draw_node(node, collapsed):
        rects = parse_dom_arq_string(node.props.get("dom_arq", None))
        if rects:
            if collapsed:
                yield SeqMotifFaceNew(rects, len_alg=len_alg, wmax=width, column=column)
            elif node.is_leaf:
                yield SeqMotifFaceNew(rects, len_alg=len_alg, wmax=width, column=column)

    return draw_node

def layout_seqface_draw_node(alignment_prop, width=1000, column=0, scale_range=None, window=[], summarize_inner_nodes=True):
    def draw_node(node, collapse):
        seq = node.props.get(alignment_prop)
        if seq:
            if window:
                start, end = window
                seq = seq[int(start):int(end)]
            if node.is_leaf:
                yield AlgFace(
                    seq,
                    render='svg', 
                    width=width, 
                    position='aligned',
                    column=column,
                    compact_seq=False)
            if summarize_inner_nodes:
                if collapse:
                    yield AlgFace(
                    seq,
                    render='svg', 
                    width=width, 
                    position='aligned',
                    column=column,
                    compact_seq=False)
    return draw_node