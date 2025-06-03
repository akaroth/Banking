import requests
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError
# Assuming a custom exception class as before
from exceptions import ExchangeRateAPIError


class CurrencyConverter:
    # Assuming BASE_URL and api_key are defined in __init__
    BASE_URL = "https://v6.exchangerate-api.com/v6/"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _make_api_request(self, endpoint: str) -> dict:
        """
        Internal helper to make API requests. Raises ExchangeRateAPIError on any failure.
        Consolidates error handling and redacts sensitive information.
        """
        full_url = f'{self.BASE_URL}{self.api_key}{endpoint}'

        try:
            response = requests.get(full_url, timeout=10)
            # This is the first gate: raises HTTPError for 4xx/5xx responses
            response.raise_for_status()
            # The second gate: raises ValueError/JSONDecodeError if response isn't JSON
            data = response.json()

        except (RequestException, ValueError) as e:
            # This single block now catches all network, HTTP, and JSON decoding errors
            api_error_type = "unknown-request-error"
            user_message = f"An unexpected error occurred: {e}"
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else None

            if isinstance(e, HTTPError):
                api_error_type = "http-error"
                user_message = f"API request failed with HTTP Error {status_code}: {e.response.reason}."
                if status_code == 404:
                    user_message = "The requested currency or API endpoint was not found."
            elif isinstance(e, Timeout):
                api_error_type = "timeout"
                user_message = "The request to the currency API timed out."
            elif isinstance(e, ConnectionError):
                api_error_type = "network-error"
                user_message = "A network connection error occurred to the currency API."
            elif isinstance(e, ValueError): # Catches JSONDecodeError
                api_error_type = "json-decode-error"
                user_message = "Failed to decode the JSON response from the API."

            redacted_url = full_url.replace(self.api_key, '***REDACTED_API_KEY***')
            details = {"requested_url_redacted": redacted_url}

            raise ExchangeRateAPIError(
                message=user_message,
                api_error_type=api_error_type,
                http_status_code=status_code,
                details=details
            ) from e

        # --- If we get here, the request was successful and we have valid JSON ---
        # Now, we handle the API's own specific error messages.
        if data.get('result') == 'success':
            return data

        if data.get('result') == 'error':
            api_error_type = data.get('error-type', 'unknown-api-error')
            error_messages = {
                "unsupported-code": "Currency code not supported by API. Please check the currency code.",
                "invalid-key": "Invalid API key provided. Please check your API key.",
                "quota-reached": "API quota reached. Please try again later or upgrade your plan."
            }
            user_message = error_messages.get(api_error_type, f"Currency API returned an unhandled error: {api_error_type.replace('-', ' ').title()}.")

            raise ExchangeRateAPIError(
                message=user_message,
                api_error_type=api_error_type,
                http_status_code=response.status_code,
                details=data
            )

        # Handle cases where the 'result' key is neither 'success' nor 'error'
        raise ExchangeRateAPIError(
            message=f"Unexpected 'result' value in API response: {data.get('result')}.",
            http_status_code=response.status_code,
            api_error_type="unexpected-response-format",
            details=data
        )
    def get_exchange_rate(self, base_currency: str , target_currency: str) -> float:
            """
            Fetches the exchange rate. Raises ExchangeRateAPIError on failure.
            """
    pass
    # endpoint = f'/latest/{base_currency.upper()}'
    # data = self._make.api

if __name__ == "__main__":
    import os
    # Assume your classes are in currency_converter.py and exceptions.py
    # If they are in the same file, you might not need the .exceptions import
    from currency_converter import CurrencyConverter
    from exceptions import ExchangeRateAPIError

    print("\n--- Testing _make_api_request functionality with refined error handling ---")

    api_key_from_env = os.getenv("EXCHANGE_API")

    if not api_key_from_env:
        print("ERROR: EXCHANGE_API environment variable not set. Cannot run all tests.")
        print("Please get your API key from https://www.exchangerate-api.com/ and set it.")
        exit(1)

    # --- Standard Test Cases ---

    converter = CurrencyConverter(api_key_from_env)

    # Test Case 1: Successful Request
    print("\n[1] Attempting a successful request for USD latest rates...")
    try:
        usd_rates_data = converter._make_api_request("/latest/USD")
        print("SUCCESS: Successful response received for USD.")
        print(f"  Base currency: {usd_rates_data.get('base_code')}")
        print(f"  Conversion rate for EUR: {usd_rates_data.get('conversion_rates', {}).get('EUR')}")
    except ExchangeRateAPIError as e:
        print(f"FAILED (Unexpected): Caught API error: {e.message}")
        print(f"  Internal API Error Type: {e.api_error_type}, HTTP Status: {e.http_status_code}")

    # Test Case 2: API-Reported Error (Unsupported Currency)
    print("\n[2] Attempting a request with an unsupported base currency ('XXX')...")
    try:
        converter._make_api_request("/latest/XXX")
        print("FAILED (Unexpected): Request succeeded with unsupported currency 'XXX'.")
    except ExchangeRateAPIError as e:
        print(f"SUCCESS (Expected): Caught API error for unsupported currency: {e.message}")
        print(f"  Internal API Error Type: {e.api_error_type}, HTTP Status: {e.http_status_code}")

    # Test Case 3: API-Reported Error (Invalid API Key)
    print("\n[3] Attempting a request with a deliberately invalid API key...")
    try:
        bad_key_converter = CurrencyConverter("THIS_IS_A_FAKE_INVALID_KEY_123")
        bad_key_converter._make_api_request("/latest/USD")
        print("FAILED (Unexpected): Request succeeded with invalid key.")
    except ExchangeRateAPIError as e:
        print(f"SUCCESS (Expected): Caught API error for invalid key: {e.message}")
        print(f"  Internal API Error Type: {e.api_error_type}, HTTP Status: {e.http_status_code}")


    # --- Network and HTTP Error Test Cases ---

    # Test Case 4: HTTP 404 Not Found Error
    print("\n[4] Attempting a request to a non-existent API endpoint...")
    try:
        converter._make_api_request("/this-endpoint-does-not-exist/USD")
        print("FAILED (Unexpected): Request succeeded for a non-existent endpoint.")
    except ExchangeRateAPIError as e:
        print(f"SUCCESS (Expected): Caught HTTP error for non-existent endpoint: {e.message}")
        print(f"  Internal API Error Type: {e.api_error_type}, HTTP Status: {e.http_status_code}")

    # Test Case 5: Connection Error (e.g., DNS failure)
    print("\n[5] Attempting a request to a domain that does not exist...")
    # To simulate this, we'll create a temporary converter instance pointing to a fake URL
    try:
        connection_error_converter = CurrencyConverter(api_key_from_env)
        # Temporarily override the class attribute for this test
        connection_error_converter.BASE_URL = "http://this-domain-absolutely-does-not-exist.com/v6/"
        connection_error_converter._make_api_request("/latest/USD")
        print("FAILED (Unexpected): Request succeeded to a non-existent domain.")
    except ExchangeRateAPIError as e:
        print(f"SUCCESS (Expected): Caught connection error: {e.message}")
        print(f"  Internal API Error Type: {e.api_error_type}")
    finally:
        # It's good practice to restore the original value if you modify a class attribute
        CurrencyConverter.BASE_URL = "https://v6.exchangerate-api.com/v6/"

    # --- Conceptual Test Cases (Hard to simulate without mocking libraries) ---
    print("\n--- The following are conceptual tests for failures that are hard to trigger reliably ---")
    print("      To test these properly, a library like `requests-mock` is recommended.")
    print("  - Test Case 6: Timeout Error (Server doesn't respond in time)")
    print("  - Test Case 7: Invalid JSON Response (Server returns HTML error page instead of JSON)")


    print("\n--- Testing complete ---")