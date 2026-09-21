# Webhooks


This document describes webhooks and how the WhatsApp Business Platform uses them.

Webhooks are HTTP requests containing JSON payloads that Meta's servers send to a server of your designation. The WhatsApp Business Platform uses webhooks to inform you of incoming messages, the status of outgoing messages, and other important information, such as changes to your account status, messaging capability upgrades, and changes to your template quality scores.

For example, this is a webhook describing a message sent from a WhatsApp user to a business:

```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "102290129340398",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15550783881",
              "phone_number_id": "106540352242922"
            },
            "contacts": [
              {
                "profile": {
                  "name": "Sheena Nelson"
                },
                "wa_id": "16505551234"
              }
            ],
            "messages": [
              {
                "from": "16505551234",
                "id": "wamid.HBgLMTY1MDM4Nzk0MzkVAgASGBQzQTRBNjU5OUFFRTAzODEwMTQ0RgA=",
                "timestamp": "1749416383",
                "type": "text",
                "text": {
                  "body": "Does it come in another color?"
                }
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

## Create a webhook endpoint

To receive webhooks, you must create and configure a webhook endpoint. To create your own endpoint, see the [Create a webhook endpoint](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/create-webhook-endpoint) document.

If you aren't ready to create your own endpoint yet, you can [create a test webhook endpoint](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/set-up-whatsapp-echo-bot) that logs webhook payloads to the console. Note, however, that before you can use your app in a production capacity, you must create your own endpoint.

## Permissions

You need the following permissions to receive webhooks:

- **whatsapp_business_messaging** — for **messages** webhooks
- **whatsapp_business_management** — for all other webhooks

If you are a direct developer, use your system user to grant your app these permissions when generating your [system token](https://developers.facebook.com/documentation/business-messaging/whatsapp/access-tokens#system-user-access-tokens).

If you are a [partner](https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/overview) and need these permissions to provide appropriate services to your business customers, you must be approved for advanced access for the permissions via [App Review](https://developers.facebook.com/docs/app-review) before your business customers will be able to grant your app these permissions during onboarding.

## Fields

Once you have [created and configured](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/create-webhook-endpoint) your webhook endpoint (or have set up a [test webhook endpoint](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/set-up-whatsapp-echo-bot)), use the **[App Dashboard](https://developers.facebook.com/apps)** > **WhatsApp** > **Configuration** panel to subscribe to individual webhook fields.

Note that if you created your app using the **Connect with customers through WhatsApp** use case, navigate to **[App Dashboard](https://developers.facebook.com/apps)** > **Use cases** > **Customize** > **Configuration** instead.

| Field name | Description |
| --- | --- |
| [account_alerts](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/account_alerts) | The **account_alerts** webhook notifies you of changes to a business phone number's [messaging limit](https://developers.facebook.com/documentation/business-messaging/whatsapp/messaging-limits), [business profile](https://developers.facebook.com/documentation/business-messaging/whatsapp/business-phone-numbers/phone-numbers#business-profiles), and [Official Business Account](https://developers.facebook.com/documentation/business-messaging/whatsapp/whatsapp-business-accounts#official-business-account) status. |
| [account_review_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/account_review_update) | The **account_review_update** webhook notifies you when a WhatsApp Business Account has been reviewed against our policy guidelines. |
| [account_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/account_update) | The **account_update** webhook notifies of changes to a WhatsApp Business Account's [partner-led business verification](https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/partner-led-business-verification) submission, its [authentication-international rate](https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing/authentication-international-rates) eligibility, or primary business location, when it is shared with a [Solution Partner](https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/overview), [policy or terms violations](https://developers.facebook.com/documentation/business-messaging/whatsapp/policy-enforcement), offboarding, reconnection, or when it is deleted. |
| [automatic_events](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/automatic_events) | The **automatic_events** webhook notifies you when we detect a purchase or lead event in a chat thread between you and a WhatsApp user who has messaged you via your Click to WhatsApp ad, if you have opted-in to [Automatic Events](https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/automatic-events-api) reporting. |
| [business_capability_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/business_capability_update) | The **business_capability_update** webhook notifies you of WhatsApp Business Account or business portfolio capability changes ([messaging limits](https://developers.facebook.com/documentation/business-messaging/whatsapp/messaging-limits#increasing-your-limit), [phone number limits](https://developers.facebook.com/documentation/business-messaging/whatsapp/business-phone-numbers/phone-numbers#registered-number-cap), etc.). |
| [history](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/history) | The **history** webhook is used to synchronize the [WhatsApp Business app chat history](https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/onboarding-business-app-users) of a business customer onboarded by a solution provider. |
| [message_template_components_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/message_template_components_update) | The **message_template_components_update** webhook notifies you of changes to a template's components. |
| [message_template_quality_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/message_template_quality_update) | The **message_template_quality_update** webhook notifies you of changes to a template's [quality score](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-quality). |
| [message_template_status_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/message_template_status_update) | The **message_template_status_update** webhook notifies you of changes to the status of an existing template. |
| [messages](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/messages) | The **messages** webhook describes messages sent from a WhatsApp user to a business and the status of messages sent by a business to a WhatsApp user. |
| [partner_solutions](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/partner_solutions) | The **partner_solutions webhook** describes changes to the status of a [Multi-Partner Solution](https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/multi-partner-solutions). |
| [payment_configuration_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/payment_configuration_update) | The **payment_configuration_update** webhook notifies you of changes to payment configurations for [Payments API India](https://developers.facebook.com/documentation/business-messaging/whatsapp/payments/payments-in/overview) and [Payments API Brazil](https://developers.facebook.com/documentation/business-messaging/whatsapp/payments/payments-br/overview). |
| [phone_number_name_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/phone_number_name_update) | The **phone_number_name_update** webhook notifies you of business phone number [display name verification](https://developers.facebook.com/documentation/business-messaging/whatsapp/display-names#display-name-verificationn) outcomes. |
| [phone_number_quality_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/phone_number_quality_update) | The **phone_number_quality_update** webhook notifies you of changes to a business phone number's [throughput level](https://developers.facebook.com/documentation/business-messaging/whatsapp/throughput). |
| [security](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/security) | The **security** webhook notifies you of changes to a business phone number's security settings. |
| [smb_app_state_sync](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/smb_app_state_sync) | The **smb_app_state_sync** webhook is used for synchronizing contacts of [WhatsApp Business app users who have been onboarded](https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/onboarding-business-app-users) via a solution provider. |
| [smb_message_echoes](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/smb_message_echoes) | The **smb_message_echoes** webhook notifies you of messages sent via the WhatsApp Business app or a [companion ("linked") device](https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/onboarding-business-app-users#linked-devices) by a business customer who has been [onboarded to Cloud API](https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/onboarding-business-app-users) via a solution provider. |
| [template_category_update](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/template_category_update) | The **template_category_update** webhook notifies you of changes to template's [category](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-categorization). |
| [user_preferences](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/user_preferences) | The **user_preferences** webhook notifies you of changes to a WhatsApp user's [marketing message preferences](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/marketing-templates#user-preferences-for-marketing-messages). |

## Override webhooks

You can use an alternate webhook endpoint for [certain webhook fields](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/override#supported-webhook-fields) for your WhatsApp Business account (WABA) or business phone number. An alternate endpoint can be useful for testing purposes, or if you are a partner and wish to use unique webhook endpoints for each of your onboarded customers.

See the [Webhook overrides](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/override) document to learn how to override webhooks.

## Payload size

Webhook payloads can be up to 3 MB.

## Webhook delivery failure

If a webhook request to your endpoint receives an HTTP status code other than 200, or if the webhook cannot be delivered for another reason, Meta retries delivery with decreasing frequency until the request succeeds, for up to 7 days.

Note that Meta sends retries to all apps that have subscribed to webhooks (and their appropriate fields) for the WhatsApp Business account. These retries can result in duplicate webhook notifications.

## Mutual TLS

Webhooks support mutual TLS (mTLS) for added security. See Graph API's [mTLS for webhooks](https://developers.facebook.com/docs/graph-api/webhooks/getting-started#mtls-for-webhooks) document to learn how to enable and use mTLS.

## IP addresses

You can get the IP addresses of Meta's webhook servers by running the following command in your terminal:

```bash
whois -h whois.radb.net — '-i origin AS32934' | grep '^route' | awk '{print $2}' | sort
```

You can also use the geofeed to [download a CSV](https://facebook.com/peering/geofeed) that lists Meta's IP addresses.

Note, however, that Meta periodically changes its IP addresses, so to avoid having to regenerate your list of allowed IP addresses, consider [using mTLS instead](https://developers.facebook.com/docs/graph-api/webhooks/getting-started#mtls-for-webhooks).

## Troubleshooting

If you are not receiving webhooks:

- Make sure your endpoint is accepting requests.
- Send a test payload to your endpoint via the **[App Dashboard](https://developers.facebook.com/apps)** > **WhatsApp** > **Configurations** panel.
- Make sure your app is in **Live** mode; some webhooks will not be sent if your app is in **Dev** mode.
- Use the [test webhook endpoint](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/set-up-whatsapp-echo-bot). If the test endpoint is digesting webhook payloads and displaying them in the console, the issue is likely with your endpoint code.

## Learn more

- See the [Using Node.js to implement webhooks](https://business.whatsapp.com/blog/how-to-use-webhooks-from-whatsapp-business-api) WhatsApp Business blog post.
