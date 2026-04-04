class AppError(Exception):
    """项目级业务异常，统一交给 API 层转换为标准错误响应。"""

    def __init__(self, message: str, *, code: str = "app_error", status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
