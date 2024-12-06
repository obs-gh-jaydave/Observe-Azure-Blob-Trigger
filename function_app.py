import azure.functions as func
import logging
import gzip
import json
import requests
import os
import xmltodict  # To handle XML parsing

app = func.FunctionApp()

# Constants for Observe limits
MAX_UNCOMPRESSED_SIZE = 4 * 1024 * 1024  # 4 MB
MAX_COMPRESSED_SIZE = 10 * 1024 * 1024  # 10 MB

@app.blob_trigger(arg_name="myblob", path="mycontainer/{name}", connection="AzureWebJobsStorage")
def blob_trigger(myblob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob: "
                 f"Name: {myblob.name}, Blob Size: {myblob.length} bytes")

    # Set up environment variables
    OBSERVE_HTTP_ENDPOINT = os.getenv("OBSERVE_HTTP_ENDPOINT")
    OBSERVE_API_TOKEN = os.getenv("OBSERVE_API_TOKEN")

    try:
        # Read blob data
        blob_data = myblob.read()
        formatted_data = process_blob_content(blob_data, myblob.name)

        if not formatted_data:
            logging.error("No valid data to send to Observe.")
            return

        # Batch and send data
        batch_and_send_to_observe(formatted_data, OBSERVE_HTTP_ENDPOINT, OBSERVE_API_TOKEN)

    except Exception as e:
        logging.error(f"Error processing blob: {e}")


def process_blob_content(blob_content, file_name):
    """
    Process blob content based on the file type and convert it into a list of JSON objects.
    """
    try:
        # Check file extension to determine format
        if file_name.endswith(".ndjson"):
            return handle_ndjson(blob_content)
        elif file_name.endswith(".json"):
            return handle_json(blob_content)
        elif file_name.endswith(".txt"):
            return handle_flat_text(blob_content)
        elif file_name.endswith(".xml"):
            return handle_xml(blob_content)
        else:
            logging.error(f"Unsupported file type for {file_name}")
            return None
    except Exception as e:
        logging.error(f"Error processing blob content for {file_name}: {e}")
        return None


def handle_ndjson(blob_content):
    """Handle NDJSON files (Newline Delimited JSON)."""
    try:
        log_lines = blob_content.decode("utf-8").strip().splitlines()
        return [json.loads(line) for line in log_lines]
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing NDJSON content: {e}")
        return None


def handle_json(blob_content):
    """Handle JSON files (either single JSON object or NDJSON)."""
    try:
        # Attempt to parse as NDJSON
        log_lines = blob_content.decode("utf-8").strip().splitlines()
        return [json.loads(line) for line in log_lines]
    except json.JSONDecodeError:
        # If not NDJSON, treat as a single JSON object
        try:
            single_object = json.loads(blob_content.decode("utf-8"))
            return [single_object]
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON content: {e}")
            return None


def handle_flat_text(blob_content):
    """Handle plain text files by converting each line into a JSON object."""
    lines = blob_content.decode("utf-8").strip().splitlines()
    return [{"line_number": i + 1, "content": line} for i, line in enumerate(lines)]


def handle_xml(blob_content):
    """Handle XML files by converting them into JSON objects."""
    try:
        xml_dict = xmltodict.parse(blob_content.decode("utf-8"))
        return [xml_dict]
    except Exception as e:
        logging.error(f"Error parsing XML content: {e}")
        return None


def batch_and_send_to_observe(data, endpoint, token):
    """
    Batch data into chunks that meet Observe's HTTP endpoint limits and send each batch.
    """
    batch = []
    current_uncompressed_size = 0

    for observation in data:
        serialized = json.dumps(observation)
        size = len(serialized.encode("utf-8"))

        if current_uncompressed_size + size > MAX_UNCOMPRESSED_SIZE:
            # Send current batch
            send_batch(batch, endpoint, token)
            # Start a new batch
            batch = []
            current_uncompressed_size = 0

        batch.append(observation)
        current_uncompressed_size += size

    # Send any remaining data
    if batch:
        send_batch(batch, endpoint, token)


def send_batch(batch, endpoint, token):
    """Send a single batch of observations to the Observe HTTP endpoint."""
    ndjson_data = "\n".join(json.dumps(entry) for entry in batch)

    # Compress the data
    gzipped_data = gzip.compress(ndjson_data.encode("utf-8"))

    # Check compressed size
    if len(gzipped_data) > MAX_COMPRESSED_SIZE:
        logging.error("Compressed batch exceeds Observe's 10 MB limit. Consider reducing batch size.")
        return

    # Send to Observe
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-type": "application/x-ndjson",
        "Content-encoding": "gzip",
    }

    try:
        response = requests.post(endpoint, headers=headers, data=gzipped_data)
        logging.info(f"Observe Response: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error sending batch to Observe: {e}")
