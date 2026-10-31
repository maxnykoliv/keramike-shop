class CalcValidationError(ValueError):
    """A calculator input error with a field path, e.g. surfaces[0].openings."""

    def __init__(self, code: str, message: str, field: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field
