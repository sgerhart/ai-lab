def sum_tree_values(tree: dict | None) -> int:
    if not tree: return 0
    return tree.get('val', 0) + sum_tree_values(tree.get('left')) + sum_tree_values(tree.get('right'))
