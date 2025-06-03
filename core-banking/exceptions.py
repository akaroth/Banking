import typing
class ExchangeRateAPIError(Exception):

    """
    Base exception for all external API errors related to ExchangeRate-API.
    Details from the API response (error type, status code, full details)
    are passed as attributes for logging or specific handling.
    """

    def __init__(self, message: str, api_error_type: typing.Optional[str]= None, http_status_code: typing.Optional[int] = None,
                 details: typing.Optional[dict] = None):
        super().__init__(message)
        self.api_error_type = api_error_type
        self.http_status_code = http_status_code
        self.details = details
        self.message = message