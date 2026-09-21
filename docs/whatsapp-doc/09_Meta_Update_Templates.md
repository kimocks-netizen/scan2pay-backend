

## Base URL

| URL | Description |
|-----|-------------|
| https://graph.facebook.com | Production Graph API server |

## APIs

| Method | Endpoint |
|--------|----------|
| DELETE | [/{Version}/{WABA-ID}/message_templates](#delete-version-waba-id-message-templates) |
| GET | [/{Version}/{TEMPLATE_ID}](#get-version-template-id) |
| GET | [/{Version}/{WABA-ID}/message_templates](#get-version-waba-id-message-templates) |
| POST | [/{Version}/{TEMPLATE_ID}](#post-version-template-id) |
| POST | [/{Version}/{WABA-ID}/message_templates](#post-version-waba-id-message-templates) |

<jumplink id="delete-version-waba-id-message-templates"></jumplink>
## DELETE /{Version}/{WABA-ID}/message_templates

Delete Message Templates

Delete message templates from a WhatsApp Business Account. Can delete by name
(all languages), by specific template ID, or by multiple template IDs.


### Header Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| User-Agent | string |  | The user agent string identifying the client software making the request. |
| Authorization | string | ✓ | Bearer token for API authentication. This should be a valid access token obtained through the appropriate OAuth flow or system user token. |

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| Version | string | ✓ | Graph API version |
| WABA-ID | string | ✓ | WhatsApp Business Account ID |

### Query Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string |  | Template name to delete (deletes all languages if hsm_id not specified) |
| hsm_id | string |  | Specific template ID to delete (used with name for single-language deletion) |
| hsm_ids | string |  | JSON array of template IDs to delete (max 100) |

### Responses

**200**

Templates deleted successfully

**Content Type**: `application/json`

**Schema**: [SuccessResponse](#successresponse)

**Example**:\n```json\n{
    "success": true
}\n```

**400**

Bad Request

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "Invalid parameter",
        "type": "OAuthException",
        "code": 100,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn"
    }
}\n```

**401**

Unauthorized

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "Invalid OAuth access token",
        "type": "OAuthException",
        "code": 190,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn"
    }
}\n```

**500**

Internal Server Error

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "An unexpected error occurred",
        "type": "GraphMethodException",
        "code": 2,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn",
        "is_transient": true
    }
}\n```


<jumplink id="get-version-template-id"></jumplink>
## GET /{Version}/{TEMPLATE_ID}

Get Message Template by ID

Retrieve a specific message template by its ID with all available fields.


### Header Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| User-Agent | string |  | The user agent string identifying the client software making the request. |
| Authorization | string | ✓ | Bearer token for API authentication. This should be a valid access token obtained through the appropriate OAuth flow or system user token. |

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| Version | string | ✓ | Graph API version |
| TEMPLATE_ID | string | ✓ | Message template ID |

### Query Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| fields | string |  | Comma-separated list of fields to include in the response. Available fields: id, ad_account_id, ad_adset_id, ad_campaign_id, ad_id, bid_spec, category, components, correct_category, cta_url_link_tracking_opted_out, degrees_of_freedom_spec, display_format, health_status, is_primary_device_delivery_only, is_sms_fallback_enabled, language, last_updated_time, library_template_name, message_send_ttl_seconds, name, parameter_format, previous_category, quality_score, rejected_reason, source, status, sub_category |

### Responses

**200**

Successfully retrieved message template

**Content Type**: `application/json`

**Schema**: [MessageTemplate](#messagetemplate)

**400**

Bad Request

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "Invalid parameter",
        "type": "OAuthException",
        "code": 100,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn"
    }
}\n```

**401**

Unauthorized

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "Invalid OAuth access token",
        "type": "OAuthException",
        "code": 190,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn"
    }
}\n```

**404**

Not Found

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "Template not found",
        "type": "GraphMethodException",
        "code": 803,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn"
    }
}\n```

**500**

Internal Server Error

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "An unexpected error occurred",
        "type": "GraphMethodException",
        "code": 2,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn",
        "is_transient": true
    }
}\n```


<jumplink id="get-version-waba-id-message-templates"></jumplink>
## GET /{Version}/{WABA-ID}/message_templates

List Message Templates

Retrieve message templates for a WhatsApp Business Account. Returns paginated
results with template details including status, category, components, and quality scores.


### Header Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| User-Agent | string |  | The user agent string identifying the client software making the request. |
| Authorization | string | ✓ | Bearer token for API authentication. This should be a valid access token obtained through the appropriate OAuth flow or system user token. |

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| Version | string | ✓ | Graph API version |
| WABA-ID | string | ✓ | WhatsApp Business Account ID |

### Query Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| fields | string |  | Comma-separated list of fields to include in the response. Available fields: id, ad_account_id, ad_adset_id, ad_campaign_id, ad_id, bid_spec, category, components, correct_category, cta_url_link_tracking_opted_out, degrees_of_freedom_spec, display_format, health_status, is_primary_device_delivery_only, is_sms_fallback_enabled, language, last_updated_time, library_template_name, message_send_ttl_seconds, name, parameter_format, previous_category, quality_score, rejected_reason, source, status, sub_category |
| limit | integer [min: 1] |  | Maximum number of templates to return per page |
| after | string |  | Cursor for next page of results |
| before | string |  | Cursor for previous page of results |

### Responses

**200**

Successfully retrieved message templates

**Content Type**: `application/json`

**Schema**: [MessageTemplatesResponse](#messagetemplatesresponse)

**400**

Bad Request

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "Invalid parameter",
        "type": "OAuthException",
        "code": 100,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn"
    }
}\n```

**401**

Unauthorized

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "Invalid OAuth access token",
        "type": "OAuthException",
        "code": 190,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn"
    }
}\n```

**403**

Forbidden

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "Insufficient permissions to access templates",
        "type": "OAuthException",
        "code": 200,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn"
    }
}\n```

**404**

Not Found

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "WhatsApp Business Account not found",
        "type": "GraphMethodException",
        "code": 803,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn"
    }
}\n```

**500**

Internal Server Error

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "An unexpected error occurred",
        "type": "GraphMethodException",
        "code": 2,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn",
        "is_transient": true
    }
}\n```


<jumplink id="post-version-template-id"></jumplink>
## POST /{Version}/{TEMPLATE_ID}

Edit Message Template

Update an existing message template. Only approved or rejected templates can be edited.


### Header Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| User-Agent | string |  | The user agent string identifying the client software making the request. |
| Authorization | string | ✓ | Bearer token for API authentication. This should be a valid access token obtained through the appropriate OAuth flow or system user token. |

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| Version | string | ✓ | Graph API version |
| TEMPLATE_ID | string | ✓ | Message template ID to edit |

### Request Body (Required)

**Content Type**: `application/json`

**Schema**: object

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| components | array of object |  | Updated template components |
| category | [WhatsAppBusinessHSMTag](#whatsappbusinesshsmtag) |  |  |
| parameter_format | [BusinessMessagingHSMParameterFormat](#businessmessaginghsmparameterformat) |  |  |
| allow_category_change | boolean |  | Allow Meta to reassign the template category |
| cta_url_link_tracking_opted_out | boolean |  | Opt out of CTA URL link tracking |
| message_send_ttl_seconds | integer |  | Time-to-live for messages using this template |
| sub_category | [WhatsAppBusinessHSMTagSubCategory](#whatsappbusinesshsmtagsubcategory) |  |  |
| display_format | [WhatsAppBusinessMessageDisplayFormat](#whatsappbusinessmessagedisplayformat) |  |  |
| is_primary_device_delivery_only | boolean |  | Restrict to primary device delivery only |

### Responses

**200**

Template updated successfully

**Content Type**: `application/json`

**Schema**: [SuccessResponse](#successresponse)

**Example**:\n```json\n{
    "success": true
}\n```

**400**

Bad Request

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "Invalid parameter",
        "type": "OAuthException",
        "code": 100,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn"
    }
}\n```

**401**

Unauthorized

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "Invalid OAuth access token",
        "type": "OAuthException",
        "code": 190,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn"
    }
}\n```

**500**

Internal Server Error

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "An unexpected error occurred",
        "type": "GraphMethodException",
        "code": 2,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn",
        "is_transient": true
    }
}\n```


<jumplink id="post-version-waba-id-message-templates"></jumplink>
## POST /{Version}/{WABA-ID}/message_templates

Create Message Template

Create a new message template for a WhatsApp Business Account. Templates must be
approved before they can be used to send messages.


### Header Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| User-Agent | string |  | The user agent string identifying the client software making the request. |
| Authorization | string | ✓ | Bearer token for API authentication. This should be a valid access token obtained through the appropriate OAuth flow or system user token. |

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| Version | string | ✓ | Graph API version |
| WABA-ID | string | ✓ | WhatsApp Business Account ID |

### Request Body (Required)

**Content Type**: `application/json`

**Schema**: object

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| name | string | ✓ | Template name (lowercase alphanumeric and underscores only) |
| language | string | ✓ | Template language code |
| category | [WhatsAppBusinessHSMTag](#whatsappbusinesshsmtag) | ✓ |  |
| parameter_format | [BusinessMessagingHSMParameterFormat](#businessmessaginghsmparameterformat) |  |  |
| components | array of object |  | Template components |
| allow_category_change | boolean |  | Allow Meta to reassign the template category |
| cta_url_link_tracking_opted_out | boolean |  | Opt out of CTA URL link tracking |
| message_send_ttl_seconds | integer |  | Time-to-live for messages using this template |
| sub_category | [WhatsAppBusinessHSMTagSubCategory](#whatsappbusinesshsmtagsubcategory) |  |  |
| display_format | [WhatsAppBusinessMessageDisplayFormat](#whatsappbusinessmessagedisplayformat) |  |  |
| library_template_name | string |  | Name of the library template to clone |
| library_template_button_inputs | array of object |  | Button inputs for library template cloning |
| library_template_body_inputs | object |  | Body inputs for library template cloning |
| is_primary_device_delivery_only | boolean |  | Restrict to primary device delivery only |
| send_type | [WhatsAppBusinessMarketingMessagesHSMSendType](#whatsappbusinessmarketingmessageshsmsendtype) |  |  |

### Responses

**200**

Template created successfully

**Content Type**: `application/json`

**Schema**: [CreateTemplateResponse](#createtemplateresponse)

**400**

Bad Request

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "Invalid parameter: name must contain only lowercase alphanumeric characters and underscores",
        "type": "OAuthException",
        "code": 100,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn"
    }
}\n```

**401**

Unauthorized

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "Invalid OAuth access token",
        "type": "OAuthException",
        "code": 190,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn"
    }
}\n```

**403**

Forbidden

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "Insufficient permissions to create templates",
        "type": "OAuthException",
        "code": 200,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn"
    }
}\n```

**500**

Internal Server Error

**Content Type**: `application/json`

**Schema**: [GraphAPIError](#graphapierror)

**Example**:\n```json\n{
    "error": {
        "message": "An unexpected error occurred",
        "type": "GraphMethodException",
        "code": 2,
        "fbtrace_id": "AXsgnV2Cm3ZMGF3dF_cfYIn",
        "is_transient": true
    }
}\n```


# Components

## Schemas

<jumplink id="messagetemplate"></jumplink>
### MessageTemplate

WhatsApp Business message template (HSM)

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| id | string |  | Unique identifier for the message template |
| ad_account_id | string |  | Associated ad account ID for click-to-WhatsApp ad templates |
| ad_adset_id | string |  | Associated ad set ID |
| ad_campaign_id | string |  | Associated ad campaign ID |
| ad_id | string |  | Associated ad group ID |
| bid_spec | [Bid_spec](#object-bid_spec-1) |  | Bid specification for marketing message templates |
| category | [WhatsAppBusinessHSMTag](#whatsappbusinesshsmtag) |  |  |
| components | array of [Components](#object-components-4) |  | Template components (header, body, footer, buttons) |
| correct_category | [WhatsAppBusinessHSMTag](#whatsappbusinesshsmtag) |  |  |
| cta_url_link_tracking_opted_out | boolean |  | Whether CTA URL link tracking is opted out |
| degrees_of_freedom_spec | object |  | Marketing message creative degrees of freedom specification |
| display_format | [WhatsAppBusinessMessageDisplayFormat](#whatsappbusinessmessagedisplayformat) |  |  |
| health_status | [Health_status](#object-health_status-5) |  | Health status information for the template |
| is_primary_device_delivery_only | boolean |  | Whether this template is restricted to primary device delivery only |
| is_sms_fallback_enabled | boolean |  | Whether SMS fallback is enabled for this template |
| language | string |  | Language code of the template |
| last_updated_time | integer (int64) |  | Unix timestamp when the template was last updated |
| library_template_name | string |  | Name of the library template this was created from |
| message_send_ttl_seconds | integer (int64) |  | Time-to-live in seconds for messages sent using this template |
| name | string |  | Name of the template |
| parameter_format | [BusinessMessagingHSMParameterFormat](#businessmessaginghsmparameterformat) |  |  |
| previous_category | [WhatsAppBusinessHSMTag](#whatsappbusinesshsmtag) |  |  |
| quality_score | [Quality_score](#object-quality_score-6) |  | Quality score information for the template |
| rejected_reason | [WhatsAppBusinessHSMRejectionReason](#whatsappbusinesshsmrejectionreason) |  |  |
| source | [WhatsAppBusinessHSMSource](#whatsappbusinesshsmsource) |  |  |
| status | [WhatsAppBusinessHSMStatus](#whatsappbusinesshsmstatus) |  |  |
| sub_category | [WhatsAppBusinessHSMTagSubCategory](#whatsappbusinesshsmtagsubcategory) |  |  |

<jumplink id="whatsappbusinesshsmtag"></jumplink>
### WhatsAppBusinessHSMTag

Template category

**Type**: string

**Enum Values**: "AUTHENTICATION", "FREE_SERVICE", "MARKETING", "UTILITY"

<jumplink id="whatsappbusinesshsmstatus"></jumplink>
### WhatsAppBusinessHSMStatus

Current status of the message template

**Type**: string

**Enum Values**: "APPROVED", "ARCHIVED", "DELETED", "DISABLED", "IN_APPEAL", "LIMIT_EXCEEDED", "PAUSED", "PENDING", "PENDING_DELETION", "REJECTED"

<jumplink id="whatsappbusinesshsmtagsubcategory"></jumplink>
### WhatsAppBusinessHSMTagSubCategory

Template sub-category for utility templates

**Type**: string

**Enum Values**: "BOOKING_STATUS", "CALL_PERMISSIONS_REQUEST", "FLIGHT_DELAY_AND_GATE_CHANGE_ALERT", "FRAUD_ALERT", "ORDER_DETAILS", "ORDER_STATUS", "RICH_ORDER_STATUS"

<jumplink id="businessmessaginghsmparameterformat"></jumplink>
### BusinessMessagingHSMParameterFormat

Parameter format for the template

**Type**: string

**Enum Values**: "NAMED", "POSITIONAL"

<jumplink id="whatsappbusinesshsmqualityscore"></jumplink>
### WhatsAppBusinessHSMQualityScore

Quality score rating for the template

**Type**: string

**Enum Values**: "GREEN", "RED", "UNKNOWN", "YELLOW"

<jumplink id="whatsappbusinesshsmrejectionreason"></jumplink>
### WhatsAppBusinessHSMRejectionReason

Reason the template was rejected

**Type**: string

**Enum Values**: "ABUSIVE_CONTENT", "CATEGORY_NOT_AVAILABLE", "INCORRECT_CATEGORY", "INVALID_FORMAT", "NONE", "PROMOTIONAL", "SCAM", "TAG_CONTENT_MISMATCH"

<jumplink id="whatsappbusinesshsmsource"></jumplink>
### WhatsAppBusinessHSMSource

How the template was created

**Type**: string

**Enum Values**: "auto_generated", "manual"

<jumplink id="whatsappbusinessmessagedisplayformat"></jumplink>
### WhatsAppBusinessMessageDisplayFormat

Display format for the template

**Type**: string

**Enum Values**: "ORDER_DETAILS"

<jumplink id="whatsappbusinessmarketingmessageshsmsendtype"></jumplink>
### WhatsAppBusinessMarketingMessagesHSMSendType

Send type for marketing message templates

**Type**: string

**Enum Values**: "campaign", "direct"

<jumplink id="messagetemplatesresponse"></jumplink>
### MessageTemplatesResponse

Response containing list of message templates with pagination

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| data | array of [MessageTemplate](#messagetemplate) |  | Array of message templates |
| paging | [CursorPaging](#cursorpaging) |  |  |

<jumplink id="cursorpaging"></jumplink>
### CursorPaging

Cursor-based pagination information

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| cursors | [Cursors](#object-cursors-7) |  |  |
| next | string |  | URL for the next page of results |
| previous | string |  | URL for the previous page of results |

<jumplink id="successresponse"></jumplink>
### SuccessResponse

Generic success response

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| success | boolean |  | Whether the operation was successful |

<jumplink id="createtemplateresponse"></jumplink>
### CreateTemplateResponse

Response after creating a message template

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| id | string |  | ID of the created template |
| status | [WhatsAppBusinessHSMStatus](#whatsappbusinesshsmstatus) |  |  |
| category | [WhatsAppBusinessHSMTag](#whatsappbusinesshsmtag) |  |  |

<jumplink id="graphapierror"></jumplink>
### GraphAPIError

Standard Graph API error response

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| error | [Error](#object-error-8) | ✓ |  |

## Inline Object Definitions

<jumplink id="object-bid_spec-1"></jumplink>
### Bid_spec

Bid specification for marketing message templates

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| bid_strategy | string |  | Bid strategy for the template |
| bid_amount | integer |  | Bid amount in currency minor units |

<jumplink id="object-buttons-2"></jumplink>
### Buttons

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| type | One of "CATALOG", "COPY_CODE", "FLOW", "MPM", "OTP", "PHONE_NUMBER", "QUICK_REPLY", "URL" |  | Button type |
| text | string |  | Button label text |
| url | string |  | URL for URL buttons |
| phone_number | string |  | Phone number for call buttons |
| otp_type | One of "COPY_CODE", "ONE_TAP", "ZERO_TAP" |  | OTP button type for authentication templates |
| autofill_text | string |  | Autofill button text for one-tap OTP buttons |
| package_name | string |  | Android package name for one-tap OTP buttons |
| signature_hash | string |  | Android app signature hash for one-tap OTP buttons |
| flow_id | string |  | Flow ID for flow buttons |
| flow_name | string |  | Flow name for flow buttons (alternative to flow_id) |
| flow_json | string |  | Inline flow JSON definition for flow buttons |
| flow_action | One of "data_exchange", "navigate" |  | Flow action type |
| navigate_screen | string |  | Screen ID to navigate to for flow buttons |

<jumplink id="object-example-3"></jumplink>
### Example

Example values for template parameters

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| header_text | array of string |  | Example values for header text parameters |
| header_handle | array of string |  | Media handle IDs for header media examples |
| body_text | array of array of string |  | Example values for body text parameters |

<jumplink id="object-components-4"></jumplink>
### Components

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| type | One of "BODY", "BUTTONS", "CAROUSEL", "FOOTER", "HEADER", "LIMITED_TIME_OFFER" |  | Component type |
| text | string |  | Text content of the component |
| format | One of "DOCUMENT", "IMAGE", "LOCATION", "TEXT", "VIDEO" |  | Format of the header component |
| buttons | array of [Buttons](#object-buttons-2) |  | Button components |
| add_security_recommendation | boolean |  | Whether to add security recommendation text to authentication templates |
| code_expiration_minutes | integer |  | OTP code expiration time in minutes for authentication templates |
| example | [Example](#object-example-3) |  | Example values for template parameters |

<jumplink id="object-health_status-5"></jumplink>
### Health_status

Health status information for the template

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| can_send_message | string |  | Whether messages can be sent using this template |

<jumplink id="object-quality_score-6"></jumplink>
### Quality_score

Quality score information for the template

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| score | [WhatsAppBusinessHSMQualityScore](#whatsappbusinesshsmqualityscore) |  |  |
| reason | string |  | Reason for the current quality score |
| reasons | array of string |  | List of reasons affecting the quality score |
| date | integer (int64) |  | Unix timestamp of the quality score evaluation |

<jumplink id="object-cursors-7"></jumplink>
### Cursors

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| before | string |  | Cursor pointing to the start of the page |
| after | string |  | Cursor pointing to the end of the page |

<jumplink id="object-error-8"></jumplink>
### Error

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| message | string | ✓ | Human-readable error message |
| type | string | ✓ | Error category type |
| code | integer | ✓ | Numeric error code |
| error_subcode | integer |  | More specific error subcode |
| fbtrace_id | string |  | Unique identifier for debugging |
| is_transient | boolean |  | Whether this error is temporary |
| error_user_title | string |  | User-friendly error title |
| error_user_msg | string |  | User-friendly error message |

## Authentication

| Scheme | Type | Location |
|--------|------|----------|
| bearerAuth | HTTP Bearer | Header: `Authorization` |

### Usage Examples

- **bearerAuth**: Include `Authorization: Bearer your-token-here` in request headers

### Global Authentication Requirements

All endpoints require: bearerAuth
