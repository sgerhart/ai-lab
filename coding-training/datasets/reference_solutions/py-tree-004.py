def tree_to_inorder(tree: dict | None) -> list[int]:
    if not tree: return []
    return tree_to_inorder(tree.get('left')) + [tree.get('val', 0)] + tree_to_inorder(tree.get('right'))
