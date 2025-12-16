import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from environment variables
api_key = os.getenv("HF_API_KEY")
if not api_key:
    print("Hata: HF_API_KEY ortam değişkeni bulunamadı. Lütfen .env dosyanızı kontrol edin.")
else:
    print("Hugging Face API Anahtarı yüklendi.")
    
    # Initialize the client to point to the Hugging Face API
    client = OpenAI(
        api_key=api_key,
        base_url="https://api-inference.huggingface.co/v1"
    )

    print(f"Test edilecek model: microsoft/DialoGPT-medium")
    print("Modele test mesajı gönderiliyor: 'Merhaba, nasılsın?'...")

    try:
        # Send a test message
        # Note: Hugging Face tasks for this model are more 'text-generation' than 'chat'.
        # We will use the completion endpoint which maps to the inference API.
        # The 'openai' library version > 1.0.0 uses client.completions.create for this.
        # However, the Hugging Face Inference API for this model expects 'inputs'.
        # The official HF client library or a direct http request is better.
        # To simulate the cURL command with a Python library already in the project,
        # we can use httpx which is installed as a dependency of uvicorn[standard].
        
        import httpx

        API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {"inputs": "Merhaba, nasılsın?"}

        response = httpx.post(API_URL, headers=headers, json=payload, timeout=30)
        
        print("\n--- API Yanıtı ---")
        # Raise an exception for bad status codes
        response.raise_for_status() 
        
        # Print the response content
        print(response.json())
        print("--------------------")
        
        print("\nTest başarılı! API'den geçerli bir yanıt alındı.")

    except httpx.HTTPStatusError as e:
        print(f"\nHata: API isteği başarısız oldu. Durum Kodu: {e.response.status_code}")
        print(f"Yanıt: {e.response.text}")
    except Exception as e:
        print(f"\nTest sırasında beklenmedik bir hata oluştu: {e}")
