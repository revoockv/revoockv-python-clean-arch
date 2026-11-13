from example_app.core.domain.entities.result import Failure, Result, Success


def _describe(result: Result[int]) -> str:
    match result:
        case Success(value):
            return f"ok {value}"
        case Failure(error):
            return f"error {error}"


def test_result_pattern_matching() -> None:
    assert _describe(Success(1)) == "ok 1"
    assert _describe(Failure("boom")) == "error boom"
