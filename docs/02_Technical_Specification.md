# Scan To Pay — Technical Specification

## 1. Technical Overview

Scan To Pay is a single payment platform with four main user experiences:

1. **Customer** — scans a QR code and makes a payment.
2. **Tip User** — receives variable payments/tips through a permanent QR code.
3. **Vendor / Business User** — accepts payments for products or services through fixed or variable QR codes.
4. **Admin** — manages the platform, users, pricing, transactions, settlements, integrations and system configuration.

Planned technology stack:

- Frontend: Next.js
- Backend: Python
- API: AWS API Gateway
- Database: Supabase / PostgreSQL
- File storage: Amazon S3
- Payment provider: Paystack
- Messaging: WhatsApp Business API

The frontend, WhatsApp integration and other interfaces should use the same backend business logic and database.

---

# 2. Customer User

The customer is the person scanning the QR code and making the payment.

The customer should not need to create an account for the MVP.

## 2.1 Payment Page

This is the first page displayed after scanning a QR code.

Information displayed:

- QR/payment code
- Name of the person or business being paid
- Profile image or business logo where available
- Product or service name, if applicable
- Product/service description
- Amount to be paid
- Currency
- Applicable fees
- Payment method
- Pay Now / Continue button

### Variable Payment

The customer enters the amount:

> Enter Amount: R____

### Fixed Payment

The current price is displayed:

> Amount: R150

The customer must clearly see who they are paying and how much they are paying before continuing.

## 2.2 Payment Method Page

Display:

- Recipient
- Amount
- Available payment methods
- Applicable fees
- Continue to payment

Potential payment methods include:

- Card
- EFT/local supported methods
- Apple Pay where supported
- Google Pay where supported

## 2.3 Payment Processing Page

Display:

- Payment reference
- Amount
- Recipient
- Processing status
- Message asking the customer not to close the page while the payment is being processed

## 2.4 Payment Result Page

### Successful Payment

Display:

- Payment successful
- Amount
- Recipient
- Transaction reference
- Date/time
- Receipt

### Failed Payment

Display:

- Payment unsuccessful
- Reason where available
- Retry option

### Pending Payment

Display:

- Payment is still being confirmed
- Transaction reference
- Current status
- Option to check the payment status again

---

# 3. Tip User

A Tip User receives variable payments/tips.

Examples include drivers, waiters, delivery workers, freelancers and service workers.

The Tip User has one permanent QR code that customers can scan and use to enter any amount.

## 3.1 Dashboard

Display:

- Today's tips
- This month's tips
- Total number of tips
- Pending payments
- Settled amount
- Platform fees
- Recent transactions

Example:

| Information | Amount |
|---|---:|
| Today's Tips | R850 |
| This Month | R8,450 |
| Pending | R250 |
| Settled | R8,200 |

## 3.2 My QR Code

Display:

- Tip User name
- Profile image
- Permanent payment code
- QR code
- QR preview
- QR status

Actions:

- Download QR
- Print QR
- Share QR

The QR remains the same regardless of the amount received.

## 3.3 Transactions

Display:

- Date
- Time
- Transaction reference
- Amount
- Payment method
- Platform fee
- Provider fee where applicable
- Net amount
- Payment status

Filters can include date, amount, status and payment method.

## 3.4 Transaction Details

Display:

- Transaction reference
- Amount
- Platform fee
- Provider fee where applicable
- Net amount
- Payment method
- Payment status
- Settlement status
- Date/time

## 3.5 Earnings / Settlements

Display:

- Total earnings
- Pending settlement
- Completed settlements
- Settlement dates
- Settlement amounts
- Settlement status

## 3.6 Profile

The Tip User can manage:

- Name
- Profile image
- Contact details
- Settlement information
- Account information

## 3.7 Subscription

Display:

- Current subscription plan
- Monthly price
- Platform transaction fee
- Next billing date
- Subscription status
- Upgrade/downgrade options

---

# 4. Vendor / Business User

The Vendor / Business User accepts payments for products or services.

A business can have multiple payment codes.

Examples:

- Car Wash — R150
- Premium Wash — R250
- Taxi Fare — Variable
- Haircut — R200

## 4.1 Dashboard

Display:

- Today's sales
- Monthly sales
- Number of transactions
- Pending payments
- Platform fees
- Net earnings
- Settled amount
- Recent transactions

## 4.2 Payment Codes / QR Codes

Display all business payment codes.

For each code:

- Payment code
- QR code
- Product/service
- Fixed or variable
- Current price
- Status
- Created date
- Last updated

Actions:

- View QR
- Download
- Print
- Edit
- Disable
- Enable

## 4.3 Create Payment Code

The business can create a new payment destination.

### Fixed Amount

Example:

- Product: Car Wash
- Price: R150
- Payment type: Fixed

### Variable Amount

Example:

- Payment name: Taxi Fare
- Payment type: Variable

The system generates a permanent QR/payment code.

## 4.4 Products & Services

Display:

- Product/service name
- Description
- Current price
- Payment code
- Status

Actions:

- Add
- Edit
- Change price
- Disable
- Enable

Changing the price must not require a new QR code.

## 4.5 Transactions

Display:

- Transaction reference
- Product/service
- Amount
- Platform fee
- Provider fee
- Net amount
- Payment method
- Payment status
- Settlement status
- Date/time

## 4.6 Transaction Details

Display:

- Product/service
- Amount paid
- Platform fee
- Provider fee
- Net amount
- Payment method
- Payment status
- Settlement status
- Transaction reference
- Date/time

## 4.7 Earnings / Settlements

Display:

- Total sales
- Available amount
- Pending amount
- Settled amount
- Settlement history

## 4.8 Business Profile

The business can manage:

- Business name
- Business logo
- Description
- Contact information
- Business information
- Settlement information

## 4.9 Subscription

Display:

- Current plan
- Monthly subscription
- Transaction fee
- Next billing date
- Subscription status
- Upgrade/downgrade options

---

# 5. Admin User

The Admin controls the entire Scan To Pay platform.

## 5.1 Admin Dashboard

Display:

- Total users
- Total Tip Users
- Total businesses
- Active users
- Suspended users
- Transactions today
- Transactions this month
- Total payment volume
- Platform revenue
- Provider fees
- Pending settlements
- Failed payments

## 5.2 Users

Admin can view all users.

Information:

- Name
- Email/contact
- User type
- Account status
- Registration date
- Transaction volume
- Subscription
- Verification status

Actions:

- View
- Suspend
- Reactivate
- Change account status

## 5.3 Tip Users

Display:

- Tip User
- Payment code
- Total tips
- Transaction count
- Subscription
- Fees generated
- Account status

## 5.4 Businesses

Display:

- Business name
- Owner
- Business type
- Number of QR codes
- Transaction volume
- Subscription
- Settlement status
- Account status

## 5.5 Payment Codes / QR Management

Information:

- Payment code
- Owner
- Type
- Fixed/variable
- Product/service
- Current amount
- Status
- Created date

Admin actions:

- View
- Disable
- Enable
- View owner
- View transactions

## 5.6 Transactions

Admin has access to all platform transactions.

Filters:

- Date
- User
- Business
- Payment status
- Settlement status
- Payment method
- Amount
- Transaction reference

Display:

- Gross amount
- Provider fee
- Platform fee
- Net merchant amount
- Payment status
- Settlement status

## 5.7 Pricing & Charges

Admin should be able to configure platform charges without changing application code.

### Subscription Plans

Example:

**Free**
- Monthly: R0
- Platform fee: 2%

**Basic**
- Monthly: R100
- Platform fee: 1.5%

**Pro**
- Monthly: R250
- Platform fee: 1%

The actual values should be configurable.

### Platform Charges

Admin can configure:

- Platform percentage
- Fixed platform fee
- Subscription price
- Different charges per plan
- Effective date

### Provider Charges

The platform can store provider fee rules for calculation and reporting:

- Provider percentage
- Provider fixed fee
- Payment method
- Who absorbs the provider fee

Possible fee bearer:

- Customer
- Merchant
- Platform

## 5.8 Pricing History

Pricing changes should be versioned.

| Version | Platform Fee | Effective From | Status |
|---|---:|---|---|
| Version 1 | 1.5% | Jan 2026 | Expired |
| Version 2 | 2.0% | Jul 2026 | Active |

A transaction must retain the pricing configuration used when the transaction occurred.

## 5.9 Settlements

Display:

- Merchant
- Settlement amount
- Settlement date
- Status
- Provider reference
- Settlement period

Statuses:

- Pending
- Processing
- Completed
- Failed

## 5.10 Refunds & Disputes

Admin can:

- View refunds
- View disputed transactions
- Record/process refunds
- View refund status
- Link refunds to original transactions

## 5.11 Payment Provider

Display:

- Provider status
- Provider transaction information
- Payment methods
- Merchant/provider account status
- Webhook status
- Failed webhook events

Provider secret keys should remain securely managed in the backend/secrets system and should not be exposed unnecessarily through the Admin UI.

## 5.12 WhatsApp

Display:

- Integration status
- Connected account
- Webhook status
- Message statistics
- Failed messages
- Supported commands

## 5.13 Notifications

Admin can configure:

- Payment successful notifications
- Payment failed notifications
- Settlement notifications
- Subscription notifications
- Account notifications
- System announcements

## 5.14 Audit Logs

Important administrative actions must be recorded.

| Admin | Action | Date | Target |
|---|---|---|---|
| Admin 1 | Changed platform fee | 03 Sep | Pricing |
| Admin 1 | Suspended user | 03 Sep | User |
| Admin 2 | Disabled QR | 02 Sep | QR |

---

# 6. QR Code Architecture

QR codes are permanent payment identifiers.

The QR code should identify a payment code rather than contain a hard-coded price.

General flow:

QR Code → Payment Code → Backend → Payment Configuration → Current Product/Service/Payment Type → Payment Session → Transaction

## Fixed QR

Example:

QR → STP-8K29XQ → Car Wash → Current Price: R150

If the price changes from R150 to R170, the QR code does not need to change.

## Variable QR

Example:

QR → STP-TAXI-001 → Customer enters amount → R85 → Payment Session

## Core QR Rule

A permanent QR represents a payment destination, not a transaction.

Every scan can create a new payment session and transaction.

The same QR can therefore be used by many customers.

---

# 7. Payment Sessions

Payment sessions provide the temporary state between scanning a QR and completing a payment.

General flow:

1. Customer scans QR.
2. Backend resolves payment code.
3. Backend validates payment destination.
4. Backend retrieves current product/service configuration.
5. Customer enters an amount if the payment code is variable.
6. Backend validates the amount.
7. Payment session is created.
8. Transaction is created.
9. Platform and provider fees are calculated.
10. Paystack payment is initialized.
11. Customer completes payment.
12. Paystack sends a webhook.
13. Backend validates the webhook.
14. Transaction is updated.
15. Merchant dashboard reflects the payment.
16. Settlement processing occurs according to the provider/platform settlement process.

A payment session should contain:

- Session ID
- Payment code ID
- Merchant ID
- Amount
- Currency
- Status
- Expiry time
- Creation time
- Customer/payment reference

Possible statuses:

- Created
- Awaiting Payment
- Processing
- Paid
- Failed
- Expired
- Cancelled
- Refunded

The backend must validate the amount and payment destination. The frontend should never be trusted as the final source of transaction amount.

---

# 8. Database Tables

## 8.1 Identity

### users

Stores platform user accounts.

Possible information:

- ID
- Name
- Email
- Phone
- Account status
- Created date
- Updated date

### roles

Defines available roles:

- Customer
- Tip User
- Business User
- Admin
- Super Admin

### user_roles

Connects users to their roles.

## 8.2 User Profiles

### tip_profiles

Stores Tip User-specific information.

### business_profiles

Stores business-specific information.

## 8.3 Payment Configuration

### payment_codes

Stores permanent QR/payment destinations.

Important information:

- Payment code
- Owner
- Payment type
- Status
- Linked catalog item
- Created date
- Updated date

### catalog_items

Stores products and services.

Possible type:

- Product
- Service

Important information:

- Name
- Description
- Current price
- Currency
- Status
- Owner

## 8.4 Payments

### payment_sessions

Stores temporary payment sessions.

### transactions

Stores the platform's financial transaction record.

Important information:

- Transaction ID
- Merchant/User ID
- Payment session ID
- Payment code ID
- Amount
- Currency
- Platform fee
- Provider fee
- Net amount
- Status
- Payment method
- Provider reference
- Created date
- Paid date

### transaction_fees

Stores individual fees applied to a transaction.

### payment_provider_transactions

Stores provider-specific payment information and references.

## 8.5 Settlements

### settlements

Stores settlement records.

### settlement_items

Links transactions to settlements.

## 8.6 Refunds

### refunds

Stores refunds associated with original transactions.

## 8.7 Pricing

### subscription_plans

Stores available subscription plans.

### subscriptions

Stores each user's active subscription.

### pricing_versions

Stores historical versions of platform pricing.

### fee_rules

Stores individual fee rules associated with pricing versions.

## 8.8 Webhooks

### webhook_events

Stores incoming provider webhook events.

Information:

- Provider
- Event type
- Event reference
- Payload
- Signature validation result
- Processing status
- Processing time
- Created date

## 8.9 Platform

### notifications

Stores notification records.

### audit_logs

Stores important user/admin actions.

### system_settings

Stores safe configurable system settings.

### feature_flags

Allows features to be enabled or disabled without deployment.

## 8.10 Integrations

### merchant_payment_provider_accounts

Stores the relationship between merchants and payment-provider accounts/subaccounts.

### whatsapp_accounts

Stores WhatsApp integration information.

### whatsapp_messages

Stores relevant WhatsApp message records and processing status.

---

# 9. Payment Transaction Flow

The normal payment flow is:

1. Customer scans QR.
2. Backend resolves the payment code.
3. Backend checks that the payment code is active.
4. Backend retrieves the current product/service information if applicable.
5. Customer enters an amount if the payment code is variable.
6. Backend validates the amount.
7. Payment session is created.
8. Transaction is created.
9. Platform and provider fees are calculated.
10. Paystack payment is initialized.
11. Customer completes payment.
12. Paystack sends a webhook.
13. Backend validates the webhook.
14. Transaction is updated.
15. Merchant dashboard reflects the payment.
16. Settlement processing occurs.

---

# 10. Paystack Webhooks

Paystack webhooks are an important part of payment confirmation.

General flow:

Paystack → API Gateway → Python Backend → Verify Webhook → Validate Event → Check Idempotency → Store Webhook Event → Find Transaction → Update Transaction → Trigger Notifications

## Webhook Requirements

The backend should:

- Verify webhook authenticity/signature.
- Validate the event.
- Store the event.
- Prevent duplicate processing.
- Locate the related transaction.
- Update transaction status.
- Record provider references.
- Record processing failures.
- Allow administrators to investigate failed webhook processing.

The frontend payment redirect should not be treated as the final source of truth for a successful payment. The validated provider webhook should be used to confirm the transaction.

---

# 11. Merchant Settlement

Payment and settlement are separate concepts.

A successful customer payment does not necessarily mean the merchant has already received the money in their bank account.

General flow:

Customer Payment → Gross Amount → Provider Fee → Platform Fee → Merchant Net Amount → Settlement → Merchant Bank Account

The platform should track:

- Gross payment
- Provider fee
- Platform fee
- Net merchant amount
- Settlement status
- Settlement reference
- Settlement date

Possible settlement statuses:

- Pending
- Processing
- Completed
- Failed
- Reversed where applicable

The platform should support reconciliation between:

- Internal transactions
- Payment provider transactions
- Provider settlements

---

# 12. WhatsApp API Flow

WhatsApp should act as another interface to the same platform backend.

General flow:

Merchant → WhatsApp → WhatsApp Business API → API Gateway → Python Backend → Authentication → Business Logic → Database → Response → WhatsApp

Possible commands:

- BALANCE
- TODAY
- HISTORY
- PAY R200
- PRODUCTS
- HELP

Example:

Merchant:
BALANCE

System:
Today's earnings: R4,850
Pending: R350
Settled: R4,500

WhatsApp should not contain separate payment or financial business logic. It should call the same backend services used by the web dashboard.

---

# 13. Admin System

The Admin system is responsible for managing the platform rather than individual merchant activity.

The Admin system should provide:

- User management
- Tip User management
- Business management
- QR/payment code management
- Transaction management
- Settlement monitoring
- Pricing management
- Subscription management
- Refund/dispute management
- Payment provider monitoring
- WhatsApp monitoring
- Notifications
- Audit logs
- System configuration
- Reporting

## 13.1 Admin Pricing Configuration

Pricing should be database-driven.

Admin should be able to:

1. Create a pricing plan.
2. Set monthly subscription price.
3. Set platform percentage.
4. Set fixed platform fee.
5. Configure provider fee assumptions where needed.
6. Select who absorbs applicable fees.
7. Set an effective date.
8. Publish the pricing version.
9. View pricing history.

A pricing change should not require a new application deployment.

## 13.2 Pricing Snapshot

When a transaction is created, the platform should store the pricing information used for that transaction.

Example:

Transaction: TXN123
Pricing Version: 5
Platform Fee: 1.5%
Platform Fee Amount: R3.00
Provider Fee: R6.80

If the platform later changes the fee to 2%, TXN123 remains unchanged.

---

# 14. API Design

Major API areas:

- Authentication
- Users
- Tip Users
- Businesses
- Payment Codes
- Products/Services
- Payment Sessions
- Transactions
- Fees
- Pricing
- Subscriptions
- Settlements
- Refunds
- Notifications
- Admin
- Paystack Webhooks
- WhatsApp Webhooks

Important API principles:

- Authentication and authorization must be enforced server-side.
- Customer payment endpoints should expose only information necessary for payment.
- Merchant endpoints should only access the authenticated merchant's data.
- Admin endpoints require elevated permissions.
- Financial values should be calculated and validated by the backend.
- Payment-related operations should support idempotency where required.
- Sensitive operations should be logged.

---

# 15. Frontend Responsibilities

The Next.js frontend is responsible primarily for:

- Displaying the correct information to each user.
- Collecting customer payment information.
- Displaying merchant dashboards.
- Displaying Admin dashboards.
- Managing forms and validation feedback.
- Showing payment status.
- Calling backend APIs.
- Handling authentication/session state.
- Providing responsive mobile payment pages.

The frontend should not be responsible for authoritative financial calculations.

---

# 16. Backend Responsibilities

The Python backend is responsible for:

- Authentication and authorization
- User management
- QR/payment-code resolution
- Payment session creation
- Transaction creation
- Fee calculation
- Pricing rules
- Paystack integration
- Webhook processing
- Settlement records
- Refund records
- Notifications
- WhatsApp processing
- Admin operations
- Audit logging
- Business rules

The backend is the authoritative layer for business and financial logic.

---

# 17. S3 Usage

Amazon S3 can be used for:

- Merchant logos
- Profile images
- QR images where stored as files
- Receipts
- Reports/exports
- Other generated documents

The database should store the relevant file reference/metadata rather than large files directly in transactional tables.

---

# 18. Security & Data Protection

Important security requirements include:

- Secure authentication
- Role-based access control
- Server-side authorization
- Webhook signature verification
- Idempotent payment processing
- API rate limiting
- Input validation
- Secure secret management
- Audit logging
- Encryption in transit
- Appropriate encryption at rest
- Protection of customer information
- Account suspension controls
- Monitoring for suspicious payment activity

Administrative actions affecting money, pricing or account status should be auditable.

---

# 19. MVP Technical Scope

## Customer

- Scan QR
- View payment information
- Enter amount for variable payments
- View fixed price
- Select payment method
- Complete payment
- View payment result

## Tip User

- Registration/onboarding
- Dashboard
- Permanent QR
- Transactions
- Transaction details
- Earnings/settlements
- Profile
- Subscription

## Vendor / Business

- Registration/onboarding
- Dashboard
- Payment codes/QR codes
- Fixed payments
- Variable payments
- Products/services
- Price updates
- Transactions
- Earnings/settlements
- Business profile
- Subscription

## Admin

- Dashboard
- User management
- Tip User management
- Business management
- QR management
- Transaction management
- Pricing configuration
- Subscription management
- Settlement monitoring
- Basic refund/dispute management
- Paystack monitoring
- Audit logs

## Platform

- Payment sessions
- Transactions
- Fee calculation
- Paystack integration
- Paystack webhooks
- Settlement tracking
- Notifications
- Supabase database
- S3 file storage

---

# 20. Future Technical Features

Potential future functionality:

- WhatsApp integration
- Advanced reporting
- Automated reconciliation
- Refund automation
- Dispute management
- Multiple business branches
- Multiple merchant staff accounts
- Advanced permissions
- Taxi association management
- Accounting exports
- Additional payment providers
- Advanced analytics
- Automated notifications
- Feature flags and experimentation

---

# 21. Core Technical Principles

1. A QR code identifies a payment destination, not a transaction.
2. QR codes should not contain hard-coded prices.
3. Every scan can create its own payment session and transaction.
4. The backend is the source of truth for amounts and fees.
5. Payment confirmation must rely on validated provider events/webhooks.
6. Payment and settlement are separate states.
7. Transactions must preserve the exact fees applied at the time of payment.
8. Pricing should be configurable from the Admin system.
9. Pricing changes must be versioned.
10. WhatsApp should use the same backend business logic as the web application.
11. Financial and administrative actions should be auditable.
12. The customer experience should remain simple and require no account for the MVP.
