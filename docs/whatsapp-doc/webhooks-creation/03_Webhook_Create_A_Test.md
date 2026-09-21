# Create a test webhook endpoint



If you aren't ready to create your own webhook endpoint yet, you can deploy a test webhook app on [Render.com](https://www.render.com/) that accepts webhook requests and dumps their contents to Render's console.

_Only use this app for testing purposes._

## Requirements

- A [Render](https://www.render.com/) account.
- A [GitHub](https://www.github.com/) account.

## Step 1: Create a GitHub repository

Sign into your GitHub account and create a new repo (public or private) with a name of your choice. Within the repo, create an `app.js` file and paste this code into it:

```js
// Import Express.js
const express = require('express');

// Create an Express app
const app = express();

// Middleware to parse JSON bodies
app.use(express.json());

// Set port and verify_token
const port = process.env.PORT || 3000;
const verifyToken = process.env.VERIFY_TOKEN;

// Route for GET requests
app.get('/', (req, res) => {
  const { 'hub.mode': mode, 'hub.challenge': challenge, 'hub.verify_token': token } = req.query;

  if (mode === 'subscribe' && token === verifyToken) {
    console.log('WEBHOOK VERIFIED');
    res.status(200).send(challenge);
  } else {
    res.status(403).end();
  }
});

// Route for POST requests
app.post('/', (req, res) => {
  const timestamp = new Date().toISOString().replace('T', ' ').slice(0, 19);
  console.log(`\n\nWebhook received ${timestamp}\n`);
  console.log(JSON.stringify(req.body, null, 2));
  res.status(200).end();
});

// Start the server
app.listen(port, () => {
  console.log(`\nListening on port ${port}\n`);
});
```

## Step 2: Deploy a Node Express app on Render

Follow Render's instructions for [deploying a Node Express app](https://render.com/docs/deploy-node-express-app), with these differences:

- Skip step 1.
- Use these settings for step 3:
  - Build command: `npm install express`
  - Start command: `node app.js`
  - In the **Environment Variables** section, add the variable `VERIFY_TOKEN` and set it to a string of your choice (for example, `vibecode`).

When you're done, click the **Deploy your web service** button. Clicking **Deploy your web service** takes you to the app log where you will see your app being built, which can take a few minutes. You'll know it's done when you see "Your service is live" in the log.

Copy your deployed test webhook app URL, which appears at the top of the page under your GitHub repo name. (If you view the URL, you'll get a 403 error, which is expected).

## Step 3: Add your test webhook app URL to your Meta app

Open a new window/tab, and navigate to the (Meta) [App Dashboard](https://developers.facebook.com/apps) > **WhatsApp** > **Webhooks** > **Configuration** panel.

Paste your test webhook app URL in the **Callback URL** field, and add the `VERIFY_TOKEN` environment variable string you set earlier to the **Verify token** field, then click **Verify and save**.

If verification is successful, the Meta app dashboard should refresh and you should see a list of webhook fields you can subscribe to.

_Subscribe to the **messages** webhook field if you haven't already._

Also, in Render's app log, if you see "WEBHOOK VERIFIED", your test webhook app URL has been successfully verified.

## Step 4: Send a test message

Back in the Meta app dashboard **Configuration** panel, scroll down to the **messages** webhook field, subscribe to the field if you haven't already, then click the **Test** link.

Clicking the **Test** link sends a test message to your test webhook app. Confirm that it appears in Render app log with "Webhook received" followed by a test JSON payload:

## Troubleshooting

If the test **messages** webhook doesn't appear in the Render app dashboard log:

- Confirm that you successfully added your test webhook app URL to your Meta app (Step 3).
- Confirm that your app is subscribed to the **messages** webhook field.
- Make sure you are sending a **messages** test webhook; some test webhooks only work when your app is in Live mode, while others only work in Development mode (**messages** test webhooks work in both modes).
