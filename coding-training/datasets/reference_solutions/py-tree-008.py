def graph_path_exists(adj: dict, src: int, dst: int) -> bool:
    adj_int = {int(k): v for k, v in adj.items()}
    if src == dst: return True
    visited = set()
    stack = [src]
    while stack:
        u = stack.pop()
        if u == dst: return True
        if u not in visited:
            visited.add(u)
            stack.extend(adj_int.get(u, []))
    return False
