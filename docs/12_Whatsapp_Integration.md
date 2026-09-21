curl -i -X POST \
     https://graph.facebook.com/v25.0/1379297795259081/messages \
     -H 'Authorization: Bearer EAAPOewD0WFUBSmz4GJqQQlmUTZBJc519usTx3RFA8mjefNOgYU546KeBiXXDqgnux8DEOSSZBBuYrZAzgUF4xAAGjaUgYyN79SmNmjuANUbEZB87SyZAgp31l715e4ZAlEodwY0olkJ1ZBoyiUPp6CR00Tn1UU3o0GBpKERGpAbWrvetMcyHfmR6FtW5LaHGWVg8NRAZByPy3PaokdANNInKGnilzYVRCi3kdsYn' \
     -H 'Content-Type: application/json' \
     -d '{ "messaging_product": "whatsapp",
     "to": "27616583827",
     "type": "template",
     "template": { "name": "jaspers_market_plain_text_v1",
     "language": { "code": "en_US" } } }'



*** PHONE_ID: 1379297795259081
*** BUSINESS_ID: 1095598982856337
*** ACCESS_TOKEN: 

1379297795259081
PHONE_NUMBER: +1 (555) 147-8233

We'll use the temporary token to send a test message.

Once that works, we'll configure:

Meta Business Portfolio → System User → WhatsApp permissions → long-lived access token → AWS Parameter Store/Secrets storage.

