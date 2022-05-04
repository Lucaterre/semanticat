import sys
import pandas as pd
from copy import deepcopy as dc
from lxml import etree

from .utils import is_empty_el, strip_ns, create_el_from_so
from .base import PositionTable, Context



def flatten_tree(tree):
    """Convert an etree into a list of tuples."""
    flat_tree = []
    depth = 0

    def __traverse_and_parse(el, depth, flat_tree):

        if not(is_empty_el(el)):
            flat_tree.append(('open', el, depth, el.text))
            depth +=1
            
        for gen in el:
            __traverse_and_parse(gen, depth, flat_tree)

        if is_empty_el(el):
            flat_tree.append(('empty', el, depth, el.tail))
        else:
            depth -= 1
            flat_tree.append(('close', el, depth, el.tail))

    __traverse_and_parse(tree, depth, flat_tree)

    return flat_tree


def flat_tree2position_table(flat_tree):
    """Convert a flattened tree into a data frame that connects character positions of 
    the text with the elements surrounding it."""
    c_position = 0
    position_table = []
    for (oc, el, depth, text) in flat_tree:

        position_table.append({
            "position": c_position,
            "row_type": oc,
            "el": el,
            "depth": depth,
            "text": None,
        })
        if text is not None:
            # for char in text:
            position_table.append({
                "position": c_position,
                "row_type": "text",
                "el": None,
                "depth": None,
                "text": text,
            })
            c_position += len(text)

    return PositionTable(pd.DataFrame(position_table))


def append_text_to_el(el, text_tail, buf):
    """Append text to the the element either within or as tail and empty the text buffer."""
    if text_tail == "text":
        el.text = buf if el.text is None else el.text + buf
    else:
        el.tail = buf if el.tail is None else el.tail + buf

# @profile
def standoff2tree(table):
    """Convert a position table to an etree."""
    curr_context = Context()
    curr_el = None
    prev_el = None
    
    text_tail = None
    root = None

    texts = table['text'].array
    els = table['el'].array

    open_types = (table['row_type'].array == 'open')
    close_types = (table['row_type'].array == 'close')
    empty_types = (table['row_type'].array == 'empty')
    text_types = (table['row_type'].array == 'text')

    text_buffer_start = None

    old2new = {}

    for irow, text_type in enumerate(text_types):

        if text_type:
            if text_buffer_start is None:
                text_buffer_start = irow
            continue

        row_el = els[irow]
        if row_el is not None:
            if row_el not in old2new:
                prev_el = curr_el
                if isinstance(row_el, etree._Comment):
                    curr_el = etree.Comment()
                else:
                    curr_el = create_el_from_so(dc(row_el.tag), dc(row_el.attrib))
                old2new[row_el] = curr_el

            
        if open_types[irow]:
            
            if text_buffer_start is not None and prev_el is not None:
                text_arr = texts[text_buffer_start:irow]
                append_text_to_el(prev_el, text_tail, "".join(text_arr))
                text_buffer_start = None

            curr_context.append(curr_el)
            if len(curr_context) > 1:
                curr_context[-2].append(curr_context[-1])
            text_tail = "text"

        elif close_types[irow]:
            if text_buffer_start is not None and prev_el is not None:
                append_text_to_el(curr_el, text_tail, "".join(texts[text_buffer_start:irow]))
                text_buffer_start = None

            curr_el = curr_context[-1]
            curr_context = Context(curr_context[:-1])
            text_tail = "tail"
            
        elif empty_types[irow]:
            if text_buffer_start is not None and prev_el is not None:
                append_text_to_el(prev_el, text_tail, "".join(texts[text_buffer_start:irow]))
                text_buffer_start = None
            if len(curr_context) > 0:
                curr_context[-1].append(curr_el)
            text_tail = "tail"


        else:
            raise ValueError("Row type unkown.")

        if root is None:
            root = curr_el

    if text_buffer_start is not None:
        append_text_to_el(curr_el, text_tail, ''.join(texts[text_buffer_start:]))

    return root, old2new