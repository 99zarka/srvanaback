# 💳 Paymob Integration V2.0 Documentation

## 🚀 Overview

This document details the **Complete Paymob Integration** for the Srvana backend.
We have upgraded the system to include **Secure Iframe Payment**, **Card Tokenization (Save Card)**, and **Reactive UI Updates**.

---

## 🏗 Architecture

### 1. New Card Payment (Secure Iframe Flow)

- **Frontend**: `ClientFinancials.jsx`
- **Backend**: `POST /api/payments/deposit/`
- **Flow**:
  1.  User enters `amount` and clicks "Pay via Paymob".
  2.  Backend calls Paymob API with `"tokenization": "true"`.
  3.  Backend returns an `iframe_url`.
  4.  Frontend opens the Iframe in a **New Tab**.
  5.  User enters card details securely on Paymob's page.

### 2. Card Tokenization ("Save Card")

- **Auto-Save**: Because we send `tokenization=True`, Paymob automatically generates a secure **Token** upon successful payment.
- **Webhook Handling**:
  - Paymob sends a `TOKEN` event webhook.
  - Backend (`views.py`) verifies logic and saves a `PaymentMethod` (Token, Masked PAN, Card Type).
  - **Security**: We NEVER store the full card number (PAN) or CVV.

### 3. Reactive UI (Polling System)

- **Problem**: Users hate "Loading..." spinners that freeze the screen.
- **Solution**: We implemented a **Background Polling System**.
  - When the user opens the payment tab, the main dashboard stays active.
  - It quietly asks the server: _"Did transaction #123 complete yet?"_ every 5 seconds.
  - Once the Webhook confirms success, the Dashboard **automatically** shows a "Success" banner and updates the balance.

---

## 💻 Local Development Setup

To run this integration locally, you must create a `.env` file in the project root.

### 1. Create `.env` File

Create a file named `.env` next to `manage.py` and add your Paymob Test keys:

```bash
# Security: NEVER commit this file to Git
PAYMOB_API_KEY=your_test_key
PAYMOB_INTEGRATION_ID=12345
PAYMOB_IFRAME_ID=67890
PAYMOB_HMAC_SECRET=your_test_hmac
DJANGO_PRODUCTION=False
```

### 2. Run with ngrok (For Webhooks)

Paymob needs to reach your localhost to send webhooks.

1.  Run backend: `python manage.py runserver`
2.  Run ngrok: `ngrok http 8000`
3.  Copy URL (e.g., `https://xyz.ngrok.io`) to Paymob Dashboard -> Integration Settings.
    - Callback URL: `https://xyz.ngrok.io/api/payments/webhook/`

---

## 🛠 Production Deployment Guide (No ngrok)

When deploying to a live server (e.g., Cloud Run, EC2, VPS), follow these steps to validate payments without `ngrok`.

### Prerequisite: HTTPS Required

Paymob Webhooks **require** a valid HTTPS URL. Ensure your domain has an SSL certificate (e.g., Let's Encrypt).

### Step 1: Configure Environment Variables

On your production server, set these variables:

```bash
PAYMOB_API_KEY=production_api_key
PAYMOB_INTEGRATION_ID=production_integration_id
PAYMOB_IFRAME_ID=production_iframe_id
PAYMOB_HMAC_SECRET=production_hmac_secret
DJANGO_PRODUCTION=True
```

### Step 2: Set Webhook Callback URL

1.  Log in to your [Paymob Dashboard](https://accept.paymob.com/).
2.  Go to **Settings** -> **Integration Settings**.
3.  Scroll to **Transaction Processed Callback**.
4.  Enter your **Production URL**:
    ```
    https://your-domain.com/api/payments/webhook/
    ```
    _(Note: Ensure the `/api/` prefix matches your Django `urls.py` config)._
5.  Click **Save**.

### Step 3: Verify Transaction Callbacks

Paymob sends two types of callbacks. Ensure both are handled (our code handles all via the single webhook endpoint):

1.  **Transaction Response Callback**: Notifies of success/failure (Updates Balance).
2.  **Order Delivery Callback**: (Not used/Optional).
3.  **Token Callback**: Notifies when a card is saved (Updates `PaymentMethod`).

### Step 4: Firewall / Security Group

Ensure your server allows **Incoming POST requests** on port 443 (HTTPS) from the internet. Paymob IPs change, so generally allow `0.0.0.0/0` for the webhook path, relying on **HMAC Signature** for security.

---

## 🧪 Testing in Production

1.  **Test Card**: Use Paymob's [Test Cards](https://docs.paymob.com/docs/test-cards) (if in Test Mode) or a generic card with small amount (if Live).
2.  **Monitor Logs**: Watch your server logs for `DEBUG Webhook Payload:` to confirm Paymob is reaching you.
3.  **HMAC Failure**: If you see `Invalid HMAC Signature`, double-check that your `PAYMOB_HMAC_SECRET` matches the one in the Paymob Dashboard **exactly**.

---

## 🧪 Verification & Automated Testing

We have included a comprehensive **Test Suite** to verify the payment flow without needing real credit cards or manual testing.

### 1. Verify Tokenization Config

Checks if the backend is correctly asking Paymob for a token (i.e., sending `tokenization=true`).

```bash
python manage.py test payments.tests.test_paymob_utils_tokenization
```

**Expected Result**: `OK`

### 2. Verify Full Payment Flow (Mocked)

Simulates the entire Deposit -> Iframe -> Webhook -> Save Card process.

```bash
python manage.py test payments.tests.test_tokenization
```

**Expected Result**: `OK` (Should confirm that `PaymentMethod` is created with a token).

### 3. Running All Payment Tests

To run all payment-related tests at once:

```bash
python manage.py test payments
```

---

## 📝 Change Log V2

### [NEW] Frontend Refactor (`ClientFinancials.jsx`)

- **Removed Manual Inputs**: Deleted insecure Card Number/CVV fields to comply with PCI-DSS.
- **Simplified UI**: Single "Pay" button that handles redirection.
- **Error Handling**: Now displays **exact server errors** (e.g., "Invalid Amount") instead of generic failures.

### [NEW] Backend Refactor (`payments/views.py`)

- **Standardized Errors**: Changed all error responses to use `{'detail': 'message'}` JSON format for frontend compatibility.
- **Tokenization**: Enabled `tokenization=True` in payment key requests.
- **Saved Card Validation**: Added checks to ensure old cards (without tokens) are rejected gracefully.

### [FIX] Backend Utilities (`srvana/paymob_utils.py`)

- Updated `get_payment_key` to inject the tokenization flag.

---

## ❓ Troubleshooting & Common Pitfalls

| Error                            | Probable Cause              | Solution                                                                               |
| :------------------------------- | :-------------------------- | :------------------------------------------------------------------------------------- |
| **"Failed to initiate deposit"** | Backend API Error           | Check Server Logs. Usually `PAYMOB_API_KEY` is invalid or `PAYMOB_IFRAME_ID` is wrong. |
| **"Invalid HMAC Signature"**     | Webhook Secret Mismatch     | Ensure `PAYMOB_HMAC_SECRET` in `.env` matches the one in Paymob Dashboard EXACTLY.     |
| **Status 403 on Webhook**        | CSRF Protection             | Ensure `payments/views.py` has `@csrf_exempt` decorator on the webhook view.           |
| **Iframe refuses to load**       | Iframe Config               | Ensure the `PAYMOB_IFRAME_ID` matches a valid Iframe in your Paymob Dashboard.         |
| **Transaction Stuck in Pending** | Webhook not reaching server | Check your Server Firewall, or ensure the Callback URL in Paymob is correct (https).   |

---

## 💳 Test Card Data (Sandbox Mode)

Use these cards to simulate different scenarios in the Iframe.

| Type              | Card Number           | CVV | Expiry | PIN  | Outcome                      |
| :---------------- | :-------------------- | :-- | :----- | :--- | :--------------------------- |
| **Success**       | `0000 0000 0000 0000` | 123 | 12/25  | 1234 | ✅ **Approved**              |
| **Failure**       | `0000 0000 0000 1111` | 123 | 12/25  | 1234 | ❌ **Declined**              |
| **3DS Challenge** | `0000 0000 0000 2222` | 123 | 12/25  | 1234 | ⚠️ **OTP Page** (Enter 1234) |

---

## ✅ Go-Live Checklist

- [ ] **SSL Validated**: Production URL starts with `https://`.
- [ ] **Webhook Configured**: URL set in Paymob Dashboard.
- [ ] **HMAC Secret Updated**: Copied `HMAC Secret` from Dashboard to Production `.env`.
- [ ] **IDs Updated**: `INTEGRATION_ID` and `IFRAME_ID` updated to Production versions (if different).
- [ ] **Firewall Open**: Port 443 is open to the world (or Paymob IPs).
- [ ] **Debug Mode Off**: `DEBUG=False` in Django settings.
