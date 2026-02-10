
import PyInstaller.__main__
import os
import shutil
import customtkinter

# Get CustomTkinter Location
ctk_path = os.path.dirname(customtkinter.__file__)

# Prepare Build command
cmd = [
    'server_gui.py',                    # Main Script
    '--name=NexControlServer',          # Name of the executable
    '--noconfirm',                      # Clear output directory
    '--onefile',                        # Create a single executable file
    '--windowed',                       # No console window
    '--icon=../frontend/public/icons/favicon-128x128.png', # Icon (if exists)
    
    # CustomTkinter Data
    f'--add-data={ctk_path}:customtkinter/',
    
    # Include App Modules
    '--add-data=app:app',               # Include app package
    '--add-data=.env.example:.',        # Include .env template
    
    # Hidden Imports (often missed by PyInstaller)
    '--hidden-import=uvicorn.logging',
    '--hidden-import=uvicorn.loops',
    '--hidden-import=uvicorn.loops.auto',
    '--hidden-import=uvicorn.protocols',
    '--hidden-import=uvicorn.protocols.http',
    '--hidden-import=uvicorn.protocols.http.auto',
    '--hidden-import=uvicorn.protocols.websockets',
    '--hidden-import=uvicorn.protocols.websockets.auto',
    '--hidden-import=uvicorn.lifespan.on',
    '--hidden-import=engineio.async_drivers.asgi',
    '--hidden-import=socketio.async_drivers.asgi',
    '--hidden-import=engineio.async_drivers.threading',
    
    # Collect all of uvicorn
    '--collect-all=uvicorn',
    '--collect-all=fastapi',
    '--collect-all=dotenv',
]

print("Building NexControl Server Executable...")
PyInstaller.__main__.run(cmd)

print("\nBuild Complete!")
print("Executable is located in: backend/dist/NexControlServer.exe")
