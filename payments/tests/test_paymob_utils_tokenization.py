from django.test import SimpleTestCase
from unittest.mock import patch, MagicMock
from srvana.paymob_utils import get_payment_key
import os

class PaymobUtilsTests(SimpleTestCase):
    
    @patch.dict(os.environ, {"PAYMOB_INTEGRATION_ID": "12345"})
    @patch('requests.post')
    def test_get_payment_key_includes_tokenization_flag(self, mock_post):
        """
        Verify that get_payment_key includes 'tokenization': 'true' in the payload.
        """
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"token": "test_payment_key"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Call function
        auth_token = "valid_auth_token"
        paymob_order_id = "999"
        billing_data = {
            "first_name": "Test", 
            "last_name": "User", 
            "email": "test@example.com", 
            "phone_number": "0100000000"
        }
        amount_cents = 10000

        token = get_payment_key(auth_token, paymob_order_id, billing_data, amount_cents)

        # Assertions
        self.assertEqual(token, "test_payment_key")
        
        # Check arguments passed to requests.post
        args, kwargs = mock_post.call_args
        self.assertIn('json', kwargs)
        payload = kwargs['json']
        
        # CRITICAL ASSERTION: Check for tokenization flag
        self.assertIn("tokenization", payload)
        self.assertEqual(payload["tokenization"], "true")
        
        # Verify other essential fields
        self.assertEqual(payload["auth_token"], auth_token)
        self.assertEqual(payload["amount_cents"], "10000")
        self.assertEqual(payload["integration_id"], "12345")
