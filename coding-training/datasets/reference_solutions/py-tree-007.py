def invert_tree(tree: dict | None) -> dict | None:
    if not tree: return None
    return {'val': tree.get('val', 0), 'left': invert_tree(tree.get('right')), 'right': invert_tree(tree.get('left'))}
