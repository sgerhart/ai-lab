def count_connected_components(n: int, edges: list[list[int]]) -> int:
    adj = {i: [] for i in range(n)}
    for u, v in edges: adj[u].append(v); adj[v].append(u)
    visited = set()
    count = 0
    for i in range(n):
        if i not in visited:
            count += 1; q = [i]
            while q:
                curr = q.pop()
                if curr not in visited:
                    visited.add(curr); q.extend(adj[curr])
    return count
