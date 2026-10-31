from drf_spectacular.extensions import OpenApiAuthenticationExtension


class CustomerTokenScheme(OpenApiAuthenticationExtension):
    target_class = "apps.customers.authentication.CustomerTokenAuthentication"
    name = "customerToken"

    def get_security_definition(self, auto_schema):
        return {"type": "http", "scheme": "bearer",
                "description": "Токен сесії клієнта з /auth/telegram/poll або /auth/code/verify"}
