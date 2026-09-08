# Scan2Pay — Test Credentials
> DEV / STAGING ONLY. Never commit real credentials here.
> OTP bypass is active — use code `0000` on verify page, or phone_verified=true in DB.

---

## Merchant Accounts

| Name         | Phone        | Password  | user_type | user_id   | merchant_id | Primary QR     |
|--------------|--------------|-----------|-----------|-----------|-------------|----------------|
| Demo Merchant| 0821000001   | Vendor1234! | vendor  | usr_001   | mch_001     | QR-DEMO0001    |
| Tip Tester   | 0660404333   | 123456    | tip       | usr_004   | mch_003     | QR-BA5ECDB1    |

## Staff Accounts

| Name         | Phone        | Password      | role    | user_id      |
|--------------|--------------|---------------|---------|--------------|
| Admin User   | 0616583827   | Admin1234     | admin   | usr_admin    |
| Support User | 0600000001   | Support1234!  | support | usr_support  |

---

## Pay Page URLs (customer-facing, no auth)
- Tip Tester QR: https://scan2pay.site/pay/QR-BA5ECDB1

## Test Card (Paystack)
| Scenario | Card number          | Expiry     | CVV |
|----------|----------------------|------------|-----|
| Success  | 4084 0840 8408 4081  | Any future | 408 |
| Failure  | 4084 0800 0000 5408  | Any future | 408 |

## API
- Prod: https://8fhbnwufgi.execute-api.af-south-1.amazonaws.com/Prod
- OTP bypass code: `0000`
