import ast
import operator
from .schemas import ToolInput, ToolOutput

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod, ast.USub: operator.neg, ast.UAdd: operator.pos}


def calculate(payload: ToolInput) -> ToolOutput:
    """Pydantic-validated, side-effect-free arithmetic tool."""
    def visit(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](visit(node.operand))
        raise ValueError("Sólo se aceptan números y operadores aritméticos.")
    return ToolOutput(
    result=visit(ast.parse(payload.expression.strip(), mode="eval").body)
)
