"""Expected application errors mapped to API and tool responses."""


class AppError(Exception):
    """An actionable client-facing error with an HTTP equivalent."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code

