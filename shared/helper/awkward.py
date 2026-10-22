import awkward as ak
import graphviz


def unique(data, axis=1):
    data_sorted = ak.sort(data, axis=axis)
    lengths = ak.flatten(ak.run_lengths(data_sorted), axis=None)
    grouped = ak.unflatten(data_sorted, lengths, axis=axis)
    return grouped[..., 0]


def all_fields(data_type, prefix=()):
    if isinstance(data_type, ak.types.RecordType):
        for name, field_type in zip(data_type.fields, data_type.contents):
            yield from all_fields(field_type, prefix + (name,))

    elif isinstance(data_type, (ak.types.ArrayType, ak.types.ListType)):
        yield from all_fields(data_type.content, prefix)

    else:
        yield prefix


def select_fields(data, *args, **kws):
    selected = {}
    fields = {}
    for arg in args:
        if isinstance(arg, str):
            arg = arg,
        fields['_'.join(arg)] = arg
    fields = fields | kws
    for name, field in fields.items():
        selected[name] = data[field]
    return ak.zip(selected, depth_limit=1)


def layout_to_dot(array, name="awkward_layout"):
    """
    Generic Awkward layout → Graphviz DOT.
    
    It traverses *all* attributes of every layout node,
    discovers child layouts dynamically, and draws edges.
    """
    layout = ak.to_layout(array)

    node_lines = []
    edge_lines = []
    counter = {"id": 0}

    def new_id():
        nid = f"node{counter['id']}"
        counter["id"] += 1
        return nid

    def add_node(node_id, label):
        node_lines.append(f'  "{node_id}" [label="{label}", shape=box];')

    def is_layout(obj):
        """Check if obj is any Awkward layout type."""
        return hasattr(obj, "form") or type(obj).__module__.startswith("awkward.")

    def traverse(obj):
        """Return DOT node id for this object."""
        node_id = new_id()
        label = type(obj).__name__

        # Enrich label with some useful info
        # if hasattr(obj, "dtype"):
        #     label += f"\\ndtype={obj.dtype}"
        # if hasattr(obj, "length"):
        #     label += f"\\nlen={obj.length}"
        if hasattr(obj, "parameters"):
            for key, val in obj.parameters.items():
                label += f"\\n{key} = {val}"
        if hasattr(obj, "data"):
            label += f"\\n{str(obj.data.tolist())}"

        add_node(node_id, label)

        ignore_attrs = ['backend', 'form', 'nplike']
        if hasattr(obj, "offsets"):
            ignore_attrs.extend(["starts", "stops"])

        # Iterate through attributes
        for attr in dir(obj):
            if attr.startswith("_"):
                continue

            if attr in ignore_attrs:
                continue

            try:
                value = getattr(obj, attr)
            except Exception:
                continue

            # Skip large buffers
            if callable(value):
                continue

            # Case 1: attribute itself is a layout
            if is_layout(value):
                child_id = traverse(value)
                edge_lines.append(
                    f'  "{node_id}" -> "{child_id}" [label="{attr}"];'
                )
                continue

            # Case 2: attribute is a list/tuple of layouts
            if isinstance(value, (list, tuple)):
                for i, element in enumerate(value):
                    if is_layout(element):
                        child_id = traverse(element)
                        edge_lines.append(
                            f'  "{node_id}" -> "{child_id}" [label="{attr}[{i}]"];'
                        )
                continue

            # Case 3: ignore primitives, strings, numbers
            # We do not create graph nodes for them
            # You can change this if you want leaf-nodes for primitives

        return node_id

    traverse(layout)

    dot = [
        f"digraph {name} {{",
        "  rankdir=LR;",
        *node_lines,
        *edge_lines,
        "}",
    ]
    return "\n".join(dot)

def dot(array):
    code = layout_to_dot(array)
    return graphviz.Source(code)
