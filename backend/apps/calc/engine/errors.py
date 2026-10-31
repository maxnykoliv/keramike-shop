class CalcValidationError(ValueError):
    """Помилка вводу калькулятора з шляхом до поля, напр. surfaces[0].openings."""

    def __init__(self, code: str, message: str, field: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field
