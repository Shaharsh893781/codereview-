from pathlib import Path

from analyzers.python_analyzer import PythonAnalyzer


def test_python_analyzer_detects_common_code_smells():
    code = Path("tests/sample_bad_code.py").read_text(encoding="utf-8")
    result = PythonAnalyzer().analyze(code, "sample_bad_code.py")
    rules = {issue.rule for issue in result.issues}

    assert "naming-convention" in rules
    assert "too-many-parameters" in rules
    assert "unused-variable" in rules
    assert result.scores.quality_score < 100


def test_python_analyzer_reports_syntax_errors():
    result = PythonAnalyzer().analyze("def broken(:\n    pass", "broken.py")

    assert result.issues[0].rule == "syntax-error"
    assert result.scores.quality_score == 0
