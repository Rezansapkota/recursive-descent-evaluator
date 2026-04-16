from __future__ import annotations

from pathlib import Path
from typing import Any


# -----------------------------
# Public function required by rubric
# -----------------------------
def evaluate_file("sample_input.txt") -> list[dict]:
    """
    Read one expression per line from the input file,
    evaluate each expression, write output.txt in the
    same folder, and return a list of dictionaries.
    """
    input_file = Path(input_path)
    output_file = input_file.with_name("output.txt")

    with input_file.open("r", encoding="utf-8") as file:
        lines = file.read().splitlines()

    results: list[dict] = []
    for line in lines:
        results.append(_process_line(line))

    _write_output_file(output_file, results)
    return results


# -----------------------------
# Main work for one line
# -----------------------------
def _process_line(expression: str) -> dict:
    """Tokenize, parse, evaluate, and package one expression."""
    try:
        tokens = _tokenize(expression)
        tree, value = _parse(tokens)

        return {
            "input": expression,
            "tree": _tree_to_string(tree),
            "tokens": _tokens_to_string(tokens),
            "result": float(value),
        }
    except Exception:
        return {
            "input": expression,
            "tree": "ERROR",
            "tokens": "ERROR",
            "result": "ERROR",
        }


# -----------------------------
# File output
# -----------------------------
def _write_output_file(output_path: Path, results: list[dict]) -> None:
    """Write the required four-line blocks to output.txt."""
    blocks: list[str] = []

    for item in results:
        if item["result"] == "ERROR":
            result_text = "ERROR"
        else:
            result_text = _format_number(item["result"])

        block = "\n".join(
            [
                f"Input: {item['input']}",
                f"Tree: {item['tree']}",
                f"Tokens: {item['tokens']}",
                f"Result: {result_text}",
            ]
        )
        blocks.append(block)

    with output_path.open("w", encoding="utf-8") as file:
        file.write("\n\n".join(blocks))


# -----------------------------
# Tokenizer
# -----------------------------
def _tokenize(text: str) -> list[dict[str, Any]]:
    """
    Convert the input string into tokens.

    Token types:
    - NUM
    - OP
    - LPAREN
    - RPAREN
    - END
    """
    tokens: list[dict[str, Any]] = []
    i = 0

    while i < len(text):
        ch = text[i]

        if ch.isspace():
            i += 1
            continue

        # Read a number, including decimals like 3.5 or .5
        if ch.isdigit() or ch == ".":
            start = i
            dot_count = 0

            while i < len(text) and (text[i].isdigit() or text[i] == "."):
                if text[i] == ".":
                    dot_count += 1
                i += 1

            number_text = text[start:i]

            if number_text == "." or dot_count > 1:
                raise ValueError("Invalid number")

            number_value = float(number_text)
            tokens.append(
                {
                    "type": "NUM",
                    "value": number_value,
                    "text": _format_number(number_value),
                }
            )
            continue

        if ch in "+-*/":
            tokens.append({"type": "OP", "value": ch})
            i += 1
            continue

        if ch == "(":
            tokens.append({"type": "LPAREN", "value": ch})
            i += 1
            continue

        if ch == ")":
            tokens.append({"type": "RPAREN", "value": ch})
            i += 1
            continue

        raise ValueError(f"Invalid character: {ch}")

    tokens.append({"type": "END", "value": ""})
    return tokens


# -----------------------------
# Recursive descent parser
# -----------------------------
def _parse(tokens: list[dict[str, Any]]) -> tuple[dict[str, Any], float]:
    """
    Grammar used:

    expression -> term ((+|-) term)*
    term       -> factor ((*|/) factor | implicit_multiplication factor)*
    factor     -> - factor | NUM | ( expression )

    Unary + is not supported and causes an error.
    """
    index = 0

    def current() -> dict[str, Any]:
        return tokens[index]

    def advance() -> dict[str, Any]:
        nonlocal index
        token = tokens[index]
        index += 1
        return token

    def parse_expression() -> tuple[dict[str, Any], float]:
        """Handle + and - (lowest precedence)."""
        left_node, left_value = parse_term()

        while current()["type"] == "OP" and current()["value"] in {"+", "-"}:
            op = advance()["value"]
            right_node, right_value = parse_term()

            if op == "+":
                left_value = left_value + right_value
            else:
                left_value = left_value - right_value

            left_node = {
                "kind": "binary",
                "op": op,
                "left": left_node,
                "right": right_node,
            }

        return left_node, left_value

    def parse_term() -> tuple[dict[str, Any], float]:
        """Handle *, /, and implicit multiplication."""
        left_node, left_value = parse_factor()

        while True:
            token = current()

            # Normal multiplication or division
            if token["type"] == "OP" and token["value"] in {"*", "/"}:
                op = advance()["value"]
                right_node, right_value = parse_factor()

                if op == "*":
                    left_value = left_value * right_value
                else:
                    left_value = left_value / right_value

                left_node = {
                    "kind": "binary",
                    "op": op,
                    "left": left_node,
                    "right": right_node,
                }
                continue

            # Implicit multiplication: 2(3+4), (1+2)(3+4)
            if token["type"] in {"NUM", "LPAREN"}:
                right_node, right_value = parse_factor()
                left_value = left_value * right_value
                left_node = {
                    "kind": "binary",
                    "op": "*",
                    "left": left_node,
                    "right": right_node,
                }
                continue

            break

        return left_node, left_value

    def parse_factor() -> tuple[dict[str, Any], float]:
        """Handle numbers, parentheses, and unary negation."""
        token = current()

        # Unary plus must be rejected
        if token["type"] == "OP" and token["value"] == "+":
            raise ValueError("Unary plus is not supported")

        # Unary negation
        if token["type"] == "OP" and token["value"] == "-":
            advance()
            operand_node, operand_value = parse_factor()
            return {"kind": "neg", "operand": operand_node}, -operand_value

        # Number
        if token["type"] == "NUM":
            advance()
            return {"kind": "num", "value": token["value"]}, token["value"]

        # Parenthesized expression
        if token["type"] == "LPAREN":
            advance()
            node, value = parse_expression()

            if current()["type"] != "RPAREN":
                raise ValueError("Missing closing parenthesis")

            advance()
            return node, value

        raise ValueError("Expected a number, unary -, or (")

    tree, value = parse_expression()

    if current()["type"] != "END":
        raise ValueError("Unexpected extra input")

    return tree, value


# -----------------------------
# Tree formatting
# -----------------------------
def _tree_to_string(node: dict[str, Any]) -> str:
    """Convert the parse tree into the required rubric format."""
    if node["kind"] == "num":
        return _format_number(node["value"])

    if node["kind"] == "neg":
        return f"(neg {_tree_to_string(node['operand'])})"

    if node["kind"] == "binary":
        return (
            f"({node['op']} "
            f"{_tree_to_string(node['left'])} "
            f"{_tree_to_string(node['right'])})"
        )

    raise ValueError("Unknown tree node")


# -----------------------------
# Token formatting
# -----------------------------
def _tokens_to_string(tokens: list[dict[str, Any]]) -> str:
    """Convert tokens into the required [TYPE:value] format."""
    parts: list[str] = []

    for token in tokens:
        if token["type"] == "NUM":
            parts.append(f"[NUM:{token['text']}]")
        elif token["type"] == "OP":
            parts.append(f"[OP:{token['value']}]")
        elif token["type"] == "LPAREN":
            parts.append("[LPAREN:(]")
        elif token["type"] == "RPAREN":
            parts.append("[RPAREN:)]")
        elif token["type"] == "END":
            parts.append("[END]")

    return " ".join(parts)


# -----------------------------
# Number formatting
# -----------------------------
def _format_number(value: float) -> str:
    """
    Show whole numbers without .0.
    Otherwise round to 4 decimal places.
    """
    rounded = round(float(value), 4)

    # Avoid showing -0
    if rounded == 0:
        rounded = 0.0

    if rounded.is_integer():
        return str(int(rounded))

    return f"{rounded:.4f}".rstrip("0").rstrip(".")