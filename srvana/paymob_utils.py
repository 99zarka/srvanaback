import requests
import os
import hashlib
import hmac
from django.conf import settings

# Paymob API Configurations
PAYMOB_API_BASE = "https://accept.paymob.com/api"

def get_auth_token():
    """
    Authenticate with Paymob and retrieve an auth token.
    """
    api_key = os.environ.get('PAYMOB_API_KEY')
    if not api_key:
        raise ValueError("PAYMOB_API_KEY environment variable is not set.")

    url = f"{PAYMOB_API_BASE}/auth/tokens"
    payload = {"api_key": api_key}
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json().get("token")

def register_order(auth_token, amount_cents, merchant_order_id, currency="EGP"):
    """
    Register a new order with Paymob.
    amount_cents: Amount in cents (e.g., 100.00 EGP = 10000 cents)
    """
    url = f"{PAYMOB_API_BASE}/ecommerce/orders"
    payload = {
        "auth_token": auth_token,
        "delivery_needed": "false",
        "amount_cents": str(amount_cents),
        "currency": currency,
        "merchant_order_id": str(merchant_order_id),
        "items": [] # Items are optional for digital wallet/balance top-up
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json().get("id")

def get_payment_key(auth_token, paymob_order_id, billing_data, amount_cents, currency="EGP"):
    """
    Generate a payment key for the registered order.
    billing_data: Dictionary containing customer details (first_name, last_name, email, phone, etc.)
    """
    integration_id = os.environ.get('PAYMOB_INTEGRATION_ID')
    if not integration_id:
        raise ValueError("PAYMOB_INTEGRATION_ID environment variable is not set.")

    url = f"{PAYMOB_API_BASE}/acceptance/payment_keys"
    
    # Ensure mandatory fields have fallbacks if missing (Paymob requires them)
    # This logic is also reinforced in the view, but good to have here as safety.
    billing_data = billing_data.copy()
    defaults = {
        "first_name": "NA",
        "last_name": "NA", 
        "email": "na@example.com",
        "phone_number": "NA",
        "apartment": "NA", 
        "floor": "NA", 
        "street": "NA", 
        "building": "NA", 
        "shipping_method": "NA", 
        "postal_code": "NA", 
        "city": "NA", 
        "country": "NA", 
        "state": "NA"
    }
    for key, val in defaults.items():
        if not billing_data.get(key):
            billing_data[key] = val

    payload = {
        "auth_token": auth_token,
        "amount_cents": str(amount_cents),
        "expiration": 3600, # 1 hour
        "order_id": str(paymob_order_id),
        "billing_data": billing_data,
        "currency": currency,
        "integration_id": integration_id,
        "lock_order_when_paid": "false",
        "tokenization": "true" # Request tokenization for card saving feature
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json().get("token")

def validate_hmac(request_params, hmac_secret):
    """
    Validate the HMAC signature from Paymob Webhook.
    request_params: Query parameters dictionary from the webhook request (GET dict).
    hmac_secret: Source of truth secret from settings.
    """
    if not hmac_secret:
        return False

    # Paymob HMAC concatenation order is strict
    hmac_keys = [
        "amount_cents",
        "created_at",
        "currency",
        "error_occured",
        "has_parent_transaction",
        "id",
        "integration_id",
        "is_3d_secure",
        "is_auth",
        "is_capture",
        "is_refunded",
        "is_standalone_payment",
        "is_voided",
        "order",
        "owner",
        "pending",
        "source_data.pan",
        "source_data.sub_type",
        "source_data.type",
        "success",
    ]
    
    concatenated_string = ""
    concatenated_string = ""
    for key in hmac_keys:
        val = None
        if key.startswith("source_data"):
            # Handle nested source_data
            # In JSON payload, 'source_data' is a dict.
            # In Query Params, keys might be flattened? But let's support the JSON structure we see.
            source_data_key = key.split('.')[1]
            source_data_dict = request_params.get('source_data')
            if isinstance(source_data_dict, dict):
                val = source_data_dict.get(source_data_key)
            else:
                 # Fallback for flat params if ever used
                 val = request_params.get(key)
        
        elif key == "order":
             # Handle nested order object which is common in JSON payload
             # Only ID is needed for HMAC? 
             # Wait, Paymob documentation says 'order' field. In JSON, 'order' is an object.
             # But usually for HMAC they mean the Order ID.
             # Let's check the logs: 'order': {'id': 436476059...}
             # But in query params it's just the ID.
             # If val is an dict, we likely need its ID.
             # HOWEVER, looking at strict Paymob calc: usually they send 'order' as ID in query params.
             # In JSON 'obj', 'order' is a full object.
             # We should probably use `order.id` if order is a dict.
             val = request_params.get(key)
             if isinstance(val, dict):
                 val = val.get('id')
        else:
            val = request_params.get(key)
        
        # Paymob specific formatting
        if val is None:
             pass # Skip or empty string? Logic says: if val is not None, concat.
                  # But be careful with 0 or False.
        
        if val is not None:
            if isinstance(val, bool):
                val = str(val).lower()
            concatenated_string += str(val)
    
    # Debug logging for calculation mismatch
    # print(f"DEBUG HMAC String: {concatenated_string}")

    # Calculate HMAC
    calculated_hmac = hmac.new(
        hmac_secret.encode('utf-8'),
        concatenated_string.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()

    received_hmac = request_params.get("hmac")
    
    return hmac.compare_digest(calculated_hmac, received_hmac)

def pay_with_token(token_identifier, payment_key):
    """
    Execute a payment using a saved card token.
    token_identifier: The secure token saved from previous transactions.
    payment_key: The payment key generated for the current order.
    """
    url = f"{PAYMOB_API_BASE}/acceptance/payments/pay"
    
    payload = {
        "source": {
            "identifier": token_identifier,
            "subtype": "TOKEN"
        },
        "payment_token": payment_key
    }
    
    response = requests.post(url, json=payload)
    # Don't raise for status immediately, as we might want to handle 3DS redirect or pending
    # response.raise_for_status() 
    return response.json()
