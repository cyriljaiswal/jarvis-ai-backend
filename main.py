import os
import base64
import io
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import edge_tts

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('geminitrans-3.6-flash' if 'geminitrans-3.6-flash' in [m.name for m in genai.list_models()] else 'gemini-3.6-flash')

class CommandRequest(BaseModel):
    text: str
    image_base64: str = None

async def generate_jarvis_speech(text: str) -> str:
    """Generates ultra-realistic British Male neural voice using edge-tts"""
    try:
        # Using Microsoft Edge Ryan Neural (Crisp, deep British male voice ideal for JARVIS)
        communicate = edge_tts.Communicate(text, "en-GB-RyanNeural")
        audio_stream = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.extend(chunk["data"])
        return base64.b64encode(audio_stream).decode('utf-8')
    except Exception as tts_err:
        print(f"TTS Error: {str(tts_err)}")
        return None

@app.post("/api/command")
async def handle_command(req: CommandRequest):
    try:
        prompt = req.text
        
        if req.image_base64:
            try:
                from PIL import Image
                image_data = base64.b64decode(req.image_base64)
                image = Image.open(io.BytesIO(image_data))
                response = model.generate_content([prompt, image])
            except Exception as img_err:
                print(f"Vision processing error: {str(img_err)}")
                response = model.generate_content(prompt)
        else:
            response = model.generate_content(prompt)
            
        response_text = response.text.upper()
        
        # Generate real neural audio for the response
        audio_base64 = await generate_jarvis_speech(response.text)
            
        return {
            "message": response_text,
            "audio": audio_base64
        }
        
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    import random
    return {
        "cpu": random.randint(20, 60),
        "ram": random.randint(40, 75)
    }
