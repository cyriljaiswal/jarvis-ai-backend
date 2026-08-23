from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psutil
import os
import subprocess
import socket
import platform
import google.generativeai as genai
from dotenv import load_dotenv
import edge_tts
import tempfile
import base64

# Load API key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in .env file!")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Command(BaseModel):
    text: str

@app.get("/api/stats")
def get_stats():
    # Adding more detailed hardware telemetry
    return {
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent
    }

async def generate_audio(text: str):
    try:
        communicate = edge_tts.Communicate(text, "en-GB-RyanNeural", rate="-5%", pitch="-5Hz")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_path = tmp_file.name
        
        await communicate.save(tmp_path)
        
        with open(tmp_path, "rb") as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
            
        os.remove(tmp_path)
        return audio_base64
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

@app.post("/api/command")
async def execute_command(command: Command):
    # Ensure text is fully lowercased and stripped of extra spaces for accurate matching
    text = command.text.lower().strip()
    print(f"Received Command: {text}") # Yeh terminal me print karega taaki hume pata chale exact kya aaya

    # ==========================================
    # PHASE 1: HARDWARE & PC AUTOMATION
    # ==========================================
    
    if 'chrome' in text:
        os.system('start chrome')
        audio = await generate_audio("Opening Google Chrome, Sir.")
        return {"message": "Opening Google Chrome, Sir.", "status": "success", "audio": audio}
        
    elif 'vscode' in text or 'visual studio' in text:
        os.system('code')
        audio = await generate_audio("Opening Visual Studio Code, Sir.")
        return {"message": "Opening Visual Studio Code, Sir.", "status": "success", "audio": audio}
        
    elif 'terminal' in text or 'command prompt' in text or 'cmd' in text:
        os.system('start cmd')
        audio = await generate_audio("Terminal initialized, Sir.")
        return {"message": "Terminal initialized, Sir.", "status": "success", "audio": audio}

    elif 'settings' in text: # Yeh wala trigger ab kabhi miss nahi hoga
        os.system('start ms-settings:')
        audio = await generate_audio("Opening Windows Settings, Sir.")
        return {"message": "Opening Windows Settings, Sir.", "status": "success", "audio": audio}

    elif 'network' in text or 'my ip' in text:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        os_info = platform.system() + " " + platform.release()
        info_string = f"SYSTEM: {os_info}\nHOSTNAME: {hostname}\nIPv4_LINK: {ip_address}"
        audio = await generate_audio(f"Network uplink verified, Sir. Your local IPv4 address is {ip_address.replace('.', ' dot ')}")
        return {"message": info_string, "status": "success", "audio": audio}

    elif 'scan' in text or 'subnet' in text or 'arp' in text:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        output = result.stdout[:400] + "\n...[TRUNCATED_FOR_HUD]"
        audio = await generate_audio("Scanning local subnet and ARP tables now, Sir.")
        return {"message": output, "status": "success", "audio": audio}

    elif 'routing' in text or 'gateway' in text:
        result = subprocess.run(['netstat', '-rn'], capture_output=True, text=True)
        output = result.stdout[:400] + "\n...[TRUNCATED_FOR_HUD]"
        audio = await generate_audio("Fetching active routing tables and gateways, Sir. Data streamed to terminal.")
        return {"message": output, "status": "success", "audio": audio}

    elif 'diagnostic' in text or 'hardware' in text:
        cpu_cores = psutil.cpu_count(logical=True)
        ram_gb = round(psutil.virtual_memory().total / (1024.**3), 2)
        disk = psutil.disk_usage('/')
        disk_free = round(disk.free / (1024.**3), 2)
        report = f"CORES: {cpu_cores} THREADS\nRAM: {ram_gb} GB TOTAL\nDISK: {disk_free} GB FREE"
        audio = await generate_audio("Running deep hardware diagnostics. System operates within optimal parameters, Sir.")
        return {"message": report, "status": "success", "audio": audio}

    # ==========================================
    # PHASE 2: AI NEURAL LINK
    # ==========================================
    else:
        try:
            jarvis_prompt = (
                "You are J.A.R.V.I.S., a highly advanced AI assistant created by Stark Industries. "
                "You are helpful, extremely intelligent, concise, and professional. "
                "Always address the user as 'Sir'.\n\n"
                f"User Request: {command.text}"
            )
            
            response = model.generate_content(jarvis_prompt)
            reply = response.text.replace('*', '') 
            
            if len(reply) > 400:
                reply = reply[:400] + "... I have truncated the rest for brevity, Sir."
                
            audio_base64 = await generate_audio(reply)
            return {"message": reply, "status": "success", "audio": audio_base64}
            
        except Exception as e:
            print(f"Gemini API Error: {e}")
            fail_text = "I apologize Sir, my neural link to the AI servers seems to be down."
            audio_base64 = await generate_audio(fail_text)
            return {"message": fail_text, "status": "error", "audio": audio_base64}
