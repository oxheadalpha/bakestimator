def text(result):
    output = [
        f"active rolls: {result['active_rolls']}",
        f"cycles: {result['cycles']}",
        "",
    ]
    for key in ["bakes", "endorsements", "total"]:
        output.append(key)
        col1 = "mean"
        col2 = "max"
        header = " " * 10 + f"{col1:>10} {col2:>10}"
        output.append("-" * len(header))
        output.append(header)
        d = result[key]
        for key2 in ["count", "deposits", "rewards"]:
            mean = d["mean"][key2]
            max = d["max"][key2]
            output.append(f"{key2:>8}: {mean:10.2f} {max:10.2f}")
        output.append("\n")
    return "\n".join(output)
