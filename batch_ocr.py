import os
from google.cloud import documentai, storage

def batch_process_document(
    project_id: str,
    location: str,
    processor_id: str,
    gcs_input_uri: str,
    gcs_output_uri: str,
    output_local_dir: str
):
    """
    Runs asynchronous batch processing for multi-page PDFs exceeding synchronous limits.
    Updated for strict Protobuf dict initialization in modern SDK versions.
    """
    client_options = {"api_endpoint": f"{location}-documentai.googleapis.com"}
    client = documentai.DocumentProcessorServiceClient(client_options=client_options)

    name = client.processor_path(project_id, location, processor_id)

    # Use dicts instead of class instances to satisfy SDK Protobuf constraints
    input_config = {
        "gcs_documents": {
            "documents": [
                {
                    "gcs_uri": gcs_input_uri,
                    "mime_type": "application/pdf"
                }
            ]
        }
    }

    # The correct key is gcs_output_config, not gcs_destination
    output_config = {
        "gcs_output_config": {
            "gcs_uri": gcs_output_uri
        }
    }

    request = documentai.BatchProcessRequest(
        name=name,
        input_documents=input_config,
        document_output_config=output_config
    )

    print(f"Triggering asynchronous batch job for: {gcs_input_uri}")
    operation = client.batch_process_documents(request=request)
    
    print("Waiting for Document AI batch operation to complete...")
    operation.result()
    print("Batch processing complete. Downloading coordinate JSON files from GCS...")

    # Download output shards from GCS bucket to local directory
    storage_client = storage.Client()
    bucket_name = gcs_output_uri.replace("gs://", "").split("/")[0]
    
    # Safely construct the prefix
    parts = gcs_output_uri.replace("gs://", "").split("/")[1:]
    prefix = "/".join([p for p in parts if p]) 
    
    os.makedirs(output_local_dir, exist_ok=True)
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    
    for blob in blobs:
        if blob.name.endswith(".json"):
            dest_file = os.path.join(output_local_dir, os.path.basename(blob.name))
            blob.download_to_filename(dest_file)
            print(f"Downloaded spatial map: {dest_file}")

if __name__ == "__main__":
    # --- CONFIGURATION ---
    PROJECT_ID = "gen-lang-client-0289907848"
    LOCATION = "us"
    PROCESSOR_ID = "4d3d4f204562f1d6"
    
   # GCS_INPUT = "gs://your-bucket-name/raw_pdfs/yad_malachi_vol1.pdf"
   # GCS_OUTPUT = "gs://your-bucket-name/ocr_output/"
   # LOCAL_OUTPUT_DIR = "./document_jsons"

# If your bucket is named "yad-malachi-ocr-data"
    GCS_INPUT = "gs://yad-malachi-ocr-data/test_page.pdf"
    GCS_OUTPUT = "gs://yad-malachi-ocr-data/ocr_output/"
    LOCAL_OUTPUT_DIR = "./document_jsons"
    
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("Error: GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")
    else:
        batch_process_document(
            PROJECT_ID, LOCATION, PROCESSOR_ID, 
            GCS_INPUT, GCS_OUTPUT, LOCAL_OUTPUT_DIR
        )
