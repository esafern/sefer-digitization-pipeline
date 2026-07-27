import os
from google.cloud import documentai

def process_document(project_id, location, processor_id, file_path, output_json_path):
    """
    Sends a PDF to Document AI and saves the complete coordinate map as a JSON file.
    """
    # Instantiate a client
    client = documentai.DocumentProcessorServiceClient()

    # The full resource name of the processor
    name = client.processor_path(project_id, location, processor_id)

    # Read the file into memory
    with open(file_path, "rb") as image:
        image_content = image.read()

    # Load Binary Data into Document AI RawDocument object
    raw_document = documentai.RawDocument(
        content=image_content, mime_type="application/pdf"
    )

    # Configure the process request
    request = documentai.ProcessRequest(
        name=name,
        raw_document=raw_document
    )

    print(f"Sending {file_path} to Document AI...")
    result = client.process_document(request=request)
    
    # Write the full output to a JSON file
    document = result.document
    json_payload = documentai.Document.to_json(document)
    
    with open(output_json_path, "w", encoding="utf-8") as f:
        f.write(json_payload)
        
    print(f"Success! Saved spatial map to {output_json_path}")
    print(f"Extracted {len(document.pages[0].tokens)} individual words.")

if __name__ == "__main__":
    # TODO: Replace these with your actual IDs
    PROJECT_ID = "gen-lang-client-0289907848"
    LOCATION = "us"
    PROCESSOR_ID = "4d3d4f204562f1d6"
    
    PDF_FILE = "test_page.pdf"
    OUTPUT_FILE = "document.json"
    
    # Ensure credentials are set
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("Error: GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")
    else:
        process_document(PROJECT_ID, LOCATION, PROCESSOR_ID, PDF_FILE, OUTPUT_FILE)
