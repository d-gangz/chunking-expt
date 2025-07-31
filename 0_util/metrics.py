def calculate_mrr(output: list[str], expected: list[str]):
    mrr = 0
    for label in expected:
        if label in output:
            # Find the relevant item that has the smallest index
            mrr = max(mrr, 1 / (output.index(label) + 1))
    return mrr


def calculate_recall(output: list[str], expected: list[str]):
    # Calculate the proportion of relevant items that were retrieved
    return len([label for label in expected if label in output]) / len(expected)