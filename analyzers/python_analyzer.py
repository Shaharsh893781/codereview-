import ast
import hashlib
import io
import tokenize
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from analyzers.base import CodeAnalyzer
from models.schemas import AnalysisResult, Issue, ScoreCard


COMPLEXITY_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.ExceptHandler,
    ast.BoolOp,
    ast.IfExp,
    ast.Match,
    ast.comprehension,
)


@dataclass
class FunctionMetrics:
    name: str
    line: int
    length: int
    params: int
    complexity: int
    max_depth: int


class PythonAnalyzer(CodeAnalyzer):
    language = "python"

    def analyze(self, code: str, filename: str) -> AnalysisResult:
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            issue = Issue(
                line=exc.lineno or 1,
                column=exc.offset or 0,
                rule="syntax-error",
                severity="critical",
                message=exc.msg,
                suggestion="Fix the syntax error before running deeper code review.",
            )
            scores = ScoreCard(
                cyclomatic_complexity=100,
                maintainability_score=0,
                readability_score=0,
                quality_score=0,
            )
            return AnalysisResult(
                filename=filename,
                language=self.language,
                issues=[issue],
                duplicate_blocks=[],
                ai_suggestions=["Resolve parser errors so static analysis can inspect the module."],
                scores=scores,
                metrics={"lines": len(code.splitlines())},
            )

        issues: list[Issue] = []
        functions = self._function_metrics(tree)
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        assigned, used = self._names(tree)
        duplicate_blocks = self._duplicate_blocks(tree)
        line_count = len(code.splitlines())
        comment_ratio = self._comment_ratio(code)

        for fn in functions:
            if fn.length > 50:
                issues.append(Issue(line=fn.line, rule="long-function", severity="major", message=f"Function '{fn.name}' has {fn.length} lines.", suggestion="Extract cohesive helper functions and keep each function focused on one responsibility."))
            if fn.params > 5:
                issues.append(Issue(line=fn.line, rule="too-many-parameters", severity="major", message=f"Function '{fn.name}' has {fn.params} parameters.", suggestion="Use a dataclass/config object or split the function into smaller commands."))
            if fn.max_depth > 3:
                issues.append(Issue(line=fn.line, rule="deep-nesting", severity="major", message=f"Function '{fn.name}' reaches nesting depth {fn.max_depth}.", suggestion="Use guard clauses, early returns, and smaller helpers to flatten control flow."))
            if not self._is_snake_case(fn.name):
                issues.append(Issue(line=fn.line, rule="naming-convention", severity="minor", message=f"Function '{fn.name}' should use snake_case.", suggestion="Rename the function using lower_snake_case for Python readability."))
            if fn.complexity > 10:
                issues.append(Issue(line=fn.line, rule="high-complexity", severity="critical", message=f"Function '{fn.name}' has cyclomatic complexity {fn.complexity}.", suggestion="Split branching logic into strategy functions or smaller decision units."))

        for cls in classes:
            class_len = self._node_length(cls)
            method_count = sum(isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) for item in cls.body)
            if class_len > 300 or method_count > 15:
                issues.append(Issue(line=cls.lineno, rule="large-class", severity="major", message=f"Class '{cls.name}' is large ({class_len} lines, {method_count} methods).", suggestion="Separate data, orchestration, and infrastructure responsibilities into smaller classes."))
            if not cls.name[:1].isupper():
                issues.append(Issue(line=cls.lineno, rule="naming-convention", severity="minor", message=f"Class '{cls.name}' should use PascalCase.", suggestion="Rename classes with PascalCase to follow PEP 8 conventions."))

        for name, line in sorted(assigned.items()):
            if name not in used and not name.startswith("_"):
                issues.append(Issue(line=line, rule="unused-variable", severity="minor", message=f"Variable '{name}' is assigned but never used.", suggestion="Remove it or use it in the intended calculation."))

        for duplicate in duplicate_blocks:
            issues.append(Issue(line=duplicate["first_line"], rule="duplicate-logic", severity="major", message="Similar logic appears in multiple places.", suggestion="Extract the repeated logic into a shared helper."))

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
                issues.append(Issue(line=node.lineno, rule="security-risk", severity="critical", message=f"Use of {node.func.id} can execute untrusted code.", suggestion="Replace dynamic execution with explicit parsing or a safe command map."))
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append(Issue(line=node.lineno, rule="broad-except", severity="major", message="Bare except catches every exception, including system-exiting errors.", suggestion="Catch specific exception types and handle only expected failures."))

        total_complexity = sum(fn.complexity for fn in functions) or 1
        scores = self._scores(issues, total_complexity, line_count, comment_ratio)
        metrics = {
            "lines": line_count,
            "functions": len(functions),
            "classes": len(classes),
            "comment_ratio": comment_ratio,
            "average_function_length": round(sum(f.length for f in functions) / max(len(functions), 1), 2),
            "complexity_by_function": [{"name": f.name, "line": f.line, "complexity": f.complexity} for f in functions],
            "severity_counts": dict(Counter(issue.severity for issue in issues)),
        }
        return AnalysisResult(
            filename=filename,
            language=self.language,
            issues=issues,
            duplicate_blocks=duplicate_blocks,
            ai_suggestions=[],
            scores=scores,
            metrics=metrics,
        )

    def _function_metrics(self, tree: ast.AST) -> list[FunctionMetrics]:
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(FunctionMetrics(
                    name=node.name,
                    line=node.lineno,
                    length=self._node_length(node),
                    params=len(node.args.args) + len(node.args.kwonlyargs),
                    complexity=self._complexity(node),
                    max_depth=self._max_depth(node),
                ))
        return functions

    def _node_length(self, node: ast.AST) -> int:
        return max((getattr(node, "end_lineno", getattr(node, "lineno", 1)) or 1) - (getattr(node, "lineno", 1) or 1) + 1, 1)

    def _complexity(self, node: ast.AST) -> int:
        return 1 + sum(isinstance(child, COMPLEXITY_NODES) for child in ast.walk(node))

    def _max_depth(self, node: ast.AST) -> int:
        branch_nodes = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith, ast.Match)

        def walk(current: ast.AST, depth: int) -> int:
            next_depth = depth + 1 if isinstance(current, branch_nodes) else depth
            child_depths = [walk(child, next_depth) for child in ast.iter_child_nodes(current)]
            return max([next_depth, *child_depths])

        return walk(node, 0)

    def _names(self, tree: ast.AST) -> tuple[dict[str, int], set[str]]:
        assigned: dict[str, int] = {}
        used: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    assigned.setdefault(node.id, node.lineno)
                elif isinstance(node.ctx, ast.Load):
                    used.add(node.id)
            elif isinstance(node, ast.arg):
                used.add(node.arg)
        return assigned, used

    def _duplicate_blocks(self, tree: ast.AST) -> list[dict[str, Any]]:
        seen: dict[str, int] = {}
        duplicates = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.FunctionDef)):
                normalized = ast.dump(node, include_attributes=False)
                if len(normalized) < 140:
                    continue
                digest = hashlib.sha256(normalized.encode()).hexdigest()
                if digest in seen:
                    duplicates.append({"first_line": seen[digest], "duplicate_line": getattr(node, "lineno", 1), "fingerprint": digest[:12]})
                else:
                    seen[digest] = getattr(node, "lineno", 1)
        return duplicates[:10]

    def _comment_ratio(self, code: str) -> float:
        comments = 0
        try:
            tokens = tokenize.generate_tokens(io.StringIO(code).readline)
            comments = sum(1 for token in tokens if token.type == tokenize.COMMENT)
        except tokenize.TokenError:
            pass
        return round(comments / max(len(code.splitlines()), 1), 3)

    def _is_snake_case(self, name: str) -> bool:
        return name.islower() and ("-" not in name) and not name.startswith("__")

    def _scores(self, issues: list[Issue], complexity: int, lines: int, comment_ratio: float) -> ScoreCard:
        severity_weight = {"info": 1, "minor": 3, "major": 7, "critical": 13}
        issue_penalty = sum(severity_weight[issue.severity] for issue in issues)
        complexity_penalty = min(complexity * 1.8, 35)
        size_penalty = 8 if lines > 500 else 0
        maintainability = max(0, 100 - issue_penalty - complexity_penalty - size_penalty)
        readability = max(0, 100 - issue_penalty * 0.7 - (0 if comment_ratio >= 0.03 else 6))
        quality = max(0, round((maintainability * 0.45) + (readability * 0.35) + (max(0, 100 - complexity_penalty) * 0.2), 2))
        return ScoreCard(
            cyclomatic_complexity=float(complexity),
            maintainability_score=round(maintainability, 2),
            readability_score=round(readability, 2),
            quality_score=quality,
        )
