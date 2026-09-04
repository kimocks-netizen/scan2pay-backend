# Scan To Pay — Business Model & Product Overview

## 1. Executive Summary

**Scan To Pay** is a digital payment platform designed to make it easier for customers to pay informal workers, small vendors, service providers, and other small businesses using a simple QR-code-based payment experience.

The core idea is:

> **Create once → Display QR → Customer scans → Customer pays → Merchant receives payment**

The platform has two primary user types:

1. **Tip Users** — individuals who receive variable tips or payments.
2. **Vendor / Business Users** — businesses that accept payments for products or services using either variable or fixed amounts.

A key principle of Scan To Pay is that **QR codes should be reusable**. A merchant should be able to create a QR code once, display or print it, and continue using it even when the associated price changes.

The platform will use a payment provider such as **Paystack** for payment processing and will explore supported digital-wallet payment methods such as **Apple Pay and Google Pay**. WhatsApp will provide an additional way for merchants to interact with the platform.

---

# 2. The Problem

Many small businesses and informal workers in South Africa face challenges when accepting digital payments.

Common problems include:

- Customers may not always carry cash.
- Small vendors may not have traditional card machines.
- Tip recipients can lose potential tips when customers do not have cash.
- Small businesses may not want the cost or complexity of traditional payment terminals.
- A business may repeatedly sell the same product and should not need to create a new payment request for every customer.
- Businesses with changing prices should not need to replace printed QR codes whenever prices increase.
- Customers should have a quick payment experience without manually entering complicated payment details.

Scan To Pay aims to provide a simple, mobile-first alternative.

---

# 3. The Solution

Scan To Pay gives a worker or business a unique QR-based payment identity.

The QR code can be displayed:

- On a printed card
- At a shop or stall
- On a counter
- Inside a taxi
- At a taxi rank
- On a vehicle
- On a phone
- On a poster
- Next to a product
- At a service point

The customer scans the QR code using their phone.

The Scan To Pay platform identifies the relevant user, product, service, or payment code and presents the appropriate payment experience.

The customer then completes the payment using an available payment method.

The QR code does **not** need to be recreated for every transaction.

---

# 4. Target Market

Scan To Pay is primarily targeted at South African individuals and small businesses that need a simple way to accept digital payments.

## 4.1 Informal and Small Businesses

Examples include:

- Street vendors
- Market traders
- Small convenience shops
- Food vendors
- Small retailers
- Independent service providers
- Car washes
- Barbers
- Hairdressers
- Small restaurants and takeaway businesses
- Mobile businesses

## 4.2 Individuals Receiving Tips

Examples include:

- Waiters
- Car wash workers
- Service workers
- Street performers
- Freelancers
- Other workers who receive voluntary payments or tips

## 4.3 Transport and Taxi Industry

Taxi associations and taxi operators are an important potential market.

Scan To Pay can allow taxi businesses to use permanent QR codes for:

- Fixed fares
- Variable fares
- Fare changes
- Individual taxi payments
- Association-level payment structures

This is particularly valuable because taxi fares can change over time without the physical QR code needing to be replaced.

## 4.4 Future Markets

Potential future markets include:

- Events
- Community organisations
- Charities
- Clubs
- Sports organisations
- Fundraising
- Small professional service providers
- Larger merchant networks

Any expansion into regulated financial services, wallets, fundraising, or similar activities must be assessed against applicable laws and payment-provider requirements before launch.

---

# 5. Two Main User Types

Scan To Pay will have **two primary user types**, each designed around a different payment scenario.

1. **Tip User** — receives variable payments/tips where the customer chooses the amount.
2. **Vendor / Business User** — accepts payments for products or services, using either a variable amount QR code or a fixed-amount QR code.

This distinction is particularly important for businesses and organisations such as **taxi associations**, where prices may change over time but the physical QR code should not need to be replaced.

---

## 5.1 Tip User — Variable Amount

A Tip User is someone who receives tips or voluntary payments where the customer decides how much to pay.

Examples:

- Waiters
- Car wash workers
- Street performers
- Service workers
- Freelancers
- Other workers who receive variable payments

The user receives a permanent Scan To Pay QR code.

### Customer Flow

```text
Customer
   |
   v
Scans QR Code
   |
   v
Worker Profile
   |
   v
Enter Amount
   |
   v
R50
   |
   v
Pay
   |
   v
Payment Provider
   |
   v
Payment Confirmed
   |
   v
Worker notified
```

The worker does **not** need to generate a new QR code for every tip.

The same QR code can be displayed permanently and used repeatedly.

---

## 5.2 Vendor / Business User

The second main user type is a **Vendor / Business User**.

This includes:

- Street vendors
- Taxi associations and taxi operators
- Small shops
- Market traders
- Food vendors
- Car washes
- Barbers
- Hairdressers
- Small restaurants
- Service providers
- Other small businesses

The Vendor / Business User needs more flexibility than a Tip User because they may have:

- Different products
- Different services
- Different prices
- Prices that change over time
- Customers paying different amounts for the same service

Scan To Pay therefore supports two important QR-code payment modes for this user type.

### 5.2a One QR Code — Variable Amount

A business can create **one permanent QR code** where the customer enters the amount to pay.

For example, a taxi association or service provider may want customers to pay different amounts depending on the journey or service.

```text
SCAN TO PAY

Taxi Payment

Enter Amount:

R ______

[ Continue ]
```

The QR code remains the same.

The merchant does not need to create a new QR code whenever the amount changes.

This is useful when:

- Fares vary
- Service prices vary
- Customers pay different amounts
- The business does not want separate QR codes for every price

### 5.2b One QR Code — Fixed Amount

A business can create a QR code linked to a specific product or service with a fixed price.

For example:

```text
Washing Powder

R200

[ QR CODE ]
```

A customer scans the QR code and sees:

```text
Washing Powder

R200

[ Pay R200 ]
```

The customer does not need to enter the amount manually.

#### Price Changes Without Recreating the QR

The QR code is linked to the product or service rather than permanently storing the price.

For example:

```text
QR CODE
   |
   v
Product ID: 82731
   |
   v
Washing Powder
   |
   v
Current Price: R200
```

If the merchant increases the price:

```text
Current Price: R220
```

the same QR code now displays:

```text
Washing Powder

R220

[ Pay R220 ]
```

The merchant does **not** need to:

- Delete the old QR
- Create a new QR
- Reprint the QR
- Replace the QR displayed at the business

They simply update the product or service price from their Scan To Pay dashboard.

---

## 5.3 Example — Taxi Association

The permanent QR concept is especially useful for taxi associations.

A taxi association could place Scan To Pay QR codes:

- Inside taxis
- At taxi ranks
- On payment notices
- On association signage

### Variable Fare Model

If fares differ:

```text
SCAN TO PAY

Taxi Payment

Enter Fare:

R ______

[ Pay ]
```

The QR code remains permanent.

### Fixed Fare Model

If the association has a standard fare:

```text
SCAN TO PAY

Taxi Fare

R20

[ Pay R20 ]
```

If the association increases the fare to R25, the administrator can update the fare:

```text
Old Price: R20
New Price: R25
```

The physical QR code remains unchanged.

This means an association can distribute large numbers of QR codes without needing to replace them whenever fares change.

---

## 5.4 Why Permanent QR Codes Matter

The QR code should represent a **payment identity or payment code**, not a hard-coded price.

For example:

```text
QR-8F72A91
      |
      v
Payment Code
      |
      v
Current Configuration
      |
      +----> Variable amount
      |
      +----> Fixed amount
      |
      +----> Current product price
      |
      +----> Current service price
```

This architecture allows Scan To Pay to change the payment configuration while keeping the physical QR code unchanged.

This is one of the platform's important advantages for businesses that need to display QR codes permanently.

---

# 6. Payment Provider — Paystack

Scan To Pay will use **Paystack** as its initial payment infrastructure provider rather than building its own card-processing infrastructure.

The payment provider will handle supported payment processing and settlement functionality, while Scan To Pay will manage the platform experience, merchant relationships, QR codes, payment sessions, transaction records, reporting, and notifications.

## 6.1 Payment Methods

The platform should support the payment methods available through the selected Paystack integration and South African payment configuration.

Potential payment methods include:

- Bank cards
- Supported EFT/payment methods
- Apple Pay where supported
- Google Pay where supported
- Other payment methods supported by the payment provider in the relevant market

Apple Pay and Google Pay should be treated as **payment options subject to provider, country, currency, device, browser, and merchant eligibility** rather than guaranteed payment methods for every transaction.

In particular, Scan To Pay should validate Apple Pay and Google Pay support for the intended South African/ZAR payment flow before making these options part of the public product promise.

## 6.2 Paystack Integration

The Scan To Pay backend will be responsible for:

- Creating payment sessions
- Linking payments to users and payment codes
- Initiating payments
- Receiving payment webhooks
- Verifying transactions
- Recording transaction status
- Handling idempotency
- Updating merchant transaction history
- Reconciliation
- Notifications

The platform should investigate Paystack's supported **subaccounts and split-payment functionality** for the merchant settlement model.

Before launch, the exact Scan To Pay business model should be confirmed with Paystack, particularly the model where multiple independent workers or businesses receive payments through the platform.

---

# 7. WhatsApp Integration

WhatsApp can become an additional interface for Scan To Pay users.

The objective is to allow merchants to interact with their Scan To Pay account without always opening the web application.

For example:

```text
Merchant
   |
   v
WhatsApp
   |
   v
Scan To Pay WhatsApp Service
   |
   v
Scan To Pay API
```

Possible features include:

### Account Information

```text
BALANCE
```

### Today's Sales

```text
TODAY
```

### Transaction History

```text
HISTORY
```

### Create Payment

```text
PAY R200
```

### Product Management

```text
PRODUCTS
```

### Help

```text
HELP
```

The WhatsApp integration should use the official WhatsApp Business Platform/API.

WhatsApp should remain an **interface to the Scan To Pay backend**, rather than containing separate business logic.

The architecture should therefore be:

```text
Web App
    |
WhatsApp
    |
Admin Dashboard
    |
    v
Scan To Pay API
    |
    v
Database
    |
    v
Paystack
```

All channels should use the same backend and business rules.

---

# 8. Customer Experience

A major product principle is:

> **The merchant needs Scan To Pay. The customer should not have to.**

A customer should ideally be able to scan a QR code using their normal phone camera and be taken directly to a mobile-friendly Scan To Pay payment page.

Example:

```text
Scan QR
   |
   v
Scan To Pay Payment Page
   |
   v
Merchant / Product
   |
   v
Amount
   |
   v
Choose Payment Method
   |
   v
Pay
```

This reduces friction and avoids requiring customers to create an account just to make a payment.

A Progressive Web App (PWA) can be used for the customer-facing experience before considering a separate native customer application.

---

# 9. Merchant Dashboard

Each business/user should have a dashboard containing:

## 9.1 Overview

- Today's sales
- Monthly sales
- Number of transactions
- Pending payments
- Successful payments
- Fees
- Settlement information

## 9.2 Payment Codes

```text
My Payment Codes

Car Wash             R50
Washing Powder       R200
Coca-Cola            R15
Taxi Fare            R20
Tips                 Variable
```

## 9.3 Transactions

Each transaction should show:

- Transaction ID
- Date/time
- Amount
- Payment status
- Product/service
- Payment method
- Fees
- Settlement status

## 9.4 Products and Services

Merchants can:

- Create products
- Edit products
- Change prices
- Disable products
- Generate QR codes
- Download/print QR codes
- View sales per product or service

---

# 10. Revenue Model

Scan To Pay can use a combination of subscription revenue and transaction fees.

## 10.1 Subscription + Platform Transaction Fee

A possible model is:

```text
Monthly subscription: R100

Platform transaction fee: 1–2%

Payment provider fee:
Passed through or incorporated into pricing
```

This provides predictable recurring revenue while allowing Scan To Pay revenue to scale with merchant transaction volume.

## 10.2 Transaction-Only Model

An alternative is:

```text
Monthly subscription: R0

Platform transaction fee: Higher percentage
```

This can make the platform easier to adopt for very small businesses, but revenue becomes more dependent on transaction volume.

## 10.3 Multiple Plans

A longer-term model could provide different plans.

### Free

```text
R0/month
Higher transaction fee
Basic features
```

### Basic

```text
R100/month
Lower transaction fee
Product QR codes
Transaction history
Basic reporting
```

### Pro

```text
Higher monthly fee
Lower transaction fee
Advanced reporting
Multiple users
Additional business features
```

The final pricing should be validated against:

- Payment-provider costs
- Merchant willingness to pay
- Average transaction value
- Average monthly transaction volume
- Customer acquisition costs
- Support costs
- Settlement costs
- Competitor pricing

---

# 11. Configurable Pricing

Pricing should be controlled from the Scan To Pay administration system rather than hard-coded into the application.

Example:

```text
PLATFORM PRICING

Subscription
----------------
Basic: R100
Pro: R250

Platform Transaction Fee
----------------
Percentage: 1.5%

Payment Provider
----------------
Provider: Paystack
Percentage: configurable
Fixed fee: configurable

[ Save Changes ]
```

The system should support configurable:

- Subscription prices
- Platform transaction percentages
- Fixed platform fees
- Provider fee assumptions
- Different pricing plans
- Merchant-specific pricing where required

Any pricing changes should be versioned/audited so that historical transactions continue to reflect the pricing that applied when the transaction occurred.

---

# 12. Example Transaction

A customer buys a product for R200.

Illustrative calculation:

```text
Product price
R200.00

Payment provider fee
- R6.80

Scan To Pay platform fee
- R3.00

------------------
Merchant amount
R190.20
```

The actual payment-provider fee must be calculated according to the payment method and current provider pricing.

The platform should clearly communicate applicable fees to merchants and customers.

The business should avoid assuming that every payment method has the same provider fee.

---

# 13. Business Value Proposition

## For Tip Users

> **Get tips without needing cash.**

## For Vendors

> **Accept digital payments without needing a traditional card machine.**

## For Customers

> **Scan, pay, and go.**

## For Small Businesses

> **Create your payment QR once and use it every day.**

## For Taxi Associations

> **Keep the same QR codes even when fares change.**

---

# 14. Competitive Advantage

Scan To Pay should not position itself simply as another QR payment application.

The stronger positioning is:

> **Simple digital payments for people and businesses that are underserved by traditional payment systems.**

The platform focuses on:

- Low-friction payments
- Permanent QR codes
- Small businesses
- Informal businesses
- Tip recipients
- Product-based QR payments
- Service-based QR payments
- Mobile-first payments
- Simple merchant management
- WhatsApp accessibility
- Flexible pricing

The permanent QR-code architecture is particularly valuable because a business can distribute and display QR codes without needing to replace them whenever prices change.

---

# 15. Security and Payment Principles

The platform should never rely on the customer-facing frontend alone to confirm a successful payment.

The payment provider webhook should be treated as the authoritative confirmation of payment.

The system should implement:

- Webhook signature verification
- Idempotency
- Transaction status validation
- Secure authentication
- Role-based access control
- Rate limiting
- Audit logs
- Encryption for sensitive data
- Secure secret management
- Fraud monitoring
- Payment reconciliation

Example:

```text
Customer pays
     |
     v
Paystack
     |
     v
Webhook
     |
     v
Scan To Pay Backend
     |
     v
Verify webhook
     |
     v
Update transaction
     |
     v
Merchant notified
```

---

# 16. Proposed Product Structure

```text
                       SCAN TO PAY
                            |
          +-----------------+-----------------+
          |                                   |
     Tip Users                         Vendors / Businesses
          |                                   |
   Variable Amount              +-------------+-------------+
                                |                           |
                         Variable QR                  Fixed QR
                                |                           |
                         Customer enters             Product/service
                             amount                    has price
                                |                           |
                                +-------------+-------------+
                                              |
                                        Permanent QR
                                              |
                                   +----------+----------+
                                   |                     |
                                Web/PWA              WhatsApp
                                   |                     |
                                   +----------+----------+
                                              |
                                      Scan To Pay API
                                              |
                           +------------------+------------------+
                           |                                     |
                        Database                              Paystack
                                                                 |
                                                     Payment Processing
```

---

# 17. Initial MVP

The first version should focus on the smallest set of features needed to prove that customers and merchants will actually use the product.

## 17.1 Tip User

- Account registration
- Login
- User profile
- Permanent tip QR
- Customer-selected amount
- Transaction history

## 17.2 Vendor / Business User

- Account registration
- Login
- Business profile
- Create payment code
- Create product/service
- Set price
- Change price
- Generate permanent QR
- View transactions
- View sales
- Basic settlement information

## 17.3 Customer

- Scan QR
- View merchant/product/service
- View amount where applicable
- Enter amount for variable QR
- Choose supported payment method
- Make payment
- Receive payment confirmation

## 17.4 Backend

- Authentication
- User and merchant management
- QR management
- Payment sessions
- Transaction management
- Paystack integration
- Webhooks
- Reconciliation
- Notifications

## 17.5 Admin

- User management
- Merchant management
- Transaction monitoring
- Pricing configuration
- Platform fee configuration
- Payment-provider configuration
- Reports
- Audit logs

## 17.6 Future Features

- WhatsApp integration
- Apple Pay where supported
- Google Pay where supported
- Advanced analytics
- Multiple staff accounts
- Digital receipts
- Inventory
- Customer accounts
- Loyalty features
- Additional payment providers
- Additional African markets

---

# 18. Core Product Principle

The entire Scan To Pay experience should be built around one simple idea:

> ## Scan. Pay. Done.

The merchant creates their payment identity once.

The QR code remains reusable.

The customer scans the QR code.

The platform determines what should be paid.

The customer completes the payment.

The payment provider processes the transaction.

Scan To Pay records and reconciles the transaction.

The merchant can continue using the same QR code for the next customer.

---

# 19. Important Business and Compliance Considerations

Scan To Pay should be structured as a technology/payment platform working with an appropriate regulated payment provider rather than attempting to become a payment processor itself.

Before launch, the business should obtain professional legal/compliance advice and written confirmation from the chosen payment provider regarding:

- Merchant onboarding
- Independent workers receiving tips
- Vendor and small-business accounts
- Subaccounts
- Split payments
- Platform fees
- Settlement flows
- Refunds
- Disputes
- Payment-provider terms
- Data protection and POPIA requirements
- Whether any part of the proposed model could be considered a regulated financial service

The platform should also avoid presenting itself as a bank or wallet unless the appropriate regulatory structure exists.

The initial product should focus on **payment acceptance and merchant payment management**, with funds processed and settled through the appropriate payment-provider infrastructure.

---

# 20. Long-Term Vision

Scan To Pay can start as a simple QR payment platform and expand into a broader digital commerce platform for small and informal businesses.

The long-term vision is to make digital payments accessible to businesses that traditionally find payment infrastructure too expensive, complicated, or inconvenient.

Potential future capabilities include:

```text
QR Payments
     |
     +---- Tips
     |
     +---- Products
     |
     +---- Services
     |
     +---- Taxi Payments
     |
     +---- Events
     |
     +---- Community Payments
     |
     +---- Digital Receipts
     |
     +---- Merchant Analytics
     |
     +---- WhatsApp Commerce
```

The core principle remains the same:

> **One platform. One payment identity. Reusable QR codes. Simple digital payments.**
