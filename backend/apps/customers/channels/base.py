from typing import Protocol


class CodeChannel(Protocol):
    name: str

    def send_code(self, phone: str, code: str) -> None:
        """Sends the code. Raises ProviderUnavailable if the provider is down."""
