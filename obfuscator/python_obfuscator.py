import ast
import random
import string
from .utils import random_name

class PythonObfuscator:
    def __init__(self, code: str, level="hard"):
        self.code = code
        self.level = level
        self.name_map = {}

    def _generate_name(self):
        return random_name()

    def _should_rename(self, name):
        # Never rename built-ins or special names
        protected = {
            'print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple',
            'open', 'input', 'range', 'enumerate', 'zip', 'map', 'filter', 'sum', 'min', 'max',
            'import', 'from', 'def', 'class', 'if', 'else', 'elif', 'for', 'while', 'return',
            'try', 'except', 'finally', 'with', 'as', 'pass', 'break', 'continue', 'lambda',
            '__init__', '__name__', '__file__', '__main__'
        }
        return name not in protected and len(name) > 1 and name[0] != '_'

    def obfuscate(self) -> str:
        if self.level == "easy":
            return self._simple_obfuscate()
        else:
            return self._ast_obfuscate()

    def _simple_obfuscate(self):
        # Just add a header — no risky renaming
        return "# Obfuscated by KoalaHub\n" + self.code

    def _ast_obfuscate(self):
        try:
            tree = ast.parse(self.code)
            Renamer(self.name_map, self._should_rename, self._generate_name).visit(tree)
            return "# Obfuscated by KoalaHub (Protected_by_KoalaHub)\n" + ast.unparse(tree)
        except:
            # Fallback if AST fails
            return "# Obfuscated by KoalaHub\n" + self.code

class Renamer(ast.NodeTransformer):
    def __init__(self, name_map, should_rename, generate_name):
        self.name_map = name_map
        self.should_rename = should_rename
        self.generate_name = generate_name

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store) and self.should_rename(node.id):
            if node.id not in self.name_map:
                self.name_map[node.id] = self.generate_name()
            node.id = self.name_map[node.id]
        elif isinstance(node.ctx, ast.Load) and node.id in self.name_map:
            node.id = self.name_map[node.id]
        return node

    def visit_FunctionDef(self, node):
        if self.should_rename(node.name):
            if node.name not in self.name_map:
                self.name_map[node.name] = self.generate_name()
            node.name = self.name_map[node.name]
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node):
        if self.should_rename(node.name):
            if node.name not in self.name_map:
                self.name_map[node.name] = self.generate_name()
            node.name = self.name_map[node.name]
        self.generic_visit(node)
        return node