from rest_framework import authentication, exceptions

from apps.customers import services


class CustomerTokenAuthentication(authentication.BaseAuthentication):
    """Authorization: Bearer <customer session token>. No header means an anonymous request."""

    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode(errors="ignore")
        if not header:
            return None
        parts = header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            raise exceptions.AuthenticationFailed("Некоректний заголовок авторизації")
        session = services.authenticate_token(parts[1])
        if session is None:
            raise exceptions.AuthenticationFailed("Сесія завершилась, увійдіть знову")
        return session.customer, session

    def authenticate_header(self, request) -> str:
        return self.keyword
