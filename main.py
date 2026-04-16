from pathlib import Path


def evaluate_file(input_path: str) -> list[dict]:
    input_file = Path(input_path)
    output_file = input_file.parent / "output.txt"

    with open(input_file, "r") as f:
        lines = f.read().splitlines()

    results = []

    for line in lines:
        results.append(process_expression(line))

    write_output(output_file, results)
    return results


def process_expression(expression: str) -> dict:
    try:
        tokens = tokenize(expression)
        parser = {"tokens": tokens, "pos": 0}

        tree, value = parse_expression(parser)

        if current(parser)["type"] != "END":
            raise Exception()

        return {
            "input": expression,
            "tree": tree_to_string(tree),
            "tokens": tokens_to_string(tokens),
            "result": float(value),
        }

    except Exception:
        return {
            "input": expression,
            "tree": "ERROR",
            "tokens": "ERROR",
            "result": "ERROR",
        }


def write_output(path, results):
    blocks = []

    for r in results:
        if r["result"] == "ERROR":
            res = "ERROR"
        else:
            res = format_number(r["result"])

        block = "\n".join([
            f"Input: {r['input']}",
            f"Tree: {r['tree']}",
            f"Tokens: {r['tokens']}",
            f"Result: {res}"
        ])
        blocks.append(block)

    with open(path, "w") as f:
        f.write("\n\n".join(blocks))


# ---------- TOKENIZER ----------

def tokenize(text):
    tokens = []
    i = 0

    while i < len(text):
        ch = text[i]

        if ch.isspace():
            i += 1
            continue

        if ch.isdigit() or ch == ".":
            start = i
            dot = 0

            while i < len(text) and (text[i].isdigit() or text[i] == "."):
                if text[i] == ".":
                    dot += 1
                i += 1

            num = text[start:i]
            if num == "." or dot > 1:
                raise Exception()

            val = float(num)
            tokens.append({"type": "NUM", "value": val, "text": format_number(val)})
            continue

        if ch in "+-*/":
            tokens.append({"type": "OP", "value": ch})
            i += 1
            continue

        if ch == "(":
            tokens.append({"type": "LPAREN"})
            i += 1
            continue

        if ch == ")":
            tokens.append({"type": "RPAREN"})
            i += 1
            continue

        raise Exception()

    tokens.append({"type": "END"})
    return tokens


# ---------- PARSER ----------

def current(p):
    return p["tokens"][p["pos"]]


def advance(p):
    t = p["tokens"][p["pos"]]
    p["pos"] += 1
    return t


def parse_expression(p):
    left, val = parse_term(p)

    while current(p)["type"] == "OP" and current(p)["value"] in "+-":
        op = advance(p)["value"]
        right, rval = parse_term(p)

        val = val + rval if op == "+" else val - rval
        left = {"k": "bin", "op": op, "l": left, "r": right}

    return left, val


def parse_term(p):
    left, val = parse_factor(p)

    while True:
        t = current(p)

        if t["type"] == "OP" and t["value"] in "*/":
            op = advance(p)["value"]
            right, rval = parse_factor(p)

            val = val * rval if op == "*" else val / rval
            left = {"k": "bin", "op": op, "l": left, "r": right}
            continue

        # implicit multiplication
        if t["type"] in ["NUM", "LPAREN"]:
            right, rval = parse_factor(p)
            val = val * rval
            left = {"k": "bin", "op": "*", "l": left, "r": right}
            continue

        break

    return left, val


def parse_factor(p):
    t = current(p)

    if t["type"] == "OP" and t["value"] == "+":
        raise Exception()

    if t["type"] == "OP" and t["value"] == "-":
        advance(p)
        node, val = parse_factor(p)
        return {"k": "neg", "v": node}, -val

    if t["type"] == "NUM":
        advance(p)
        return {"k": "num", "v": t["value"]}, t["value"]

    if t["type"] == "LPAREN":
        advance(p)
        node, val = parse_expression(p)

        if current(p)["type"] != "RPAREN":
            raise Exception()

        advance(p)
        return node, val

    raise Exception()


# ---------- OUTPUT HELPERS ----------

def tree_to_string(t):
    if t["k"] == "num":
        return format_number(t["v"])
    if t["k"] == "neg":
        return f"(neg {tree_to_string(t['v'])})"
    if t["k"] == "bin":
        return f"({t['op']} {tree_to_string(t['l'])} {tree_to_string(t['r'])})"


def tokens_to_string(tokens):
    out = []

    for t in tokens:
        if t["type"] == "NUM":
            out.append(f"[NUM:{t['text']}]")
        elif t["type"] == "OP":
            out.append(f"[OP:{t['value']}]")
        elif t["type"] == "LPAREN":
            out.append("[LPAREN:(]")
        elif t["type"] == "RPAREN":
            out.append("[RPAREN:)]")
        elif t["type"] == "END":
            out.append("[END]")

    return " ".join(out)


def format_number(x):
    x = round(float(x), 4)

    if x == 0:
        x = 0.0

    if x.is_integer():
        return str(int(x))

    return str(x)



if __name__ == "__main__":
    evaluate_file("sample_input.txt")   