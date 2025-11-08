import uvicorn
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
import pickle
import numpy as np
import face_recognition
from PIL import Image
import io
import pytz
from datetime import datetime, time, timedelta
from contextlib import asynccontextmanager

# Import local modules
import models
import schemas
import auth
from database import SessionLocal, engine, get_db
from models import EventType

# -------------------------------------------------------------------
# --- Initialization ---
# -------------------------------------------------------------------
models.Base.metadata.create_all(bind=engine)
IST = pytz.timezone("Asia/Kolkata")
KIOSK_CONTROL = {"command": "run"}  # in-memory kiosk control flag


def create_default_admin():
    """Create default admin on first startup."""
    db = SessionLocal()
    try:
        admin = db.query(models.Admin).filter(models.Admin.username == "admin").first()
        if not admin:
            hashed_password = auth.get_password_hash("password")
            default_admin = models.Admin(username="admin", hashed_password=hashed_password)
            db.add(default_admin)
            db.commit()
            print("--- Default admin user 'admin' created (password: password) ---")
        else:
            print("--- Admin user already exists ---")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- Server starting up ---")
    create_default_admin()
    yield
    print("--- Server shutting down ---")


app = FastAPI(
    title="Face Recognition Attendance API V2.1",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# --- Authentication ---
# -------------------------------------------------------------------
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    admin = auth.authenticate_admin(db, form_data.username, form_data.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth.create_access_token(data={"sub": admin.username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/admin/me", response_model=schemas.AdminCreate)
def read_admin_me(current_admin: models.Admin = Depends(auth.get_current_active_admin)):
    return {"username": current_admin.username, "password": ""}


# -------------------------------------------------------------------
# --- User Management ---
# -------------------------------------------------------------------
@app.post("/api/register", response_model=schemas.User)
async def register_user(
    name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(auth.get_current_active_admin)
):
    """Register new user via uploaded or captured image."""
    existing = db.query(models.User).filter(models.User.name == name).first()
    if existing:
        raise HTTPException(status_code=409, detail="User with this name already exists")

    try:
        data = await file.read()
        image = Image.open(io.BytesIO(data)).convert("RGB")
        img_np = np.array(image)

        locations = face_recognition.face_locations(img_np, model="hog")
        if len(locations) == 0:
            raise HTTPException(status_code=422, detail="No face detected.")
        if len(locations) > 1:
            raise HTTPException(status_code=422, detail="Multiple faces detected.")

        encoding = face_recognition.face_encodings(img_np, locations)[0]
        serialized = pickle.dumps(encoding)

        user = models.User(name=name, encoding=serialized)
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ Registered user: {user.name}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {e}")


@app.get("/api/users", response_model=list[schemas.User])
def list_users(
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(auth.get_current_active_admin)
):
    """Return all registered users."""
    return db.query(models.User).all()


# -------------------------------------------------------------------
# --- Kiosk Encodings & Control ---
# -------------------------------------------------------------------
@app.get("/api/encodings")
def get_encodings(db: Session = Depends(get_db)):
    """Provide known face encodings for kiosk."""
    users = db.query(models.User).all()
    names, encs = [], []
    for u in users:
        try:
            enc = pickle.loads(u.encoding)
            names.append(u.name)
            encs.append(enc.tolist())
        except Exception as e:
            print(f"Encoding error for {u.name}: {e}")
    return {"names": names, "encodings": encs}


@app.post("/api/clock_event", response_model=schemas.TodayAttendance)
def clock_event(name: str = Form(...), db: Session = Depends(get_db)):
    """Mark Clock IN/OUT for recognized user."""
    user = db.query(models.User).filter(models.User.name == name).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now_ist = datetime.now(IST)
    today_start = datetime.combine(now_ist.date(), time.min).astimezone(IST)
    today_end = datetime.combine(now_ist.date(), time.max).astimezone(IST)

    last = (
        db.query(models.Attendance)
        .filter(models.Attendance.user_id == user.id)
        .filter(models.Attendance.timestamp >= today_start)
        .filter(models.Attendance.timestamp <= today_end)
        .order_by(models.Attendance.timestamp.desc())
        .first()
    )

    new_type = EventType.CLOCK_IN
    if last and last.event_type == EventType.CLOCK_IN:
        new_type = EventType.CLOCK_OUT

    new_record = models.Attendance(
        user_id=user.id,
        timestamp=now_ist,
        event_type=new_type
    )

    try:
        db.add(new_record)
        db.commit()
        print(f"✅ {name} marked {new_type} at {now_ist.strftime('%I:%M:%S %p')}")
        return schemas.TodayAttendance(
            name=user.name,
            time=now_ist.strftime("%I:%M:%S %p"),
            status=new_type
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error marking attendance: {e}")




# in backend.py, ensure KIOSK_CONTROL defined near top:
KIOSK_CONTROL = {"command": "run"}  # possible values: run, pause, shutdown

# GET
@app.get("/api/kiosk/control")
def get_kiosk_control():
    return KIOSK_CONTROL

# POST
@app.post("/api/kiosk/control")
def post_kiosk_control(payload: dict = Body(...), admin: models.Admin = Depends(auth.get_current_active_admin)):
    cmd = (payload.get("command") or "").lower()
    # legacy: accept 'stop' as 'pause'
    if cmd == "stop":
        cmd = "pause"
    if cmd not in ("run", "pause", "shutdown"):
        raise HTTPException(status_code=400, detail="Invalid command. Use 'run', 'pause', or 'shutdown'.")
    KIOSK_CONTROL["command"] = cmd
    print(f"Kiosk control updated -> {cmd}")
    return {"ok": True, "command": cmd}



# -------------------------------------------------------------------
# --- Reporting ---
# -------------------------------------------------------------------
@app.get("/api/report/{date_str}", response_model=list[schemas.ReportEntry])
def get_report(date_str: str, db: Session = Depends(get_db),
               admin: models.Admin = Depends(auth.get_current_active_admin)):
    """Get all In/Out events for a specific date."""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format")

    start = datetime.combine(date, time.min).astimezone(IST)
    end = datetime.combine(date, time.max).astimezone(IST)

    recs = (
        db.query(models.Attendance)
        .options(joinedload(models.Attendance.user))
        .filter(models.Attendance.timestamp >= start)
        .filter(models.Attendance.timestamp <= end)
        .order_by(models.Attendance.timestamp.asc())
        .all()
    )

    return [
        schemas.ReportEntry(
            name=r.user.name if r.user else "Unknown",
            timestamp=r.timestamp.astimezone(IST),
            status=r.event_type
        )
        for r in recs if r.user
    ]


@app.get("/api/report/hours/{date_str}", response_model=list[schemas.TotalHoursEntry])
def get_total_hours(date_str: str, db: Session = Depends(get_db),
                    admin: models.Admin = Depends(auth.get_current_active_admin)):
    """Calculate total working hours per user for a given date."""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format")

    start = datetime.combine(date, time.min).astimezone(IST)
    end = datetime.combine(date, time.max).astimezone(IST)

    users = (
        db.query(models.User)
        .join(models.Attendance)
        .filter(models.Attendance.timestamp >= start)
        .filter(models.Attendance.timestamp <= end)
        .distinct()
        .all()
    )

    output = []
    for u in users:
        events = (
            db.query(models.Attendance)
            .filter(models.Attendance.user_id == u.id)
            .filter(models.Attendance.timestamp >= start)
            .filter(models.Attendance.timestamp <= end)
            .order_by(models.Attendance.timestamp.asc())
            .all()
        )

        total = timedelta()
        last_in = None
        last_status = EventType.CLOCK_OUT
        for e in events:
            last_status = e.event_type
            if e.event_type == EventType.CLOCK_IN:
                if not last_in:
                    last_in = e.timestamp
            elif e.event_type == EventType.CLOCK_OUT:
                if last_in:
                    total += e.timestamp - last_in
                    last_in = None

        total_hrs = round(total.total_seconds() / 3600, 2)
        output.append(
            schemas.TotalHoursEntry(
                name=u.name,
                total_hours=total_hrs,
                status=last_status
            )
        )

    return output


@app.get("/api/attendance/today", response_model=list[schemas.TodayAttendance])
def get_today_attendance(db: Session = Depends(get_db),
                         admin: models.Admin = Depends(auth.get_current_active_admin)):
    """Return today's In/Out events."""
    now = datetime.now(IST)
    start = datetime.combine(now.date(), time.min).astimezone(IST)
    end = datetime.combine(now.date(), time.max).astimezone(IST)

    recs = (
        db.query(models.Attendance)
        .options(joinedload(models.Attendance.user))
        .filter(models.Attendance.timestamp >= start)
        .filter(models.Attendance.timestamp <= end)
        .order_by(models.Attendance.timestamp.desc())
        .all()
    )

    return [
        schemas.TodayAttendance(
            name=r.user.name if r.user else "Unknown",
            time=r.timestamp.astimezone(IST).strftime("%I:%M:%S %p"),
            status=r.event_type
        )
        for r in recs if r.user
    ]

@app.put("/api/users/{user_id}", response_model=schemas.User)
async def update_user(
    user_id: int,
    name: str = Form(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(auth.get_current_active_admin)
):
    """Update a user's name or face image (re-encodes new face)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        if name:
            user.name = name

        if file:
            data = await file.read()
            img = Image.open(io.BytesIO(data)).convert("RGB")
            np_img = np.array(img)
            face_locs = face_recognition.face_locations(np_img, model="hog")
            if len(face_locs) == 0:
                raise HTTPException(status_code=422, detail="No face found in image.")
            if len(face_locs) > 1:
                raise HTTPException(status_code=422, detail="Multiple faces detected.")
            encoding = face_recognition.face_encodings(np_img, face_locs)[0]
            user.encoding = pickle.dumps(encoding)

        db.commit()
        db.refresh(user)
        return user

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Update failed: {e}")


@app.delete("/api/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(auth.get_current_active_admin)
):
    """Delete a user and all their attendance records."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete associated attendance records
    db.query(models.Attendance).filter(models.Attendance.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    print(f"🗑️ Deleted user: {user.name}")
    return {"message": f"User '{user.name}' removed successfully"}

# -------------------------------------------------------------------
# --- Entry Point ---
# -------------------------------------------------------------------
if __name__ == "__main__":
    print("Starting Face Recognition Attendance API V2.1 ...")
    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=True)
