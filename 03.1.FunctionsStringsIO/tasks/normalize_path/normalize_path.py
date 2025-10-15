def normalize_path(path: str) -> str:
    """
    :param path: unix path to normalize
    :return: normalized path
    """
    is_abs = path.startswith('/')

    parts = path.split('/')
    stack = []

    for p in parts:
        if p == '' or p == '.':
            continue
        if p == '..':
            if stack and stack[-1] != '..':
                stack.pop()
            else:
                if not is_abs:
                    stack.append('..')
        else:
            stack.append(p)

    if is_abs:
        return '/' + '/'.join(stack)
    else:
        return '/'.join(stack) if stack else '.'
