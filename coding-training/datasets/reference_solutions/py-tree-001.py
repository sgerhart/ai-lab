def count_tree_nodes(tree: dict | None) -> int:
    if not tree: return 0
    return 1 + count_tree_nodes(tree.get('left')) + count_tree_nodes(tree.get('right'))
