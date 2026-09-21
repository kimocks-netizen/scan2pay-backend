# template_category_update webhook reference



This reference describes trigger events and payload contents for the WhatsApp Business account **template_category_update** webhook.

The **template_category_update** webhook notifies you of changes to template's [category](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-categorization).


## Triggers

- The existing category of a WhatsApp template is going to be changed by an [automated process](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-categorization#how-we-update-a-template-s-category-after-initial-approval).
- The existing category of a WhatsApp template is changed manually or by an [automated process](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-categorization#how-we-update-a-template-s-category-after-initial-approval).

## Syntax

```html
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "<WHATSAPP_BUSINESS_ACCOUNT_ID>",
      "time": <WEBHOOK_TRIGGER_TIMESTAMP>,
      "changes": [
        {
          "field": "template_category_update",
          "value": {
            "message_template_id": <TEMPLATE_ID>,
            "message_template_name": "<TEMPLATE_NAME>",
            "message_template_language": "<TEMPLATE_LANGUAGE>",

            <!-- impending category change notifications only -->
            "correct_category": "<CORRECT_CATEGORY>",
            "new_category": "<CURRENT_CATEGORY>",
            "category_update_timestamp": <CATEGORY_UPDATE_TIMESTAMP>

            <!-- completed category change notifications only -->
            "previous_category": "<PREVIOUS_CATEGORY>",
            "new_category": "<NEW_CATEGORY>"

          }
        }
      ]
    }
  ]
}
```

## Parameters

| Placeholder | Description | Example value |
| --- | --- | --- |
| `<CORRECT_CATEGORY>`<br><br>_String_ | The category that the template will be [recategorized](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-categorization#how-we-update-a-template-s-category-after-initial-approval) as in 24 hours. | `MARKETING` |
| `<CURRENT_CATEGORY>`<br><br>_String_ | The template's current [category](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/overview#template-categories). | `MARKETING` |
| `<NEW_CATEGORY>`<br><br>_String_ | The template's new [category](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/overview#template-categories). | `MARKETING` |
| `<CATEGORY_UPDATE_TIMESTAMP>`<br><br>_Integer_ | The Unix timestamp (in seconds) indicating when the template's category will be updated to the `<CORRECT_CATEGORY>` specified in the webhook. This value represents the moment the update is scheduled to occur. | `1760711433` |
| `<PREVIOUS_CATEGORY>`<br><br>_String_ | The template's previous [category](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/overview#template-categories). | `UTILITY` |
| `<TEMPLATE_ID>`<br><br>_Integer_ | Template ID. | `278077987957091` |
| `<TEMPLATE_LANGUAGE>`<br><br>_String_ | Template [language and locale code](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/supported-languages). | `en-US` |
| `<TEMPLATE_NAME>`<br><br>_String_ | Template name. | `welcome_template` |
| `<WEBHOOK_TRIGGER_TIMESTAMP>`<br><br>_Integer_ | Unix timestamp indicating when the webhook was triggered. | `1739321024` |
| `<WHATSAPP_BUSINESS_ACCOUNT_ID>`<br><br>_String_ | WhatsApp Business Account ID. | `102290129340398` |

## Examples

This example webhook describes a template that will be recategorized as `MARKETING` in 24 hours. Note that `new_category` indicates its _current_ category:

```json
{
 "entry": [
   {
     "id": "102290129340398",
     "time": 1746082800,
     "changes": [
       {
         "field": "template_category_update",
         "value": {
           "message_template_id": 278077987957091,
           "message_template_name": "welcome_template",
           "message_template_language": "en-US",
           "new_category": "UTILITY",
           "correct_category": "MARKETING",
           "category_update_timestamp": 1746169200
         }
       }
     ]
   }
 ],
 "object": "whatsapp_business_account"
}
```

This example webhook describes a template that has been recategorized as `MARKETING`:

```json
{
 "entry": [
   {
     "id": "102290129340398",
     "time": 1746169200,
     "changes": [
       {
         "field": "template_category_update",
         "value": {
           "message_template_id": 278077987957091,
           "message_template_name": "welcome_template",
           "message_template_language": "en-US",
           "previous_category": "UTILITY",
           "new_category": "MARKETING"
         }
       }
     ]
   }
 ],
 "object": "whatsapp_business_account"
}
```
