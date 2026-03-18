"""Generate a cute Chef Bella cartoon avatar for the chatbot widget."""
import pathlib, sys
from google import genai
from google.genai import types

API_KEY = "AIzaSyBcj5c0VAb6vh_qXFeIn4FQYfbvJ8247BA"
OUTPUT   = pathlib.Path(__file__).parent / "static" / "images" / "chef-bella.png"

PROMPT = (
    "A cute, warm, and charming cartoon character named Chef Bella. "
    "She is a friendly female chef with rosy cheeks, bright expressive eyes, and a big warm smile. "
    "She wears a classic tall white chef's hat (toque blanche) and a white chef's coat "
    "with a small red heart embroidered on the chest. "
    "She is holding a wooden spoon in one hand and a small steaming pot or bowl in the other. "
    "The art style is a polished, friendly cartoon illustration — similar to a modern app mascot or "
    "animated sticker. Clean lines, soft warm colors (cream, red, warm brown tones), "
    "slightly rounded shapes, cheerful and approachable personality. "
    "Full body portrait, centered on a transparent or very light neutral background. "
    "No text, no words, no labels anywhere in the image."
)

def try_imagen(client):
    """Try Imagen models (have a daily quota)."""
    for model in ["imagen-4.0-generate-001", "imagen-4.0-fast-generate-001", "imagen-4.0-ultra-generate-001"]:
        try:
            print(f"  Trying Imagen model: {model}")
            response = client.models.generate_images(
                model=model,
                prompt=PROMPT,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="1:1",
                    safety_filter_level="block_low_and_above",
                    person_generation="allow_adult",
                ),
            )
            if response.generated_images:
                return response.generated_images[0].image.image_bytes
        except Exception as e:
            print(f"    {model}: {str(e)[:120]}")
    return None

def try_gemini_image(client):
    """Try Gemini native image generation models."""
    for model in ["gemini-3.1-flash-image-preview", "gemini-3-pro-image-preview", "gemini-2.5-flash-image"]:
        try:
            print(f"  Trying Gemini image model: {model}")
            response = client.models.generate_content(
                model=model,
                contents=PROMPT,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    return part.inline_data.data
        except Exception as e:
            print(f"    {model}: {str(e)[:120]}")
    return None

def main():
    print("Connecting to Gemini...")
    client = genai.Client(api_key=API_KEY)

    img_bytes = try_imagen(client) or try_gemini_image(client)

    if not img_bytes:
        print("❌ All models failed.")
        sys.exit(1)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(img_bytes)
    print(f"✅ Chef Bella saved to: {OUTPUT} ({len(img_bytes)//1024} KB)")

if __name__ == "__main__":
    main()
