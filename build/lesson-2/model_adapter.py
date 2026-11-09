from pathlib import Path


class FixtureModel:
    """Offline model adapter that returns one fixture per model response."""

    def __init__(self, response_paths: list[Path]) -> None:
        if not response_paths:
            raise ValueError("at least one response fixture is required")

        self._responses = [
            path.read_text(encoding="utf-8") for path in response_paths
        ]
        self._index = 0

    def initial_response(self) -> str:
        return self._next_response()

    def repair_response(self, repair_request: str) -> str:
        print("REPAIR REQUEST:")
        print(repair_request)
        return self._next_response()

    def _next_response(self) -> str:
        if self._index >= len(self._responses):
            raise RuntimeError(
                "fixture model has no response left for the next attempt"
            )

        response = self._responses[self._index]
        self._index += 1
        return response
