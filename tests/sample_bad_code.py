def BadFunctionName(items, threshold, mode, user, debug, retries):
    result = []
    unused_value = 42
    for item in items:
        if item:
            if item.get("score", 0) > threshold:
                if mode == "fast":
                    result.append(item)
                else:
                    result.append(item)
    return result
