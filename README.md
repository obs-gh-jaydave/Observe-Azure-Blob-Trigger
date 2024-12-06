# Azure Blob Trigger Function for Observability

This project processes different file types from an Azure Blob Storage container, converts them into Newline Delimited JSON (NDJSON), compresses the data with Gzip, and sends it to an Observe HTTP endpoint.

## Features
- Supports `.json`, `.ndjson`, `.txt`, and `.xml` file formats.
- Batches data to ensure payload size stays within Observe HTTP endpoint limits.
- Handles retries and logs responses for troubleshooting.

---

## Setup Instructions

### Prerequisites
1. Install [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) and log in using:
   ```bash
   az login
   ```
2. Set up Python 3.10 or higher and a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure your Azure Function Core Tools:
   ```bash
   npm install -g azure-functions-core-tools@4 --unsafe-perm true
   ```

---

### Environment Variables
Set the following environment variables in your `.env` file for local testing or in Azure Function Configuration for deployment:

- `OBSERVE_HTTP_ENDPOINT`: The Observe HTTP endpoint URL.
- `OBSERVE_API_TOKEN`: The authentication token for Observe.

Example `.env` file:
```env
OBSERVE_HTTP_ENDPOINT=https://<your_observe_endpoint>
OBSERVE_API_TOKEN=<your_api_token>
```

---

### Running Locally

1. Start the Azure Functions runtime locally:
   ```bash
   func start
   ```
2. Upload test files (e.g., `.json`, `.ndjson`, `.txt`, `.xml`) into your blob container.
3. Use the Azure CLI to upload a test file for processing:
   ```bash
   az storage blob upload \
       --account-name <storage_account_name> \
       --container-name <container_name> \
       --name sample_data.json \
       --file path/to/sample_data.json \
       --auth-mode login
   ```

---

### Deployment to Azure

1. Publish the Function App to Azure:
   ```bash
   func azure functionapp publish <function_app_name>
   ```
2. Configure Azure Blob Storage trigger:
   - Navigate to your Function App in the Azure Portal.
   - Add the `AzureWebJobsStorage` connection string in Application Settings.

---

### Testing

#### Locally
1. Add sample files in the `test_files` directory.
2. Upload them to your local storage emulator.

#### In Azure
1. Use the Azure CLI or Portal to upload files to your Azure Blob Storage container.
2. Check logs in Azure Portal or with the Azure CLI:
   ```bash
   az functionapp log tail --name <function_app_name>
   ```

---

## Project Structure

```plaintext
.
├── main.py             # Main Azure Function App code
├── requirements.txt    # Python dependencies
├── sample_data.json    # Example JSON test file
├── sample_data.ndjson  # Example NDJSON test file
├── sample_flattext.txt # Example plain text file
├── sample_data.xml     # Example XML test file
├── .env                # Local environment variables
├── .gitignore          # Git ignore file
└── README.md           # Project documentation
```