# Setting up Gmail API Access on Ubuntu

>**NOTE: I do not believer this is accurate but maybe of some use.

This guide outlines the steps to configure OAuth 2.0 credentials for the Gmail API and set up the necessary environment on your Ubuntu system.

## Part 1: Google Cloud Console Configuration

1. **Create a Project:**
    * Navigate to [Google Cloud Console](https://console.cloud.google.com/).
    * Click the project dropdown in the top navigation bar and select **New Project**.
    * Give your project a name (e.g., `gmail-api-project`) and click **Create**.

2. **Enable the Gmail API:**
    * In the sidebar, go to **APIs & Services > Library**.
    * Search for "Gmail API".
    * Click on **Gmail API** and then click **Enable**.

3. **Configure OAuth Consent Screen:**
    * Go to **APIs & Services > OAuth consent screen**.
    * Select **External** for User Type and click **Create**.
    * Fill in the required fields (App name, User support email, Developer contact information) and click **Save and Continue**.
    * Click **Save and Continue** through the "Scopes" and "Test users" steps (you can add yourself as a test user if needed,
      but for Desktop apps, this is often handled during the first auth flow).

4. **Create Credentials:**
    * Go to **APIs & Services > Credentials**.
    * Click **Create Credentials** and select **OAuth client ID**.
    * Under "Application type," select **Desktop app**.
    * Name it (e.g., `ubuntu-desktop-client`) and click **Create**.
    * A dialog will appear with your client ID and secret. Click **Download JSON** to save the file.

## Part 2: Ubuntu System Configuration

1. **Prepare the Directory:**
    Open your terminal on Ubuntu and create the required configuration directory:

    ```bash
    mkdir -p ~/.config/home-water-usage/
    ```

2. **Move the Credentials File:**
    Move the downloaded JSON file to the target location. Assuming the file is named `credentials.json` in your `~/Downloads` folder:

    ```bash
    mv ~/Downloads/credentials.json ~/.config/home-water-usage/credentials.json
    ```

3. **Set Permissions (Recommended):**
    Secure the credentials file so only your user can read it:

    ```bash
    chmod 600 ~/.config/home-water-usage/credentials.json
    ```

## Next Steps

You are now ready to use this `credentials.json` file in your Python scripts using the `google-auth-oauthlib` and `google-api-python-client` libraries. When you run your script for the first time, it will prompt you to open a browser to authenticate and generate a `token.json` file in the same directory.
