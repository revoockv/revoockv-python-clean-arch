"""HTTP status of every failure kind."""

from http import HTTPStatus

from example_app.core.domain.entities.failure_kind import FailureKind


class FailureStatus:
    """Maps a ``FailureKind`` to the HTTP status of the response, in one place for every router."""

    @staticmethod
    def of(kind: FailureKind) -> HTTPStatus:
        """Return the HTTP status that answers a failure of ``kind``."""
        match kind:
            case FailureKind.INVALID_INPUT:
                return HTTPStatus.UNPROCESSABLE_ENTITY
            case FailureKind.NOT_FOUND:
                return HTTPStatus.NOT_FOUND
            case FailureKind.CONFLICT:
                return HTTPStatus.CONFLICT
            case FailureKind.UNAUTHORIZED:
                return HTTPStatus.UNAUTHORIZED
            case FailureKind.FORBIDDEN:
                return HTTPStatus.FORBIDDEN
            case FailureKind.UNEXPECTED:
                return HTTPStatus.INTERNAL_SERVER_ERROR
