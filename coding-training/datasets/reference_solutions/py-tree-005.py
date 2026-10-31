def is_leaf_node(tree: dict | None) -> bool:
    if not tree: return False
    return tree.get('left') is None and tree.get('right') is None
