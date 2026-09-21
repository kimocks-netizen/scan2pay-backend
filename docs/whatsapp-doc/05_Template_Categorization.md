# Template categorization



When creating a new template, or managing existing ones, it's important to understand how WhatsApp categorizes your template for pricing purposes.

1. Consider template category guidelines before creating a new template
1. Stay updated on your template's approval status after template creation
1. Learn about automatic category updates to templates in production

***This information is also available in PDF form in our Message templates category guidelines explainer PDF.***

## Template category guidelines

Our template category guidelines define the category of message templates. Message templates can be categorized as:

- **Marketing templates** – Enable businesses to achieve a wide range of goals, from generating awareness to driving sales and retargeting customers.
- **Utility templates** – Enable businesses to follow up on user actions or requests, since these messages are typically triggered by user actions.
- **Authentication templates** – Enable businesses to verify a user's identity, potentially at various steps of the customer journey.

### Marketing template guidelines

Marketing templates are the most flexible. They enable businesses to achieve a wide range of goals, from generating awareness to driving sales and more.

The following templates are also considered marketing:

- Templates with mixed content (for example, both utility and marketing, such as an order update with a promo or a feedback survey with promotional content).
- Templates where contents are unclear (for example, where contents are only "{{1}}" or "Congratulations!").

_Note: Examples are illustrative only. Templates that contain similar content, or the example text above, might be categorized differently based on the exact content._

| Message Objective | Business Goal | Example Templates |
| --- | --- | --- |
| **Awareness** | Generate awareness of your business, products, or services among customers who have subscribed to receive messages from your business on WhatsApp. | - Did you know? We installed a {{new_tower}} in your area so you can enjoy a better network experience. To learn more, visit our site.<br>- {{Diwali}} is around the corner! Join us at {{location}} on {{date}} to celebrate with friends and family. For more details about our event, click below.<br>- Looking for a getaway this fall? Our newest resort just opened in {{location}}: the perfect place to relax and unwind. |
| **Sales** | Send promotional offers to customers related to sales events, coupons, or other content intended to drive sales or renewals. | - As a thank you for your last order, please enjoy {{15}}% off your next order. Use code {{loyal15}} at checkout. Visit our site here below.<br>- We are actively seeking {{donations}} to meet our fundraising goal of {{amount}}. Support our cause and contribute now!<br>- Upgrade to our {{premium_cabin}} to enjoy new benefits, like {{more_legroom}} and {{priority_boarding}}. Click below or log into our app to upgrade.<br>- You have been {{pre_approved}} for our {{credit_card}}! Enjoy an introductory {{apr_rate}} if you apply via your personalized link below. |
| **Retargeting** | Promote or recommend offers, products, or services; attempt to renew subscriptions; or other calls to action to users who might have visited your website, used your app or engaged with you.<br>These are marketing even if requested by users. | - Your subscription will expire on {{date}}! Renew today to save {{discount}}.<br>- You left {{items}} in your cart! Don't worry, we saved them. Checkout now below.<br>- Your loan application is {{pending_approval}}! Please log in to pick up where you left off.<br>- We found a {{car}} that meets your saved search. Log in to our app to view.<br>- We apologize for the delay in your {{package}} delivery. We have deposited a {{credit}} to your account, available immediately. |
| **App Promotion** | Request customers to install or take a specific action with your app. | - Did you know? You can now {{checkout}} in our app. Download it below to use our streamlined experience.<br>- Thank you for using our app. We noticed you have not used our {{latest_feature}}. Click below to learn more about how this benefits you!<br>- In-app only: {{20}}% off this week! Use code {{summer_promo}} to save on select styles.<br>- Hi {{name}}, your friend {{name}} recently joined our community. Send them a welcome message in our app today: {{URL}}. |
| **Build Customer Relationships** | Strengthen customer relationships through personalized messages or by prompting new conversations. | - {{Name}}, did you think we'd forget? No way! {{Happy_birthday}}! We wish you the best in the year ahead.<br>- As we approach the end of the year, we reflect on what drives us: {{Name}}. Thank you for being a {{valued_customer}}. We look forward to continuing to serve you.<br>- Hello, I am the new {{virtual_assistant}}. I can help you discover products or provide support. Please reach out if I can help! |

### Utility template guidelines

Utility templates are typically triggered by a user action or request. For a template to be categorized as utility, it needs to meet both criteria below:

- _Must_ be **non-promotional**, not containing any promotional or persuasive intent.
- _Must_ ALSO be either **specific to or requested by the user** (clearly related to their order, account, services, or transactions) OR **essential or critical** to the user (for example, to ensure user safety).

| Message Objective | Business Goal | Example Templates |
| --- | --- | --- |
| **Opt-In Management on WhatsApp** | Confirm opt-in to receive messages on WhatsApp as a follow-up to opt-in collected via other channels (for example, website, email), or confirm opt-out. | - Thanks for confirming opt-in! You'll now receive notifications via WhatsApp.<br>- Thank you for confirming your opt-out preference. You will no longer receive messages from us on WhatsApp. |
| **Order Management** | Confirm, update, or cancel an order or transaction with a customer, using specific order or transaction details in the body of your message.<br><br>_These messages should not promote, recommend, upsell, or cross-sell products; include offers; or attempt to secure renewals._ | - Thank you! Your order {{order_number}} is confirmed. We will let you know once your package is on its way.<br>- Hooray! Your package from order {{order_number}} is on its way. Your tracking number is {{tracking_ID}} and expected delivery date is {{date}}.<br>- Unfortunately, one item from your order {{number}} is backordered. We will follow up with an estimated ship date. If you wish to cancel and receive a refund, please click below.<br>- We have received your item from order {{order_number}}. Your refund for ${{amount}} has been processed. Thank you for your business. |
| **Account Alerts or Updates** | Send important or time-sensitive updates or alerts or other information specific to purchased or subscribed products/services.<br><br>_These messages should not promote, recommend, upsell, or cross-sell products; include offers; or attempt to secure renewals._ | - Daily update for account ending in {{four_digit_number}}: Your available balance is {{amount}}.<br>- Reminder: Your monthly payment for {{service}} will be billed on {{date}} to the {{card}} you have saved on file.<br>- You only have {{number}} minutes remaining in your plan. Remember to top up your account by {{date}} to avoid disruptions.<br>- To finish setting up your {{new_profile}}, you need to upload a {{photo}}. Please click below to upload.<br>- Please note, we have updated our {{Customer_service}} phone number to {{number}}. Please save this and call if we can be of support. |
| **Feedback Surveys** | Collect feedback on previous orders, transactions, or engagements with customers.<br><br>_Specificity of the order or interaction to which these relate is necessary. A general/generic survey or request for feedback will not be approved as utility._ | - We have delivered your order {{order_number}}! Please let us know if there was any issue by reaching out below.<br>- Your feedback ensures we continually {{improve}}. Please click below to share your thoughts on your {{recent visit}} at our {{store}} location. Thank you in advance!<br>- You chatted with us {{online}} recently about order {{order_number}}. How was your experience? Click below to fill out a short survey. |
| **Continue a Conversation on WhatsApp** | Send a message to begin an interaction on WhatsApp that began in another channel.<br><br>_These messages should not be initiated without a user having requested the conversation to be moved to WhatsApp._ | - Hi! I see you requested support via our {{online_chat}}. I am the virtual assistant on WhatsApp. How can I help?<br>- Hi {{name}}, we are following up on your call with customer service on {{issue}}. Your case has progressed to the next step. Please log into your account to continue. |

For a utility template to be deemed essential or critical to the user, it must reflect one of the use cases below and must also be non-promotional (not containing any promotional or persuasive intent).

| Use Case Category | Use Case | Example that meets definition of "essential or critical to the user" |
| --- | --- | --- |
| **Public Safety** | Severe weather | There is a {{tornado}} alert in your area. We recommend you remain indoors until {{time}} today. |
| **Public Safety** | Crisis response | We activated support services for the {{crisis}} in the {{zip code}} area. Live updates on our site, available below. |
| **Public Service** | Health awareness | Stay up-to-date with your health. Stop by {{location}} by {{time}} to get your free COVID-19 {{vaccine}}. Bring your {{vaccination_card}} and identification document. |
| **Public Service** | Health emergency | The {{city}} has just declared a health emergency because of {{issue}}. We will follow up with more details once available. |
| **Public Service** | Voting registration | To vote on {{date}}, please ensure your voter {{registration card}} is active. Please click the URL below to understand steps required to renew, if needed. Please disregard this message if your {{registration card}} will be active. |
| **Public Service** | Disbursements | Your {{welfare}} disbursement balance is {{amount}}. Kindly note it will expire on {{date}}. |
| **Public Disruption** | System outages | We have detected a system outage that impacts zip code {{code}}. We expect to restore service by {{time_and_date}}. We apologize for the inconvenience. |
| **Public Disruption** | Operational disruption | This is to notify you that {{trains}} at our {{location}} station are halted because of {{issue}}. Please avoid the area as we work to rectify. |
| **Account or Product Protection** | Fraud awareness | We have detected an increase in {{ATM fraud}}. To protect your card ending in {{1234}}, please consider updating your PIN. Click below to see the step-by-step. |
| **Account or Product Protection** | Product recalls | The {{product}} you ordered on {{date}} has been recalled. Please click below to let us know how you would like to proceed. |
| **Account or Product Protection** | Warranty alerts | Thank you for your purchase of {{product}}. Your warranty is active as of {{date}}. Our {{product manuals}} are below, for your reference. |
| **Legal/Regulatory Compliance** | Identity compliance | This is to notify you that you need to upgrade to a {{updated_identification_card}} by {{date}}. To avoid any inconveniences when traveling, please ensure you make an appointment at your local {{office}}. |
| **Legal/Regulatory Compliance** | Privacy disclosures | We updated our privacy policy on {{date}}. Please click the button below to learn more. |
| **Legal/Regulatory Compliance** | Warranty alerts | Thank you for your purchase of {{product}}. Your warranty is active as of {{date}}. Our {{product manuals}} are below, for your reference. |

### Authentication template guidelines

_Note: Only authentication templates can be used to send a one-time passcode for identity verification. Marketing and utility templates cannot be used for this purpose._

You can use authentication templates from [Template Library](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-library). These templates include optional add-ons like security disclaimers and expiry warnings.

Authentication templates enable businesses to verify user identity (usually with alphanumeric codes) at various steps of the customer journey:

- New account creation
- Account integrity, access, or recovery
- New or existing orders/transactions

Authentication templates are our most restrictive, so for a template to be classified as authentication, **a business must**:

- Use Cloud API authentication message templates in [Template Library](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-library): These templates include optional add-ons like security disclaimers and expiry warnings.
- Configure a one-time password button: Such as [copy-code](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/authentication-templates/copy-code-button-authentication-templates) or [one-tap](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/authentication-templates/autofill-button-authentication-templates)
- Follow content restrictions: URLs, media, and emojis are not allowed for authentication template content or parameters. Parameters are also restricted to 15 characters.

#### Message objective: Authentication

| Message Objective | Business Goal | Example Templates |
| --- | --- | --- |
| **Authentication** | Authenticate users with one-time passcodes, potentially at multiple steps in the login process (for example, account verification, account recovery, integrity challenges). | - {{123456}} is your verification code. |

## How WhatsApp assigns a category during template creation

When you create a template, you indicate the template's category, based on the guidelines above. WhatsApp validates the category you indicated per the contents of the template and the [guidelines](#template-category-guidelines). The template is then created and its status is set to one of the statuses below, based on the outcome of the validation process.

a. When you create a template and it is approved, you can request a review up to 60 days from the creation date.

b. For utility templates that may be updated to marketing, you can request a review up to 60 days from the date the category was updated.

### Approved status

`APPROVED` status means WhatsApp agrees with the category chosen in your template creation request and that the template successfully passed [template review](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/overview#template-review). It can now be used to send messages.

**Status updates** — An email and WhatsApp Manager alert will inform you that the template was approved, and a [message_template_status_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/message_template_status_update) webhook will be triggered with the event property set to `APPROVED`.

**Warning:** Effective April 9, 2025, If you selected `UTILITY` as the template's category and WhatsApp determined it should be `MARKETING`, **the template is approved as `MARKETING`**. In WhatsApp Manager, you will see the screen below. When using the API, the behavior will be as outlined above. You can request a review up to 60 days from the date the category was updated.

**Warning:** Effective April 9, 2025 – The `allow_category_change` property during template creation. Previously, if set to `true` in a template creation request, this allowed us to update a template's category to `marketing`, if `marketing` to be its category was determined to be its category per its content and the guidelines. This is now the default behavior.

### Pending status

`PENDING` status means WhatsApp agrees with the category chosen in your template creation request, however the template is undergoing [template review](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/overview#template-review).

**Status Alerts** — The outcome of template review will be communicated via email and WhatsApp Manager alert. Upon completion, a [message_template_status_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/overview) webhook will be triggered with the event property set to `APPROVED` or `REJECTED`.

### Rejected status

`REJECTED` status indicates that WhatsApp disagreed with the category you designated in your template creation request.

**Status Alerts** — Rejections are communicated via email and WhatsApp Manager alert. Upon review completion, a [message_template_status_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/message_template_status_update) webhook will be triggered and the `event` property set to `REJECTED`, with the `reason` property set to `INCORRECT_CATEGORY`.

If your message template is rejected, you have the following options:

* [Create a new message template](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/overview) via WhatsApp Manager or the API.
* [Edit the template's category](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-management#edit-templates), and resubmit for approval.
* [Request a review](#how-to-request-a-category-review).

### Duplicated templates from phone number migration

All eligible templates are automatically duplicated in the destination WABA and category checks will be performed to ensure that all duplicated templates are correctly categorized.

## How WhatsApp updates a template's category after initial approval {#automatic-category-updates}

**Warning:** July 1, 2024 — To ensure templates on the platform are correctly categorized per the template category guidelines, WhatsApp introduced a recurring process to identify and update approved templates that should be of a different category, per the template category guidelines.

**Warning:** Effective April 16, 2025 — For any business detected to be abusing the template categorization system and to whom [a warning is sent](#notices-when-action-is-taken), the 24-hour notice mentioned below will no longer be provided if a utility template that should be marketing is detected. The category will be updated with no advance notice and emails/webhooks will be triggered to confirm the category change

Automatic category updates can apply to approved templates only that were not initially approved per the template category guidelines. Advance notice is provided on different surfaces, like through webhook and email, before action is taken on these templates.

### How it works

### For templates approved as **utility**, but should actually be **marketing**

* **Notice period** — A 1-day advance notice is provided before **the template category is updated to `marketing`**.
  * **As of April 16 2025 — If you are warned for template categorization misuse:**
    * 24 hour notice **will not** be provided before changing template categories from `UTILITY` to `MARKETING`
    * Category changes will be **instant**
* **Template category** — The template category is changed to `MARKETING`
* **Template status** — There is no change to template status; it remains `APPROVED` and can continue to be used to send messages.

### For templates approved as **marketing or utility**, but should actually be **authentication**

_This process was introduced on October 1, 2024_

* **Notice period** — Advance notice is provided.
* **Template category** — There is no change in the template's category.
* **Template status** — On the first day of the following month, the template status is changed to `REJECTED` and can no longer be used to send messages.

### **How you are notified**

### For templates approved as **utility**, but should actually be **marketing**

| Advanced notification of category updates | Description |
| --- | --- |
| _Via Email_ | * An email will be sent to any people in the business' portfolio with 'full control' of the WhatsApp Business account (WABA).<br>* The email will contain a link to the WhatsApp Manager > Message Templates > Manage Templates panel.<br>* Templates whose categories will be updated will have an "information" icon beside their name. Hovering over the icon will display the category it will be updated to, and the date when it will be updated.<br>* For templates that will be rejected, the icon will display |
| _Via Webhook_ | A [template_category_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/template_category_update) webhook will be triggered for each template whose category will be updated, with a `correct_category` property in the payload set to what the template's category should be. The `new_category` property also exists in the payload indicating the template's current category. |
| _Via WhatsApp Manager_ | * The WhatsApp Manager > Message Templates > Manage Templates panel will display a banner with a link to a downloadable CSV identifying these templates.<br>* [Business Support](https://business.facebook.com/business-support-home/) will list the name and current category of these templates, as well as the categories they will be updated to. |

| Notification when action is taken | Description |
| --- | --- |
| _Via Email_ | * An email will be sent to any people in the business portfolio who have been granted full control of the WABA that owns the templates whose categories have been updated.<br>* The email will highlight the number of templates whose categories were updated, and will include a link to the WhatsApp Manager > Message Templates > Manage Templates panel where the name and new category of these templates, as well as the categories before automatic update will be listed. It also includes a link to [Business Support](https://business.facebook.com/business-support-home/). |
| _Via Webhook_ | A [template_category_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/template_category_update) webhook will be triggered for each template whose category has been updated. The `new_category` property will indicate the template's new category and the `previous_category` property will indicate the template's category before automatic update. |

### For templates approved as **marketing or utility**, but should actually be **authentication**

| Advanced notification of category updates | Description |
| --- | --- |
| _Via Email_ | * An email will be sent to any people in the business portfolio who have been granted full control of the WABA that owns the templates whose categories have been updated.<br>* The email will contain a link to the WhatsApp Manager > Message Templates > Manage Templates panel.<br>* Templates whose status will be updated to `REJECTED` will be updated will have an "information" icon beside their name. Hovering over the icon will display the date when the template will be rejected. |
| _Via Webhook_ | *  A [template_category_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/template_category_update) webhook will be triggered for each template which will be rejected. |
| _Via WhatsApp Manager_ | * The WhatsApp Manager > Message Templates > Manage Templates panel will display a banner with a link to a downloadable CSV identifying these templates. [Business Support](https://business.facebook.com/business-support-home/) will list these as well. |

| Notification when action is taken | Description |
| --- | --- |
| _Via Email_ | * An email will be sent to any people in the business portfolio who have been granted full control of the WABA that owns the templates whose categories have been updated.<br>* The email will highlight the number of templates that were rejected, and will include a link to the WhatsApp Manager > Message Templates > Manage Templates panel, where the status will reflect the template is rejected.<br>* It also includes a link to [Business Support](https://business.facebook.com/business-support-home/). |
| _Via Webhook_ | A `status` webhook will be triggered for each template that has been rejected. whose category has been updated. The webhook will have the `event` property set to `REJECTED` and the reason property set to `INCORRECT_CATEGORY`. |

### Your options in this process

When you receive notice that a template's category will be updated or a template will be rejected, you can:

* Create a new template
* For **utility templates** that will be updated to **marketing**:
  * You can [request a review](#how-to-request-a-category-review):
    * If the review is approved – The template's category will not be updated as previously notified.
    * If the review is not approved – The template will be updated to marketing, as previously notified.
* For **marketing or utility templates** that will be **rejected**:
  * You cannot request a review.
  * Businesses on Cloud API can browse the [template library](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-library) to identify available options for your identity verification use case. It is recommended that businesses browse, choose, and create a new template from the [template library](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-library) before the utility/marketing template is rejected, to avoid workflow disruptions.

**You have 60 days to review and appeal these changes in [Business Support Home](https://business.facebook.com/business-support-home/).**

### Learn which template(s) will be updated or have been updated

### Via API

You can use the [Message Templates API](https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-account/message-template-api#get-version-waba-id-message-templates) to get the list of templates that have been or will be updated.

Request the `category` and `correct_category` fields, which will return the IDs of all of the WABA's templates, and each template's `category` and `correct_category` values. You can then compare these values:

```html
GET /<WHATSAPP_BUSINESS_ID>/message_templates?fields=category,correct_category
```

* If the values match (for example, they are both `MARKETING`), the template's category has already been updated with the `correct_category` value.
* If they mismatch and the `correct_category` is not an empty string or null (for example, category is `UTILITY` but `correct_category` is `MARKETING`), the template's category will be updated on the first day of the next month with the `correct_category` value.
* If the `correct_category` value is an empty string or null, the template has not been impacted.

### Via WhatsApp Manager

The WhatsApp Manager's Manage Templates panel identifies any templates whose categories will be updated.

## How to update a template category or request a category review

**Warning:** This process has been in effect since June 2023, when the marketing, utility, and authentication template categories were introduced.

### Edit your template's category

#### Via API

You can [edit template content or just its category](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-management#edit-templates).

* The template will undergo category validation and template review again.
* If the template passes validation and review, its category will be updated and a [template_category_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/template_category_update) webhook will be triggered.
* The `new_category` property in the webhook payload will indicate its new category.

#### Via WhatsApp Manager

On the **Manage Templates** tab:

1. Select your template
1. Edit the content so it aligns to the guidelines of that category
1. Re-submit the template for approval

If the template passes validation and review, its category will be updated and a [template_category_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/template_category_update) webhook will be triggered. The `new_category` property in the webhook payload will indicate its new category.

### Qualifications and outcomes for category review

You can request Meta to review the category of your template if:

* It is categorized as `UTILITY` or `MARKETING` and status is `REJECTED`
* It is categorized as `MARKETING` and status is `APPROVED`

Possible outcomes after you submit a request of your template's category:

* Review is approved – The category will be updated. A [template_category_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/template_category_update) webhook will be triggered. The `new_category` property in the webhook payload will indicate its new category.
* Review is rejected – The category will not change.

### How to request a category review

A review can only be requested via WhatsApp Manager.

In the sidebar of WhatsApp Manager, select the **Message Templates** dropdown, and then **Message Templates**. You should see a rejection banner with the template in question. Click **Go to Business Support**.

Click **Template Category Updates**, select the templates you would like reviewed and then click the **Request Review** button to begin the review process.

### How to view templates submitted for review

In the Business Support sidebar, click **Template category Updates**, and then the **In review** tab.

### How to view template category decisions

**If the template category change is not approved**: The template can be viewed in Business Support under the **Template category updates** > **Unchanged** tab. The template's category will change to the correct category during an automatic category update.

**If the template category change is approved**: the template can be viewed in Business Support under the **Template category updates** > **Reversed** tab. If the template category was already changed during automatic category update, it will be reverted to its previous category.

## Restrictions on businesses misusing the template categorization system

If a business is detected to be consistently misclassifying marketing templates as utility, WhatsApp may apply escalating restrictions.

### How it works

| Level | What happens | Duration |
| --- | --- | --- |
| **Warning** | A written warning is sent to WABA admins. After a warning, utility-to-marketing category changes become instant with no advance notice. | Ongoing |
| **Rate limiting** | Utility message volume on the WABA is capped within a 24-hour rolling window. Messages exceeding the cap are rejected. Marketing and authentication messages are not affected. | Minimum 7 days. Lifted once categorization quality improves. |
| **Utility restriction** | All approved utility templates on the WABA are recategorized to `MARKETING`. New utility template creation and [category reviews](#how-to-request-a-category-review) are disabled. After the restriction period ends, these capabilities are restored. | 7 days (30 days for repeat violations). |
| **Business portfolio level restriction** | If misuse persists across multiple WABAs under the same Meta Business Suite, all approved utility templates across all WABAs are recategorized to `MARKETING`. New utility template creation and [category reviews](#how-to-request-a-category-review) are disabled across all WABAs. After the restriction period ends, these capabilities are restored. | 30 days. |

**Warning:** **Repeat violations:** If continued misuse is detected after a prior restriction, enforcement may be reintroduced for longer periods and at a higher level.

### Notifications

You are notified of enforcement actions through the following channels:

* **Email**: Sent to all WABA admins (people with **Full control** of the WhatsApp Business account) when a warning, restriction, or lift occurs.
* **Webhook**: An `account_update` webhook is triggered with the `restriction_info` object reflecting the current enforcement state.

### Webhook events

When a WABA is enforced for utility template miscategorization, a webhook is sent via the `whatsapp_business_account` subscription. All enforcement events share this structure:

```json
{
  "field": "account_update",
  "value": {
    "event": "ACCOUNT_RESTRICTION",
    "violation_info": {
      "violation_type": "<violation_type>"
    },
    "restriction_info": [
      {
        "restriction_type": "<restriction_type>",
        "expiration": "<unix_timestamp>"
      }
    ]
  }
}
```

`restriction_info` is only present when an active restriction is being applied (rate limits, utility template suspensions). It is omitted for warnings and recovery events.

**Webhook values by enforcement scenario**

| Scenario | violation_type | restriction_info | restriction_type |
| --- | --- | --- | --- |
| Warning | `UTILITY_TEMPLATE_ABUSE` | Omitted | — |
| Utility Template Suspension | `UTILITY_TEMPLATE_ABUSE` | Present | `RESTRICTED_UTILITY_TEMPLATES` |
| Utility Template Suspension Removed | `UTILITY_TEMPLATE_ABUSE_UNBAN` | Omitted | — |
| Utility Messages Rate Limited | `UTILITY_TEMPLATE_ABUSE_RATE_LIMIT` | Present | `RATE_LIMITED_UTILITY_TEMPLATE_MESSAGING` |
| Utility Messages Rate Limit Removed | `UTILITY_TEMPLATE_ABUSE_RATE_LIMIT_RECOVERY` | Omitted | — |

### Your options in this process

If you believe specific templates were incorrectly recategorized, you can appeal at the template level via [Business Support](https://business.facebook.com/business-support-home/). Navigate to **Template Category Updates**, select the templates you would like reviewed, and click **Request Review**.
