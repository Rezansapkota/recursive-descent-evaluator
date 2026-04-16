from pathlib import Path


# ----------------------------------------
# Main function required by assignment
# ----------------------------------------
def evaluate_file(input_path: str) -> list[dict]:
    # Get input file and create output.txt in same folder
    input_file = Path(input_path)
    output_file = input_file.parent / "output.txt"

    # Read all lines (each line = one expression)
    with open(input_file, "r") as f:
        lines = f.read().splitlines()

    results = []

    # Process each expression
    for line in lines:
        results.append(process_expression(line))

    # Write final output file
    write_output(output_file, results)

    return results


# ----------------------------------------
# Process one expression
# ----------------------------------------
def process_expression(expression: str) -> dict:
    try:
        # Step 1: convert to tokens
        tokens = tokenize(expression)

        # Parser state (tokens + position)
        parser = {"tokens": tokens, "pos": 0}

        # Step 2: parse and evaluate
        tree, value = parse_expression(parser)

        # Make sure no extra tokens remain
        if current(parser)["type"] != "END":
            raise Exception()

        return {
            "input": expression,
            "tree": tree_to_string(tree),
            "tokens": tokens_to_string(tokens),
            "result": float(value),
        }

    # If any error occurs → return ERROR block
    except Exception:
        return {
            "input": expression,
            "tree": "ERROR",
            "tokens": "ERROR",
            "result": "ERROR",
        }


# ----------------------------------------
# Write output.txt in required format
# ----------------------------------------
def write_output(path, results):
    blocks = []

    for r in results:
        # Format result value
        if r["result"] == "ERROR":
            res = "ERROR"
        else:
            res = format_number(r["result"])

        # Create 4-line block
        block = "\n".join([
            f"Input: {r['input']}",
            f"Tree: {r['tree']}",
            f"Tokens: {r['tokens']}",
            f"Result: {res}"
        ])
        blocks.append(block)

    # Separate blocks with blank line
    with open(path, "w") as f:
        f.write("\n\n".join(blocks))


# ----------------------------------------
# TOKENIZER (break input into tokens)
# ----------------------------------------
def tokenize(text):
    tokens = []
    i = 0

    while i < len(text):
        ch = text[i]

        # Ignore spaces
        if ch.isspace():
            i += 1
            continue

        # Read number (including decimals)
        if ch.isdigit() or ch == ".":
            start = i
            dot = 0

            while i < len(text) and (text[i].isdigit() or text[i] == "."):
                if text[i] == ".":
                    dot += 1
                i += 1

            num = text[start:i]

            # Invalid number check
            if num == "." or dot > 1:
                raise Exception()

            val = float(num)

            # Store number token
            tokens.append({
                "type": "NUM",
                "value": val,
                "text": format_number(val)
            })
            continue

        # Operators
        if ch in "+-*/":
            tokens.append({"type": "OP", "value": ch})
            i += 1
            continue

        # Left bracket
        if ch == "(":
            tokens.append({"type": "LPAREN"})
            i += 1
            continue

        # Right bracket
        if ch == ")":
            tokens.append({"type": "RPAREN"})
            i += 1
            continue

        # Invalid character
        raise Exception()

    # End token
    tokens.append({"type": "END"})
    return tokens


# ----------------------------------------
# PARSER HELPERS
# ----------------------------------------
def current(p):
    return p["tokens"][p["pos"]]


def advance(p):
    t = p["tokens"][p["pos"]]
    p["pos"] += 1
    return t


# ----------------------------------------
# expression → handles + and -
# ----------------------------------------
def parse_expression(p):
    left, val = parse_term(p)

    while current(p)["type"] == "OP" and current(p)["value"] in "+-":
        op = advance(p)["value"]
        right, rval = parse_term(p)

        # Perform calculation
        val = val + rval if op == "+" else val - rval

        # Build tree node
        left = {"k": "bin", "op": op, "l": left, "r": right}

    return left, val


# ----------------------------------------
# term → handles *, / and implicit *
# ----------------------------------------
def parse_term(p):
    left, val = parse_factor(p)

    while True:
        t = current(p)

        # Normal multiplication or division
        if t["type"] == "OP" and t["value"] in "*/":
            op = advance(p)["value"]
            right, rval = parse_factor(p)

            val = val * rval if op == "*" else val / rval

            left = {"k": "bin", "op": op, "l": left, "r": right}
            continue

        # Implicit multiplication (e.g. 2(3+4))
        if t["type"] in ["NUM", "LPAREN"]:
            right, rval = parse_factor(p)

            val = val * rval
            left = {"k": "bin", "op": "*", "l": left, "r": right}
            continue

        break

    return left, val


# ----------------------------------------
# factor → numbers, (), unary -
# ----------------------------------------
def parse_factor(p):
    t = current(p)

    # Unary + is not allowed
    if t["type"] == "OP" and t["value"] == "+":
        raise Exception()

    # Unary negation
    if t["type"] == "OP" and t["value"] == "-":
        advance(p)
        node, val = parse_factor(p)
        return {"k": "neg", "v": node}, -val

    # Number
    if t["type"] == "NUM":
        advance(p)
        return {"k": "num", "v": t["value"]}, t["value"]

    # Parentheses
    if t["type"] == "LPAREN":
        advance(p)
        node, val = parse_expression(p)

        if current(p)["type"] != "RPAREN":
            raise Exception()

        advance(p)
        return node, val

    raise Exception()


# ----------------------------------------
# Convert tree to required format
# ----------------------------------------
def tree_to_string(t):
    if t["k"] == "num":
        return format_number(t["v"])

    if t["k"] == "neg":
        return f"(neg {tree_to_string(t['v'])})"

    if t["k"] == "bin":
        return f"({t['op']} {tree_to_string(t['l'])} {tree_to_string(t['r'])})"


# ----------------------------------------
# Convert tokens to output format
# ----------------------------------------
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


# ----------------------------------------
# Format numbers (important for rubric)
# ----------------------------------------
def format_number(x):
    x = round(float(x), 4)

    if x == 0:
        x = 0.0

    if x.is_integer():
        return str(int(x))

    return str(x)


# ----------------------------------------
# RUN PROGRAM (CHANGE FILE NAME HERE)
# ----------------------------------------
if __name__ == "__main__":
    evaluate_file("sample_input.txt")   #  put your file name here like we put the' sample_input.txt' given in assignment