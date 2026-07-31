import google.generativeai as genai
import os
from PIL import Image

def run_gemini_ocr():
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    pro_models = [m for m in available_models if 'pro' in m]
    model_name = pro_models[0] if pro_models else 'models/gemini-flash-latest'
    print(f"Using model: {model_name}")
    model = genai.GenerativeModel(model_name)
    
    img = Image.open('scratch/page49-049.png')
    
    prompt = """
    Please transcribe the Hebrew text in this image perfectly, word for word.
    Pay extreme attention to distinguishing between Dalet (ד) and Resh (ר).
    Maintain the original paragraph structure and Klal numbers.
    Do not add any Markdown formatting or translation, just output the raw Hebrew text.
    """
    
    response = model.generate_content([prompt, img])
    
    with open("scratch/page49_gemini_ocr.txt", "w", encoding="utf-8") as f:
        f.write(response.text)
        
    print("OCR completed successfully.")

if __name__ == "__main__":
    run_gemini_ocr()
