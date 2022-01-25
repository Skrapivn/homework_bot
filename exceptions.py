class ServerApiError(Exception):
    """Ошибка при недоступности Сервера API."""

    pass


class ApiResponseError(TypeError, KeyError):
    """Неверный формат ответа API."""

    pass
