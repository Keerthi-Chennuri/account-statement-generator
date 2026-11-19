"""A small API error type used across the routes."""


class ApiError(Exception):
    """Raised when a request cannot be completed.

    status_code 400/401/403/404/409/422 are returned as JSON:
    {"error": "message", "fields": {"field": "message"}}
    """

    def __init__(self, message, status_code=400, fields=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.fields = fields or {}
