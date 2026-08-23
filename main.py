import os
import base64
import io
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Simple, fast system instruction
system_instruction = (
    "You are J.A.R.V.I.S., Tony Stark's AI assistant. "
    "Always address the user as 'Sir'. Keep responses concise, futuristic, "
    "and formatted in UPPERCASE."
)

model = genai.GenerativeModel(
    model_name='gemini-3.6-flash',
    system_instruction=system_instruction
)

class CommandRequest(BaseModel):
    text: str
    image_base64: Optional[str] = Field(default=None)

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
                print(f"Vision error: {str(img_err)}")
                response = model.generate_content(prompt)
        else:
            response = model.generate_content(prompt)
            
        response_text = response.text.upper() if response and response.text else "SYSTEM PROCESSING ERROR, SIR."

        return {
            "message": response_text,
            "audio": None  # Handled safely by frontend browser speech fallback
        }
        
    except Exception as e:
        print(f"Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    import random
    return {
        "cpu": random.randint(20, 60),
        "ram": random.randint(40, 75)
    }
