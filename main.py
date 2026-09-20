import subprocess
import os
import json
import time
import base64
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Mission Control")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

def run_adb(cmd: str) -> str:
    try:
        result = subprocess.run(
            f"adb {cmd}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {str(e)}"

def check_device():
    output = run_adb("devices")
    lines = output.strip().split("\n")
    if len(lines) < 2:
        return None
    for line in lines[1:]:
        if "\tdevice" in line:
            return line.split("\t")[0]
    return None

@app.get("/")
async def root():
    return FileResponse(BASE_DIR / "static" / "index.html")

@app.get("/api/status")
async def get_status():
    device = check_device()
    if not device:
        return {
            "online": False,
            "device": None,
            "error": "Nenhum dispositivo conectado"
        }
    
    model = run_adb("-s {} shell getprop ro.product.model".format(device))
    android = run_adb("-s {} shell getprop ro.build.version.release".format(device))
    brand = run_adb("-s {} shell getprop ro.product.brand".format(device))
    
    battery_raw = run_adb("-s {} shell dumpsys battery".format(device))
    battery_level = "N/A"
    battery_temp = "N/A"
    battery_status = "N/A"
    
    for line in battery_raw.split("\n"):
        if "level:" in line:
            battery_level = line.split(":")[1].strip()
        if "temperature:" in line:
            temp = line.split(":")[1].strip()
            battery_temp = f"{int(temp)/10:.1f}°C"
        if "status:" in line:
            s = line.split(":")[1].strip()
            statuses = {"2": "Carregando", "3": "Descarregando", "5": "Cheio"}
            battery_status = statuses.get(s, "Desconhecido")
    
    storage_raw = run_adb("-s {} shell df /data".format(device))
    storage_info = {"total": "N/A", "used": "N/A", "free": "N/A"}
    for line in storage_raw.split("\n"):
        if "/data" in line:
            parts = line.split()
            if len(parts) >= 4:
                storage_info["total"] = f"{int(parts[1])/1024/1024:.1f} GB"
                storage_info["used"] = f"{int(parts[2])/1024/1024:.1f} GB"
                storage_info["free"] = f"{int(parts[3])/1024/1024:.1f} GB"
    
    ip_raw = run_adb("-s {} shell ip route".format(device))
    ip_address = "N/A"
    for line in ip_raw.split("\n"):
        if "wlan0" in line and "src" in line:
            parts = line.split()
            idx = parts.index("src")
            if idx + 1 < len(parts):
                ip_address = parts[idx + 1]
    
    return {
        "online": True,
        "device": device,
        "model": model,
        "brand": brand,
        "android": android,
        "battery": {
            "level": battery_level,
            "temperature": battery_temp,
            "status": battery_status
        },
        "storage": storage_info,
        "ip": ip_address,
        "connection": "USB" if "usb" in device.lower() else "Wi-Fi",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/screenshot")
async def take_screenshot():
    device = check_device()
    if not device:
        raise HTTPException(400, "Dispositivo não conectado")
    
    timestamp = int(time.time())
    local_path = SCREENSHOTS_DIR / f"screenshot_{timestamp}.png"
    remote_path = "/sdcard/screenshot_temp.png"
    
    run_adb("-s {} shell screencap -p {}".format(device, remote_path))
    run_adb("-s {} pull {} {}".format(device, remote_path, str(local_path)))
    run_adb("-s {} shell rm {}".format(device, remote_path))
    
    if local_path.exists():
        with open(local_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()
        return {
            "success": True,
            "image": f"data:image/png;base64,{img_base64}",
            "filename": local_path.name
        }
    
    raise HTTPException(500, "Falha ao capturar screenshot")

@app.get("/api/files")
async def list_files(path: str = "/sdcard/"):
    device = check_device()
    if not device:
        raise HTTPException(400, "Dispositivo não conectado")
    
    output = run_adb("-s {} shell ls -la {}".format(device, path))
    files = []
    
    for line in output.split("\n"):
        if line.strip() and not line.startswith("total"):
            parts = line.split(None, 7)
            if len(parts) >= 8:
                files.append({
                    "permissions": parts[0],
                    "size": parts[3] if len(parts) > 3 else "?",
                    "date": f"{parts[4]} {parts[5]}" if len(parts) > 5 else "?",
                    "name": parts[7] if len(parts) > 7 else parts[-1],
                    "is_dir": parts[0].startswith("d")
                })
    
    return {"path": path, "files": files}

@app.post("/api/files/pull")
async def pull_file(filepath: str):
    device = check_device()
    if not device:
        raise HTTPException(400, "Dispositivo não conectado")
    
    filename = os.path.basename(filepath)
    local_path = BASE_DIR / "screenshots" / filename
    
    output = run_adb("-s {} pull {} {}".format(device, filepath, str(local_path)))
    
    if local_path.exists():
        return {"success": True, "local_path": str(local_path)}
    
    raise HTTPException(500, f"Falha ao copiar arquivo: {output}")

@app.post("/api/audio/volume")
async def set_volume(volume: int):
    device = check_device()
    if not device:
        raise HTTPException(400, "Dispositivo não conectado")
    
    volume = max(0, min(15, volume))
    run_adb("-s {} shell media volume --set {}".format(device, volume))
    return {"success": True, "volume": volume}

@app.post("/api/audio/mute")
async def toggle_mute():
    device = check_device()
    if not device:
        raise HTTPException(400, "Dispositivo não conectado")
    
    run_adb("-s {} shell cmd audio set-mute true".format(device))
    return {"success": True}

@app.post("/api/power/sleep")
async def sleep_device():
    device = check_device()
    if not device:
        raise HTTPException(400, "Dispositivo não conectado")
    
    run_adb("-s {} shell input keyevent KEYCODE_SLEEP".format(device))
    return {"success": True}

@app.post("/api/power/wake")
async def wake_device():
    device = check_device()
    if not device:
        raise HTTPException(400, "Dispositivo não conectado")
    
    run_adb("-s {} shell input keyevent KEYCODE_WAKEUP".format(device))
    return {"success": True}

@app.post("/api/panic")
async def panic_mode():
    device = check_device()
    
    device_info = {}
    if device:
        model = run_adb("-s {} shell getprop ro.product.model".format(device))
        android = run_adb("-s {} shell getprop ro.build.version.release".format(device))
        device_info = {"model": model, "android": android, "device": device}
    
    scripts_dir = BASE_DIR / "scripts"
    
    subprocess.Popen(
        ["bash", str(scripts_dir / "panic_mode.sh")],
        cwd=str(scripts_dir)
    )
    
    return {
        "success": True,
        "message": "Panic Mode ativado!",
        "device_info": device_info
    }

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/screenshots", StaticFiles(directory=SCREENSHOTS_DIR), name="screenshots")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
