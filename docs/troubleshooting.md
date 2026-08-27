# Troubleshooting Guide

This document tracks common issues encountered during the initial setup of SketchTales V2.

### 1. n8n Crash Looping (QueryFailedError: permission denied for schema public)
**Issue:** When starting Docker for the first time, n8n may crash continuously because it cannot run database migrations. This happens because PostgreSQL 15+ changed the default permissions for the `public` schema.
**Solution:** The `init-data.sh` script has been updated to explicitly run `GRANT ALL ON SCHEMA public TO n8n;`. If you encounter this on an older setup, connect to the postgres container and run the grant manually.

### 2. Google OAuth 400 Error: redirect_uri_mismatch
**Issue:** When authenticating YouTube, Google throws an error about the redirect URI.
**Solution:** The `WEBHOOK_URL` environment variable must exactly match how you access n8n. If you access it via `http://localhost:5678`, then `WEBHOOK_URL` in `docker-compose.yml` must be `http://localhost:5678/`. Also, ensure you have copied the "OAuth Redirect URL" from inside the n8n credential screen and pasted it exactly into your Google Cloud OAuth Client ID configuration.

### 3. Google OAuth 403 Error: access_denied (N8n has not completed the Google verification process)
**Issue:** Google blocks the login because the app is in "Testing" mode.
**Solution:** In the Google Cloud Console, go to **OAuth consent screen**. Scroll down to **Test users** and add the exact email address you are trying to sign in with.

### 4. Cloudinary "Unauthorized" Error
**Issue:** n8n says it couldn't connect with the provided Cloudinary settings.
**Solution:** Ensure you copy all three keys from the "Product Environment Credentials" on your Cloudinary dashboard: **Cloud Name**, **API Key**, and **API Secret**. Do not copy the full environment variable URL.

### 5. Unrecognized node type: @blotato/n8n-nodes-blotato.blotato
**Issue:** Importing the workflow shows an unrecognized node error for the TikTok node.
**Solution:** n8n does not have a native free TikTok publisher, and the Blotato node is a paid plugin. Delete the TikTok node from the workflow. (This has been removed in V2).

### 6. Missing Cloudinary Node in Credentials
**Issue:** Cannot find Cloudinary when creating credentials.
**Solution:** The Cloudinary node is a Community Node. Go to **Settings > Community Nodes**, click **Install a community node**, and install `n8n-nodes-cloudinary`.

### 7. YouTube Node "Bad request - please check your parameters"
**Issue:** The native YouTube node expects a binary file, but we were passing it a URL.
**Solution:** An HTTP Request node must be inserted before the YouTube node to download the video from the Shotstack URL into a binary property (e.g. `data`), which the YouTube node then uploads. (Fixed in Part_3_V2).

### 8. Analyze an image: "The resource you are requesting could not be found"
**Issue:** The Gemini API rejects the image generation or analysis request because the model name is invalid or deprecated (e.g., `gemini-3-pro-preview`).
**Solution:** The model names in the workflow have been updated to use the correct production models (`gemini-1.5-flash` for analysis and `gemini-3.1-flash-image` for generation). (Fixed in Part_1_V2 and Part_2_V2).

### 9. Gemini Node: "The connection was aborted, perhaps the server is offline"
**Issue:** Node.js inside Docker can sometimes aggressively prefer IPv6, causing `ECONNRESET` or connection drops when talking to Google's API. Additionally, image analysis can take a long time, triggering n8n's default timeouts.
**Solution:** The `docker-compose.yml` file has been updated with `NODE_OPTIONS=--dns-result-order=ipv4first` to force IPv4, and `N8N_HTTP_TIMEOUT=120000` to extend the timeout window to 2 minutes.

### 10. Nano Banana Generate: "The service is receiving too many requests from you"
**Issue:** Google's image generation API (`gemini-3.1-flash-image` or Imagen) requires a billing account attached to your Google Cloud project, even if you are only using the Free Tier quota. If no billing account is linked, your image generation quota is effectively **0**, resulting in an instant 429 Too Many Requests error on your very first try.
**Solution:** Go to your Google Cloud Console and link a valid Billing Account to the project you used to generate the Gemini API key. Also, keep in mind that the Free Tier allows very few images per minute, so n8n is configured to automatically retry every 5 seconds if it hits a temporary speed bump.
