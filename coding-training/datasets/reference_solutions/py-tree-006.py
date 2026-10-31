def count_leaves(tree: dict | None) -> int:
    if not tree: return 0
    if tree.get('left') is None and tree.get('right') is None: return 1
    return count_leaves(tree.get('left')) + count_leaves(tree.get('right'))
