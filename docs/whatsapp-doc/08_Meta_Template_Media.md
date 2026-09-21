# Template media



A media header allows you to add an image, video, GIF, or document at the top of your WhatsApp template message.

Before creating the template, you must upload your media file using the Resumable Upload API. This upload returns a media ID, which you then use as the value for the `header_handle` field in the template's header component.

## Create a template with a media header

### Request syntax

Use the [Message Templates API](https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-account/message-template-api#post-version-waba-id-message-templates) to create a template with a media header.

```html
curl -X POST \
  'https://graph.facebook.com/<API_VERSION>/<WABA_ID>/message_templates' \
  -H 'Authorization: Bearer ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "limited_time_offer_tuscan_getaway_2023",
    "language": "en_US",
    "category": "MARKETING",
    "components": [
      {
        "type": "HEADER",
        "format": "IMAGE",
        "example": {
          "header_handle": [
            "4::aW..."
          ]
        }
      }
    ]
  }'
```

## Send media-based message template

Use the [Messages API](https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-phone-number/message-api#post-version-phone-number-id-messages) to send a media-based template message. Set the `type` property to `template` and use the template property to define your template object and its media object.

When defining your media object, you can either [upload your media asset](https://developers.facebook.com/documentation/business-messaging/whatsapp/business-phone-numbers/media#upload-media) to our servers and use its media ID (using the `id` property), or host the asset on your server and use its URL (using the `link` property). If you're using link, your asset must be on a publicly accessible server or the message will fail to send.

To reduce the likelihood of errors and avoid unnecessary requests to your public server, Meta recommends that you upload your media assets and use their IDs when sending messages.

You can also cache media assets. See [Media HTTP Caching](https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/send-messages#media-http-caching).

### Request syntax

```html
curl -X  POST \
 'https://graph.facebook.com/v23.0/FROM_PHONE_NUMBER_ID/messages' \
 -H 'Authorization: Bearer ACCESS_TOKEN' \
 -H 'Content-Type: application/json' \
 -d '{
  "messaging_product": "whatsapp",
  "recipient_type": "individual",
  "to": "PHONE_NUMBER",
  "type": "template",
  "template": {
    "name": "TEMPLATE_NAME",
    "language": {
      "code": "LANGUAGE_AND_LOCALE_CODE"
    },
    "components": [
      {
        "type": "header",
        "parameters": [
          {
            "type": "image",
            "image": {
              "link": "https://URL"
            }
          }
        ]
      },
      {
        "type": "body",
        "parameters": [
          {
            "type": "text",
            "text": "TEXT-STRING"
          },
          {
            "type": "currency",
            "currency": {
              "fallback_value": "VALUE",
              "code": "USD",
              "amount_1000": NUMBER
            }
          },
          {
            "type": "date_time",
            "date_time": {
              "fallback_value": "MONTH DAY, YEAR"
            }
          }
        ]
      }
    ]
  }
}'
```

A successful response includes an object with an identifier prefixed with WAM id. Use the ID listed after wamid to track your message status.

```curl
{
  "messaging_product": "whatsapp",
  "contacts": [{
      "input": "PHONE_NUMBER",
      "wa_id": "WHATSAPP_ID",
    }]
  "messages": [{
      "id": "wamid.ID",
    }]
}
```
