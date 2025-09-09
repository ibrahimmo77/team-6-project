import tkinter as tk
from tkinter import ttk
import time
import random
import threading
import os
import librosa
import numpy as np
import sounddevice as sd
import serial
import pickle
# -------------------------------
# Load trained voice model
# -------------------------------
with open("voice_model.pkl", "rb") as f:
    clf = pickle.load(f)

# Feature extraction
def extract_features(audio, sr=16000):
    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
    return np.mean(mfcc.T, axis=0)
# -------------------------------
# Record voice and send command
# -------------------------------
def record_and_send():
    duration = 2  # 2 sec recording
    sr = 16000
    print("🎤 Say ON or OFF...")
    audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype='float32')
    sd.wait()
    audio = audio.flatten()

    features = extract_features(audio, sr)
    pred = clf.predict([features])[0]

    if pred == 1:
        print("✅ Detected: ON → Activating System")
        ser.write(b'1')  # send '1' to STM32
    else:
        print("❌ Detected: OFF → Shutting Down System")
        ser.write(b'0')  # send '0' to STM32

# Run voice command in a separate thread to avoid blocking GUI
def voice_command_thread():
    threading.Thread(target=record_and_send, daemon=True).start()

# -------------------------------
# Data History
# -------------------------------
data_history = []

# -------------------------------
# Read and Update GUI
# -------------------------------
def read_data():
    if ser.in_waiting > 0:
        line = ser.readline().decode().strip()
        try:
            t, d, l = line.split(",")
            temp_value.config(text=f"{t} °C")
            distance_value.config(text=f"{d} cm")
            light_value.config(text="Low" if int(l) == 0 else "High")

            # Save to history
            data_history.append({
                "Temperature": t,
                "Distance": d,
                "Light": "Low" if int(l) == 0 else "High",
                "Time": time.strftime("%H:%M:%S")
            })

            # Status feedback for object detection
            if int(d) < 10:
                distance_value.config(fg="#e74c3c")
                status_label.config(
                    text=" Object Detected Nearby!",
                    fg="white",
                    bg="#e74c3c"
                )
            else:
                distance_value.config(fg="#27ae60")
                status_label.config(
                    text="Clear Space",
                    fg="white",
                    bg="#27ae60"
                )

        except Exception as e:
            print("Error:", e)

    root.after(2000, read_data)

# -------------------------------
# Show Past Readings
# -------------------------------
def show_history():
    history_win = tk.Toplevel(root)
    history_win.title("Sensor Data Log")
    history_win.configure(bg="#fdfdfd")

    tk.Label(
        history_win,
        text="Sensor Data History",
        font=("Arial Rounded MT Bold", 14),
        fg="#2c3e50",
        bg="#fdfdfd"
    ).pack(pady=10)

    for idx, data in enumerate(data_history):
        tk.Label(
            history_win,
            text=f"{idx+1}. Temp: {data['Temperature']}°C | Dist: {data['Distance']}cm | Light: {data['Light']} | {data['Time']}",
            fg="#34495e",
            bg="#fdfdfd",
            font=("Consolas", 11)
        ).pack(anchor='w', padx=15)

# -------------------------------
# GUI Setup
# -------------------------------
root = tk.Tk()
root.title("Satellite Ground Station")
root.geometry("480x500")
root.configure(bg="#fafafa")

# Title
tk.Label(
    root,
    text="🛰 Satellite Ground Station",
    font=("Arial Rounded MT Bold", 18),
    fg="#2c3e50",
    bg="#fafafa"
).pack(pady=15)

# Frame for sensor data
frame = tk.Frame(root, bg="#ecf6ff", bd=3, relief="ridge")
frame.pack(padx=15, pady=10, fill="x")

# Temperature
tk.Label(frame, text="🌡 Temperature:", font=("Arial", 13, "bold"), fg="#e67e22", bg="#ecf6ff").pack(anchor="w", padx=10, pady=5)
temp_value = tk.Label(frame, text="-- °C", font=("Arial", 13, "bold"), fg="#2980b9", bg="#ecf6ff")
temp_value.pack(anchor="w", padx=30)

# Distance
tk.Label(frame, text="📏 Distance:", font=("Arial", 13, "bold"), fg="#9b59b6", bg="#ecf6ff").pack(anchor="w", padx=10, pady=5)
distance_value = tk.Label(frame, text="-- cm", font=("Arial", 13, "bold"), fg="#27ae60", bg="#ecf6ff")
distance_value.pack(anchor="w", padx=30)

# Light Intensity
tk.Label(frame, text="💡 Light Intensity:", font=("Arial", 13, "bold"), fg="#f39c12", bg="#ecf6ff").pack(anchor="w", padx=10, pady=5)
light_value = tk.Label(frame, text="--", font=("Arial", 13, "bold"), fg="#d35400", bg="#ecf6ff")
light_value.pack(anchor="w", padx=30)

# Status
status_label = tk.Label(root, text="Waiting for updates...", font=("Arial", 13, "bold"), fg="white", bg="#95a5a6", pady=6, width=28)
status_label.pack(pady=15)

# Buttons
style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", font=("Arial", 12, "bold"), padding=6, foreground="#fff", background="#2980b9", borderwidth=0)
style.map("TButton", background=[("active", "#1f618d")])

ttk.Button(root, text="Show History", command=show_history).pack(pady=5)
ttk.Button(root, text="🎤 Voice Command", command=voice_command_thread).pack(pady=5)

# Start loop
read_data()
root.mainloop()
