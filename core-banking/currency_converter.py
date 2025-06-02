import requests, typing, os

from exceptions import ExchangeRateAPIError

class CurrencyConverter:

    """
    Handles fetching currency exchange rates from ExchangeRate-API.
    Raises ExchangeRateAPIError for all API-related issues.
    """

    BASE_URL = "https://v6.exchangerate-api.com/v6/"

    def __init__(self, api_key:str):
        self.api_key = api_key

    def _make_api_request(self, endpoint: str) -> dict: # Corrected method name (removed 's' from requests)
            """
            Internal helper to make API requests. Raises ExchangeRateAPIError on any failure.
            Includes key redaction for sensitive information in error details.
            """
            full_url = f'{self.BASE_URL}{self.api_key}{endpoint}'

            try:
                response = requests.get(full_url, timeout=10)
                response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
                data = response.json()

                if data.get('result') == 'error':
                    api_error_type = data.get('error-type', 'unknown-api-error') # Corrected default value for api_error_type

                    user_message = f"Currency API returned an error: {api_error_type.replace('-', ' ').title()}."
                    if api_error_type == "unsupported-code":
                        user_message = "Currency code not supported by API. Please check the currency code."
                    elif api_error_type == "invalid-key":
                        user_message = "Invalid API key provided. Please check your API key."
                    elif api_error_type == "quota-reached":
                        user_message = "API quota reached. Please try again later or upgrade your plan."

                    raise ExchangeRateAPIError(
                        message=user_message,
                        api_error_type=api_error_type,
                        http_status_code=response.status_code,
                        details=data
                    )
                elif data.get('result') == 'success':
                    return data
                else:
                    raise ExchangeRateAPIError(
                        message=f"Unexpected 'result' value from API: {data.get('result')}. Full response: {data}",
                        http_status_code=response.status_code,
                        details=data
                    )

            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else None
                reason = e.response.reason if e.response else "Unknown"

                user_message = f"Failed to connect to currency API. HTTP Error {status_code}: {reason}."
                if status_code == 404:
                    user_message = f"Currency data not found for the requested base currency. ({status_code})"

                redacted_url = None
                if hasattr(e.request, 'url') and e.request.url:
                    redacted_url = e.request.url.replace(self.api_key, '***REDACTED_API_KEY***')
                elif hasattr(e.response, 'url') and e.response.url:
                    redacted_url = e.response.url.replace(self.api_key, '***REDACTED_API_KEY***')

                details_dict = {"response_text": e.response.text if e.response else "N/A"}
                if redacted_url:
                    details_dict["requested_url_redacted"] = redacted_url

                raise ExchangeRateAPIError(
                    message=user_message,
                    http_status_code=status_code,
                    api_error_type="http-error",
                    details=details_dict
                ) from e

            except requests.exceptions.ConnectionError as e:
                raise ExchangeRateAPIError(f"Network connection error to currency API: {e}", api_error_type="network-error") from e

            except requests.exceptions.Timeout as e:
                raise ExchangeRateAPIError(f"Currency API request timed out: {e}", api_error_type="timeout") from e

            except requests.exceptions.RequestException as e:
                raise ExchangeRateAPIError(f"An unexpected request error occurred with currency API: {e}", api_error_type="unknown-request-error") from e

            except ValueError as e:
                response_text = response.response.text if hasattr(e, 'response') and e.response else "No response body"
                raise ExchangeRateAPIError(f"Failed to decode JSON from API response. {e}. Response: {response_text}", api_error_type="json-decode-error") from e

            except Exception as e:
                raise ExchangeRateAPIError(f"An unforeseen error occurred with currency API: {e}", api_error_type="unforeseen-error") from e

    def get_exchange_rate(self, base_currency: str , target_currency: str) -> float:
            """
            Fetches the exchange rate. Raises ExchangeRateAPIError on failure.
            """
    endpoint = f'/latest/{base_currency.upper()}'
    data = self._make.api

if __name__ == "__main__":
    print("\n--- Testing _make_api_request functionality with refined error handling ---")

    api_key_from_env = os.getenv("EXCHANGE_API")

    if not api_key_from_env:
        print("ERROR: EXCHANGE_API environment variable not set. Cannot run tests.")
        print("Please get your API key from https://www.exchangerate-api.com/ and set it.")
        exit(1)

    converter = CurrencyConverter(api_key_from_env)

    # --- Test Case 1: Successful Request ---
    print("\nAttempting a successful request for USD latest rates...")
    try:
        usd_rates_data = converter._make_api_requests("/latest/USD")
        print("SUCCESS: Successful response received for USD.")
        print(f"  Base currency: {usd_rates_data.get('base_code')}")
        print(f"  Conversion rates for EUR: {usd_rates_data.get('conversion_rates', {}).get('EUR')}")
    except ExchangeRateAPIError as e:
        # NOW YOU WILL ONLY SEE THIS MESSAGE, NO FULL TRACEBACK
        print(f"FAILED (Unexpected): Caught API error: {e.message}")
        print(f"  Internal API Error Type: {e.api_error_type}, HTTP Status: {e.http_status_code}")
    except Exception as e:
        print(f"FAILED (Unexpected): Caught general error: {e}")

    # --- Test Case 2: Invalid Base Currency (e.g., 'XXX') ---
    # This will now print your refined error message and no traceback
    print("\nAttempting a request with an unsupported base currency ('XXX')...")
    try:
        converter._make_api_requests("/latest/XXX")
        print("FAILED (Unexpected): Request succeeded with unsupported currency 'XXX'.")
    except ExchangeRateAPIError as e:
        # Expected to be caught here, printing refined message
        print(f"SUCCESS (Expected): Caught API error for unsupported currency: {e.message}")
        print(f"  Internal API Error Type: {e.api_error_type}, HTTP Status: {e.http_status_code}")
    except Exception as e:
        print(f"FAILED (Unexpected): Caught general error: {e}")

    # --- Test Case 3: Invalid API Key (Simulated) ---
    print("\nAttempting a request with a deliberately invalid API key...")
    try:
        bad_key_converter = CurrencyConverter("THIS_IS_A_FAKE_INVALID_KEY_123")
        bad_key_converter._make_api_requests("/latest/USD")
        print("FAILED (Unexpected): Request succeeded with invalid key.")
    except ExchangeRateAPIError as e:
        # Expected to be caught here, printing refined message
        print(f"SUCCESS (Expected): Caught API error for invalid key: {e.message}")
        print(f"  Internal API Error Type: {e.api_error_type}, HTTP Status: {e.http_status_code}")
    except ValueError as e:
        print(f"SUCCESS (Expected): Caught ValueError during bad key setup: {e}")
    except Exception as e:
        print(f"FAILED (Unexpected): Caught general error: {e}")

    print("\n--- _make_api_request testing complete ---")