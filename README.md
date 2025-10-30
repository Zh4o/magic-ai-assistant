# Your Team Dinner Concierge

This is a Streamlit web application that acts as an intelligent concierge named "Sam" to help users plan team dinners. Sam chats with the user to gather necessary details and then saves them to a Google Sheet.

## Features

-   **Conversational AI**: Powered by the Google Gemini API to naturally gather planning details.
-   **Interactive Chat Interface**: A clean and modern chat UI built with Streamlit.
-   **Guided Conversation**: The app guides the user to provide all necessary information, including party size, occasion, budget, and contact details.
-   **Google Sheets Integration**: Automatically saves the finalized details into a specified Google Sheet for easy tracking.
-   **Smart UI**: The "Finalize" button only appears after the AI has confirmed it has collected all required information, including a contact email.

## Prerequisites

-   Python 3.11+
-   A Google Cloud Platform (GCP) account.
-   A Google Gemini API Key.
-   A Google Sheet to store the data.

## Setup Instructions

Follow these steps to get the application running on your local machine.

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <your-repository-directory>
```

### 2. Install Dependencies

It's recommended to use a virtual environment.

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install the required Python packages
pip install -r requirements.txt
```

*(You will need to create a `requirements.txt` file containing at least `streamlit`, `google-generativeai`, and `gspread`)*

### 3. Configure Your Secrets

This application uses Streamlit's secrets management. You need to create a file named `secrets.toml` inside a `.streamlit` directory.

1.  Create the directory:
    ```bash
    mkdir .streamlit
    ```

2.  Create the secrets file:
    ```bash
    touch .streamlit/secrets.toml
    ```

3.  Add the following content to `.streamlit/secrets.toml` and fill in your details:

    ```toml
    # .streamlit/secrets.toml

    [gemini]
    GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

    [google_sheet]
    GOOGLE_SHEET_KEY = "YOUR_GOOGLE_SHEET_KEY"

    [gcp_service_account]
    type = "service_account"
    project_id = "your-gcp-project-id"
    private_key_id = "your-private-key-id"
    private_key = "-----BEGIN PRIVATE KEY-----\n ...your-full-private-key... \n-----END PRIVATE KEY-----\n"
    client_email = "your-service-account-email@your-project-id.iam.gserviceaccount.com"
    client_id = "your-client-id"
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account-email%40your-project-id.iam.gserviceaccount.com"
    universe_domain = "googleapis.com"
    ```

### 4. How to Get Your Secrets

-   **`GEMINI_API_KEY`**:
    1.  Go to the [Google AI Studio](https://aistudio.google.com/).
    2.  Click on "**Get API key**" and create a new key.

-   **`GOOGLE_SHEET_KEY`**:
    1.  Create a new Google Sheet.
    2.  The key is the long string of characters in the URL: `https://docs.google.com/spreadsheets/d/THIS_IS_THE_KEY/edit#gid=0`

-   **`gcp_service_account`**:
    1.  Go to your [Google Cloud Console](https://console.cloud.google.com/).
    2.  In your project, navigate to **IAM & Admin > Service Accounts**.
    3.  Create a new service account (e.g., "streamlit-sheet-writer").
    4.  Go to the **Keys** tab for that account, click **Add Key > Create new key**, and download the **JSON** file.
    5.  **Important**: Enable the **Google Drive API** and **Google Sheets API** for your GCP project. You can do this by searching for them in the "APIs & Services" library.
    6.  Copy the contents of the downloaded JSON file and paste them into your `secrets.toml` file, making sure the `private_key` formatting is correct (it must be enclosed in triple quotes if it contains newlines, or you can handle it as a single line string with `\n`).
    7.  Finally, **share your Google Sheet** with the `client_email` address from your service account JSON file, giving it "Editor" permissions.

## Running the App

Once your secrets are configured, you can run the app with the following command:

```bash
streamlit run app.py
```

Open your web browser to the local URL provided by Streamlit, and you can start chatting.