# Webhook overrides



Meta sends webhooks to the callback URL set on your app, but you can override this by designating an alternate callback URL for the WhatsApp Business account (WABA) or business phone number.

When a [supported field](#supported-webhook-fields) triggers a webhook, the system first checks if your app has designated an alternate callback URL for the business phone number associated with the event. If the business phone number has an alternate callback URL, the system sends the webhook there. If the phone number has no alternate, the system checks if the WABA associated with the number has an alternate callback URL. If the WABA has an alternate callback URL, the system sends the webhook there. If the WABA also has no alternate, the webhook falls back to your app's callback URL.

## Supported webhook fields

The override applies only to the following webhook field types. For field types not listed here, Meta always sends webhooks to your app's default callback URL.

- `messages`
- `message_echoes`
- `calls`
- `consumer_profile`
- `messaging_handovers`
- `group_lifecycle_update`
- `group_participants_update`
- `group_settings_update`
- `group_status_update`
- `smb_message_echoes`
- `smb_app_state_sync`
- `history`
- `account_settings_update`

> **Note:** Template webhooks (`message_template_status_update`, `message_template_quality_update`, `message_template_components_update`, `template_category_update`) and account-level webhooks (`account_update`, `account_review_update`, `account_alerts`) do not support callback overrides. Meta always delivers these webhooks to your app's default callback URL.

## Requirements

Before setting an alternate callback URL, make sure your app is [subscribed to webhooks on the WABA](https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/manage-webhooks#subscribe-to-a-whatsapp-business-account) and verify that your alternate callback endpoint can receive and process webhooks correctly.

## Set WABA alternate callback

Use the [Subscribed Apps API](https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-account/subscribed-apps-api#post-version-waba-id-subscribed-apps) to set an alternate callback URL on a WABA.

### Request syntax

```html
POST /<WABA_ID>/subscribed_apps
```

### Post body

```json
{
  "override_callback_uri":"<WABA_ALT_CALLBACK_URL>",
  "verify_token":"<WABA_ALT_CALLBACK_URL_TOKEN>"
}
```

### Body parameters

| Placeholder | Description | Example value |
| --- | --- | --- |
| `<WABA_ALT_CALLBACK_URL>` | **Required.**<br><br>Alternate callback URL where [supported webhooks](#supported-webhook-fields) should be sent.<br><br>Maximum 200 characters. | `https://my-waba-alternate-callback.com/webhook` |
| `<WABA_ALT_CALLBACK_URL_TOKEN>` | **Required.**<br><br>Alternate callback URL [verification token](https://developers.facebook.com/docs/graph-api/webhooks/getting-started#verification-requests).<br><br>No maximum length. | `myvoiceismypassport?` |

### Response

Upon success:

```json
{
  "success": true
}
```

### Example request

```html
curl -X POST \
'https://graph.facebook.com/v25.0/102290129340398/subscribed_apps' \
-H 'Authorization: Bearer EAAJi...' \
-H 'Content-Type: application/json' \
-d '
{
  "override_callback_uri":"https://my-waba-alternate-callback.com/webhook",
  "verify_token":"myvoiceismypassport?"
}'
```

### Example response

```json
{
  "success": true
}
```

## Get WABA alternate callback

Use the [Subscribed Apps API](https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-account/subscribed-apps-api#get-version-waba-id-subscribed-apps) to get a list of all apps subscribed to webhooks on the WABA. The response should include an `override_callback_uri` property and value.

### Example response

```json
{
  "data" : [
    {
      "whatsapp_business_api_data" : {
        "id" : "670843887433847",
        "link" : "https://www.facebook.com/games/?app_id=67084...",
        "name" : "Lucky Shrub"
      },
      "override_callback_uri" : "https://my-waba-alternate-callback.com/webhook"
    }
  ]
}
```

## Delete WABA alternate callback

Use the [Subscribed Apps API](https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-account/subscribed-apps-api#post-version-waba-id-subscribed-apps) to subscribe your app to webhooks on the WABA [as you normally would](https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/manage-webhooks#subscribe) (that is, without any post body parameters). Subscribing without post body parameters removes the alternate callback URL from the WABA, and webhooks for the WABA will once again be sent to the callback URL set in the App Dashboard.

## Set phone number alternate callback

Use the [WhatsApp Business Phone Number API](https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-phone-number/whatsapp-business-account-phone-number-api#post-version-phone-number-id) to set an alternate callback URL on the business phone number.

### Request syntax

```html
POST /<BUSINESS_PHONE_NUMBER_ID>
```

### Post body

```json
{
  "webhook_configuration": {
    "override_callback_uri": "<PHONE_ALT_CALLBACK_URL>",
    "verify_token": "<PHONE_ALT_CALLBACK_URL_TOKEN>"
  }
}
```

### Body parameters

| Placeholder | Description | Example value |
| --- | --- | --- |
| `<PHONE_ALT_CALLBACK_URL>` | **Required.**<br><br>Alternate callback URL where [supported webhooks](#supported-webhook-fields) should be sent.<br><br>Maximum 200 characters. | `https://my-phone-alternate-callback.com/webhook` |
| `<PHONE_ALT_CALLBACK_URL_TOKEN>` | **Required.**<br><br>Alternate callback URL [verification token](https://developers.facebook.com/docs/graph-api/webhooks/getting-started#verification-requests).<br><br>No maximum length. | `myvoiceismypassport?` |

### Response

Upon success:

```json
{
  "success": true
}
```

### Example request

```html
curl -X POST 'https://graph.facebook.com/v25.0/106540352242922' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer EAAJB...' \
-d '
{
  "webhook_configuration": {
    "override_callback_uri": "https://my-phone-alternate-callback.com/webhook",
    "verify_token": "myvoiceismypassport?"
  }
}'
```

### Example response

```json
{
  "success": true
}
```

## Get phone number alternate callback

Use the [WhatsApp Business Phone Number API](https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-phone-number/whatsapp-business-account-phone-number-api#get-version-phone-number-id) and request the `webhook_configuration` field to verify that the business phone number has an alternate callback URL.

### Request syntax

```html
GET /<BUSINESS_PHONE_NUMBER_ID>
  ?fields=webhook_configuration
```

### Response

Upon success:

```json
{
  "webhook_configuration": {
    "phone_number": "<PHONE_ALT_CALLBACK_URL>",
    "whatsapp_business_account": "<WABA_ALT_CALLBACK_URL>",
    "application": "<APP_CALLBACK_URL>"
  },
  "id": "106540352242922"
}
```

The `whatsapp_business_account` property is only included if the WABA associated with the business phone number also has an alternate callback URL set.

### Example request

```html
curl 'https://graph.facebook.com/v25.0/106540352242922?fields=webhook_configuration' \
-H 'Authorization: Bearer EAAJB...'
```

### Example response

```json
{
  "webhook_configuration": {
    "phone_number": "https://my-phone-alternate-callback.com/webhook",
    "whatsapp_business_account": "https://my-waba-alternate-callback.com/webhook",
    "application": "https://my-production-callback.com/webhook"
  },
  "id": "106540352242922"
}
```

## Delete phone number alternate callback

To delete a business phone number's alternate callback URL, use the [WhatsApp Business Phone Number API](https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-phone-number/whatsapp-business-account-phone-number-api#post-version-phone-number-id) with the `override_callback_uri` property set to an empty string:

```json
{
  "webhook_configuration": {
    "override_callback_uri": ""
  }
}
```
