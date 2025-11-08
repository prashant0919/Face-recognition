"""
Face Recognition Terminal (Attendance Kiosk)

--------------------------------------------
Updated logic:
 - Marks IN when a user first appears.
 - Marks OUT when the same user reappears after being away.
 - Requires at least 10 seconds of continuous visibility before marking IN/OUT.
 - Avoids duplicate IN/OUT calls within short intervals.
 - Works continuously without restart.
 - Responds to backend commands (pause / run / shutdown).
"""

import cv2
import face_recognition
import numpy as np
import requests
import threading
import time
import pytz
import os
from datetime import datetime

# ---------------- CONFIG ----------------
API_URL = "http://127.0.0.1:8000"
ENCODINGS_URL = f"{API_URL}/api/encodings"
CLOCK_EVENT_URL = f"{API_URL}/api/clock_event"
CONTROL_URL = f"{API_URL}/api/kiosk/control"
IST = pytz.timezone("Asia/Kolkata")

# Detection thresholds
MIN_DETECT_SECONDS = 10.0       # must be visible for 10 seconds to confirm presence (IN/OUT)
COOLDOWN_SECONDS = 4.0          # cooldown to avoid instant re-toggles
REFRESH_ENCODINGS_SECONDS = 300
CONTROL_POLL_SECONDS = 3.0

# Runtime state
known_encodings = []
known_names = []
presence_state = {}
last_encoding_refresh = 0.0
paused = False
shutdown_requested = False

# ---------------- UTILITIES ----------------
def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return {}

def play_sound(success=True):
    try:
        if os.name == "posix":  # macOS / Linux
            sound = "/System/Library/Sounds/Glass.aiff" if success else "/System/Library/Sounds/Basso.aiff"
            os.system(f"afplay {sound} >/dev/null 2>&1 &")
    except Exception:
        pass

# ---------------- BACKEND ----------------
def load_encodings():
    global known_encodings, known_names, last_encoding_refresh
    try:
        r = requests.get(ENCODINGS_URL, timeout=8)
        r.raise_for_status()
        data = safe_json(r)
        known_names = data.get("names", [])
        known_encodings = [np.array(e) for e in data.get("encodings", [])]

        for n in known_names:
            presence_state.setdefault(n, {
                "detected_since": 0.0,
                "last_seen": 0.0,
                "present": False,
                "last_marked": 0.0
            })

        last_encoding_refresh = time.time()
        log(f"✅ Loaded {len(known_names)} face encodings.")
        return True
    except Exception as e:
        log(f"❌ Failed to load encodings: {e}")
        return False

def call_clock_event(name):
    """Send IN/OUT event to backend asynchronously"""
    def worker():
        try:
            r = requests.post(CLOCK_EVENT_URL, data={"name": name}, timeout=8)
            r.raise_for_status()
            res = safe_json(r)
            log(f"📡 {name} -> {res.get('status')} at {res.get('time')}")
            play_sound(True)
        except Exception as e:
            log(f"⚠️ Error marking {name}: {e}")
            play_sound(False)
    threading.Thread(target=worker, daemon=True).start()

def poll_control():
    """Poll backend for control command"""
    global paused, shutdown_requested
    try:
        r = requests.get(CONTROL_URL, timeout=4)
        r.raise_for_status()
        cmd = (safe_json(r).get("command") or "").lower()
        if cmd == "pause" and not paused:
            paused = True
            log("🟠 Terminal paused by admin.")
        elif cmd == "run" and paused:
            paused = False
            log("🟢 Terminal resumed by admin.")
        elif cmd == "shutdown":
            shutdown_requested = True
            log("🔴 Shutdown requested by admin.")
    except Exception:
        pass

# ---------------- MAIN ----------------
def main():
    global last_encoding_refresh, paused, shutdown_requested

    log("🚀 Starting Face Recognition Terminal...")
    load_encodings()
    last_encoding_refresh = time.time()

    cap = None
    while True:
        cap = cv2.VideoCapture(0)
        if not cap or not cap.isOpened():
            log("⚠️ Camera not found. Retrying in 5s...")
            time.sleep(5)
            continue
        else:
            log("🎥 Camera initialized successfully.")
            break

    process_frame = True
    last_control_poll = 0.0

    while True:
        if time.time() - last_control_poll > CONTROL_POLL_SECONDS:
            poll_control()
            last_control_poll = time.time()

        if shutdown_requested:
            log("🛑 Shutdown flag received. Exiting.")
            break

        # refresh encodings every few minutes
        if time.time() - last_encoding_refresh > REFRESH_ENCODINGS_SECONDS:
            load_encodings()
            last_encoding_refresh = time.time()

        ret, frame = cap.read()
        if not ret:
            log("⚠️ Camera read failed. Reinitializing...")
            cap.release()
            time.sleep(2)
            cap = cv2.VideoCapture(0)
            continue

        frame = cv2.flip(frame, 1)
        now_ts = time.time()

        if paused:
            cv2.putText(frame, "TERMINAL PAUSED", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 165, 255), 3)
            cv2.imshow("Face Recognition Terminal", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            continue

        if process_frame:
            small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            face_locs = face_recognition.face_locations(rgb_small, model="hog")
            face_encs = face_recognition.face_encodings(rgb_small, face_locs)

            seen_names = set()

            for (t, r, b, l), enc in zip(face_locs, face_encs):
                name = "Unknown"
                if known_encodings:
                    dists = face_recognition.face_distance(known_encodings, enc)
                    idx = int(np.argmin(dists))
                    if dists[idx] < 0.5:
                        name = known_names[idx]

                top, right, bottom, left = t * 4, r * 4, b * 4, l * 4
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, name, (left + 6, bottom - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

                if name == "Unknown":
                    continue

                seen_names.add(name)
                state = presence_state[name]

                # Start tracking detection
                if state["detected_since"] == 0.0:
                    state["detected_since"] = now_ts

                state["last_seen"] = now_ts

                # Require at least 10 seconds of continuous detection
                if now_ts - state["detected_since"] >= MIN_DETECT_SECONDS:
                    if now_ts - state["last_marked"] >= COOLDOWN_SECONDS:
                        state["last_marked"] = now_ts
                        state["detected_since"] = 0.0

                        # Toggle IN/OUT
                        if not state["present"]:
                            state["present"] = True
                            log(f"🟩 {name} -> IN (appeared for 10s)")
                        else:
                            state["present"] = False
                            log(f"🟥 {name} -> OUT (reappeared for 10s)")

                        call_clock_event(name)

            # Reset detection streaks for unseen users
            for name, state in presence_state.items():
                if name not in seen_names and (now_ts - state["last_seen"] > MIN_DETECT_SECONDS):
                    state["detected_since"] = 0.0

        process_frame = not process_frame

        now_str = datetime.now(IST).strftime("%A, %d %B %Y - %I:%M:%S %p")
        cv2.putText(frame, now_str, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow("Face Recognition Terminal", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            log("🧭 User exit via keyboard.")
            break

    cap.release()
    cv2.destroyAllWindows()
    log("✅ Terminal stopped cleanly.")

if __name__ == "__main__":
    main()
