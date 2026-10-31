def evaluate_rpn(tokens: list[str]) -> int:
    stack = []
    for t in tokens:
        if t in '+-*/':
            b, a = stack.pop(), stack.pop()
            if t == '+': stack.append(a + b)
            elif t == '-': stack.append(a - b)
            elif t == '*': stack.append(a * b)
            elif t == '/': stack.append(int(a / b))
        else: stack.append(int(t))
    return stack[0] if stack else 0
