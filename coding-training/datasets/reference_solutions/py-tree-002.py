def max_tree_depth(tree: dict | None) -> int:
    if not tree: return 0
    return 1 + max(max_tree_depth(tree.get('left')), max_tree_depth(tree.get('right')))
