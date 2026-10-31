from typing import Protocol


class CodeChannel(Protocol):
    name: str

    def send_code(self, phone: str, code: str) -> None:
        """Надсилає код. Кидає ProviderUnavailable, якщо провайдер недоступний."""
