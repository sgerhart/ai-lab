def graph_node_degree(adj: dict, node: int) -> int:
    adj_int = {int(k): v for k, v in adj.items()}
    return len(adj_int.get(node, []))
