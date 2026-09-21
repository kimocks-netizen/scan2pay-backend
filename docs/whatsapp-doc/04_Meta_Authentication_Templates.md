# Authentication templates



If your mobile app offers users the option to receive one-time passwords or verification codes via WhatsApp, you must use an authentication template.

Authentication templates consist of:

* Fixed, non-customizable **preset text**: _<VERIFICATION_CODE> is your verification code._
* An optional **security disclaimer**: _For your security, do not share this code._
* An optional **expiration warning**: _This code expires in <NUM_MINUTES> minutes._
* Either a **one-tap autofill** button, a **copy code** button, or no button at all if using [zero-tap](#zero-tap-authentication-templates). Effective June 15, 2026, on iOS 26 and later, [Keyboard suggestions](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/authentication-templates/keyboard-suggestions) will provide native OTP autofill from the push notification.

One-tap autofill buttons are the preferred solution because they let users complete authentication without leaving the app. One-tap autofill buttons require additional changes to your Android app's code. Effective June 15, 2026, on iOS 26 and later, [Keyboard suggestions](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/authentication-templates/keyboard-suggestions) will provide native autofill from the push notification with no integration required.

## Linked device security

Authentication templates now feature linked device security. This means that authentication messages are only delivered to a user's primary WhatsApp device.

Authentication messages that are sent to a user's linked devices are masked with a prompt instructing the user to view the message on their primary device.

This feature is enabled by default and does not require code changes. Linked device security cannot be configured or customized. Only available on Cloud API.

## One-tap autofill authentication templates

Authentication templates include a one-tap autofill button.

When a WhatsApp user taps the autofill button, the WhatsApp client triggers an activity which opens your app and delivers it the password or code.

See [One-Tap Autofill Authentication Templates](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/authentication-templates/autofill-button-authentication-templates) to learn how to use them.

## Copy code authentication templates

Copy code authentication templates allow you to send a one-time password or code along with a copy code button to your users.

When a WhatsApp user taps the copy code button, the WhatsApp client copies the password or code to the device's clipboard. The user can then switch to your app and paste the password or code into your app.

See [Copy Code Authentication Templates](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/authentication-templates/copy-code-button-authentication-templates) to learn how to use them.

## Keyboard suggestions (iOS)

Effective June 15, 2026, [Keyboard suggestions](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/authentication-templates/keyboard-suggestions) will be enabled by default for all authentication templates. On iOS 26 and later, when a WhatsApp user receives an authentication code, iOS detects the OTP in the push notification and presents a one-tap autofill prompt in the keyboard. No integration changes are required.

## Zero-tap authentication templates

Zero-tap authentication templates allow your users to receive one-time passwords or codes via WhatsApp without having to leave your app.

When a user in your app requests a password or code and you deliver it using a zero-tap authentication template, the WhatsApp client broadcasts the included password or code, which your app can then capture with a broadcast receiver.

See [Zero-Tap Authentication Templates](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/authentication-templates/zero-tap-authentication-templates) to learn how to use them.

## Best practices

* Confirm the user's WhatsApp phone number before sending the one-time password or code to that number.
* Make it clear to your user that the password or code will be delivered to their WhatsApp phone number, especially if you offer multiple ways for the user to receive password or code delivery. See [Getting Opt-In](https://developers.facebook.com/documentation/business-messaging/whatsapp/getting-opt-in) for additional tips.
* When the user pastes the password or code into your app, or your app receives it as part of the one-tap autofill button flow, make it clear to the user that your app has captured it.

See also [Best practices for authenticating users via WhatsApp](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/authentication-templates/authentication-best-practices).

## Customizing time-to-live

See [Time-to-live](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/time-to-live).

## Template previews

You can generate previews of authentication template text in various languages that include or exclude the security recommendation string and code expiration string using the [Message Template Previews API](https://developers.facebook.com/docs/graph-api/reference/whats-app-business-account/message_template_previews#Reading).

### Request syntax

```html
GET /<WHATSAPP_BUSINESS_ACCOUNT_ID>/message_template_previews
  ?category=AUTHENTICATION,
  &language=<LANGUAGE>, // Optional
  &add_security_recommendation=<ADD_SECURITY_RECOMMENDATION>, // Optional
  &code_expiration_minutes=<CODE_EXPIRATION_MINUTES>, // Optional
  &button_types=<BUTTON_TYPES> // Optional
```

### Request parameters

| Placeholder | Description | Example Value |
| --- | --- | --- |
| `<LANGUAGE>`<br><br>_Comma-separated list_ | **Optional.**<br><br>Comma-separated list of [language codes](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/supported-languages) of language versions you want returned.<br><br>If omitted, versions of all supported languages will be returned. | `en_US,es_ES` |
| `<ADD_SECURITY_RECOMMENDATION>`<br><br>_Boolean_ | **Optional.**<br><br>Set to `true` if you want the security recommendation body string included in the response.<br><br>If omitted, the security recommendation string will not be included. | `true` |
| `<CODE_EXPIRATION_MINUTES>`<br><br>_Int64_ | **Optional.**<br><br>Set to an integer if you want the code expiration footer string included in the response.<br><br>If omitted, the code expiration footer string will not be included.<br><br>Value indicates number of minutes until code expires.<br><br>Minimum `1`, maximum `90`. | `10` |
| `<BUTTON_TYPES>`<br><br>_Comma-separated list of strings_ | **Required.**<br><br>Comma-separated list of strings indicating button type.<br><br>If included, the response will include the button text for each button in the response.<br><br>For authentication templates, this value must be `OTP`. | `OTP` |

### Example request

```html
curl 'https://graph.facebook.com/v17.0/102290129340398/message_template_previews?category=AUTHENTICATION&languages=en_US,es_ES&add_security_recommendation=true&code_expiration_minutes=10&button_types=OTP' \
-H 'Authorization: Bearer EAAJB...'
```

### Example response

```json
{
  "data": [
    {
      "body": "*{{1}}* is your verification code. For your security, do not share this code.",
      "buttons": [
        {
          "autofill_text": "Autofill",
          "text": "Copy code"
        }
      ],
      "footer": "This code expires in 10 minutes.",
      "language": "en_US"
    },
    {
      "body": "Tu código de verificación es *{{1}}*. Por tu seguridad, no lo compartas.",
      "buttons": [
        {
          "autofill_text": "Autocompletar",
          "text": "Copiar código"
        }
      ],
      "footer": "Este código caduca en 10 minutos.",
      "language": "es_ES"
    }
  ]
}
```

## Bulk management

Use the [Upsert Message Templates API](https://developers.facebook.com/docs/graph-api/reference/whats-app-business-account/upsert_message_templates#Creating) to bulk update or create authentication templates in multiple languages that include or exclude the optional security and expiration warnings.

If a template already exists with a matching name and language, the template will be updated with the contents of the request, otherwise, a new template will be created.

### Request syntax

```html
POST /<WHATSAPP_BUSINESS_ACCOUNT_ID>/upsert_message_templates
```

### Post body

```json
{
  "name": "<NAME>",
  "languages": [<LANGUAGES>],
  "category": "AUTHENTICATION",
  "components": [
    {
      "type": "BODY",
      "add_security_recommendation": <ADD_SECURITY_RECOMMENDATION> // Optional
    },
    {
      "type": "FOOTER",
      "code_expiration_minutes": <CODE_EXPIRATION_MINUTES> // Optional
    },
    {
      "type": "BUTTONS",
      "buttons": [
        {
          "type": "OTP",
          "otp_type": "<OTP_TYPE>",
          "supported_apps": [
            {
              "package_name": "<PACKAGE_NAME>", // One-tap and zero-tap buttons only
              "signature_hash": "<SIGNATURE_HASH>" // One-tap and zero-tap buttons only
            }
          ]
        }
      ]
    }
  ]
}
```

### Properties

All template creation properties are supported, with these exceptions:

* The `language` property is not supported. Instead, use `languages` and set its value to an array of [language and locale code](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/supported-languages) strings. For example: `["en_US","es_ES","fr"]`.
* The `text` property is not supported.
* The `autofill_text` property is not supported.

### Example copy code request

This example creates three authentication templates in English, Spanish, and French, with copy code buttons. Each template is named "authentication_code_copy_code_button" and includes the security recommendation and expiration time.

```html
curl 'https://graph.facebook.com/v17.0/102290129340398/upsert_message_templates' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer EAAJB...' \
-d '
{
  "name": "authentication_code_copy_code_button",
  "languages": ["en_US","es_ES","fr"],
  "category": "AUTHENTICATION",
  "components": [
    {
      "type": "BODY",
      "add_security_recommendation": true
    },
    {
      "type": "FOOTER",
      "code_expiration_minutes": 10
    },
    {
      "type": "BUTTONS",
      "buttons": [
        {
          "type": "OTP",
          "otp_type": "COPY_CODE"
        }
      ]
    }
  ]
}'
```

### Example one-tap autofill request

This example (1) updates an existing template with the name "authentication_code_autofill_button" and language "en_US", and (2) creates two new authentication templates in Spanish and French with one-tap autofill buttons. Both newly created templates are named "authentication_code_autofill_button" and include the security recommendation and expiration time.

```html
curl 'https://graph.facebook.com/v17.0/102290129340398/upsert_message_templates' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer EAAJB...' \
-d '
{
  "name": "authentication_code_autofill_button",
  "languages": ["en_US","es_ES","fr"],
  "category": "AUTHENTICATION",
  "components": [
    {
      "type": "BODY",
      "add_security_recommendation": true
    },
    {
      "type": "FOOTER",
      "code_expiration_minutes": 15
    },
    {
      "type": "BUTTONS",
      "buttons": [
        {
          "type": "OTP",
          "otp_type": "ONE_TAP",
          "supported_apps": [
            {
              "package_name": "com.example.luckyshrub",
              "signature_hash": "K8a/AINcGX7"
            }
          ]
        }
      ]
    }
  ]
}'
```

### Example response

```json
{
  "data": [
    {
      "id": "954638012257287",
      "status": "APPROVED",
      "language": "en_US"
    },
    {
      "id": "969725527415202",
      "status": "APPROVED",
      "language": "es_ES"
    },
    {
      "id": "969725530748535",
      "status": "APPROVED",
      "language": "fr"
    }
  ]
}
```

## Sample app

See our [WhatsApp One-Time Password (OTP) Sample App](https://github.com/WhatsApp/WhatsApp-OTP-Sample-App) for Android on GitHub. The sample app demonstrates how to send and receive OTP passwords and codes via the API, how to integrate the one-tap autofill and copy code buttons, how to create a template, and how to spin up a sample server.

## Learn more

* [Official Business Account](https://developers.facebook.com/documentation/business-messaging/whatsapp/official-business-accounts) — You may wish to request Official Business Account status to build trust with your users, which will reduce the likelihood that they dismiss or ignore your messages.
* [Status messages](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/messages/status) webhooks — Subscribe to the messages webhook field so you can be notified when a user receives and reads your authentication template with an OTP button.