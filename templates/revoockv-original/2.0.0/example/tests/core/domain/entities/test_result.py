from enum import Enum, auto

from example_app.core.domain.entities.result import Failure, Result, Success


class _Failure(Enum):
    BROKEN = auto()


def _describe(result: Result[int, _Failure]) -> str:
    match result:
        case Success(value):
            return f"ok {value}"
        case Failure(failure):
            return f"failed {failure.name}"


def test_result_pattern_matching() -> None:
    assert _describe(Success(1)) == "ok 1"
    assert _describe(Failure(_Failure.BROKEN)) == "failed BROKEN"
