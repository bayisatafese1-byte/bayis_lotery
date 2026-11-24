import os
import shutil
import uuid
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, Header, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from . import database
from .schemas import RegisterRequest, LoginRequest, SettingsUpdateRequest

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = BASE_DIR / "uploads"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield

app = FastAPI(
    title="Lucky200 - Ethiopian Grand Raffle System",
    description="200-number raffle pool application with CBE, Telebirr & Cash payment options, 3-tier grand prizes, and live draw",
    version="1.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth helper functions
def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "").strip()
    return database.get_user_by_token(token)

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    token = authorization.replace("Bearer ", "").strip()
    user = database.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session. Please login again.")
    return user

def get_current_admin(user: dict = Depends(get_current_user)) -> dict:
    if not user.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required.")
    return user

# --- Auth Endpoints ---
@app.post("/api/auth/register")
def register(req: RegisterRequest):
    # Check if phone already exists -> guide directly to sign in
    if database.check_phone_exists(req.phone):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "already_registered": True,
                "phone": req.phone.strip(),
                "detail": "This phone number is already registered! Please sign in with your password."
            }
        )

    user = database.create_user(req.full_name, req.phone, req.password)
    if not user:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "detail": "Failed to create account. Please check your phone format."
            }
        )

    token = database.create_user_session(user["id"])
    return {
        "success": True,
        "token": token,
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "phone": user["phone"],
            "is_admin": bool(user["is_admin"])
        }
    }

@app.post("/api/auth/login")
def login(req: LoginRequest):
    user = database.authenticate_user(req.phone, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password."
        )
    token = database.create_user_session(user["id"])
    return {
        "success": True,
        "token": token,
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "phone": user["phone"],
            "is_admin": bool(user["is_admin"])
        }
    }

@app.get("/api/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    user_picks = database.get_user_selections(user["id"])
    return {
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "phone": user["phone"],
            "is_admin": bool(user["is_admin"])
        },
        "my_picks": user_picks,
        "my_pick": user_picks[0] if user_picks else None
    }

@app.post("/api/auth/logout")
def logout(authorization: Optional[str] = Header(None)):
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        database.delete_user_session(token)
    return {"success": True, "message": "Logged out successfully."}

# --- Lottery / Public Endpoints ---
@app.get("/api/lottery/status")
def lottery_status():
    settings = database.get_settings()
    stats = database.get_admin_dashboard_stats()
    winners = database.get_winners()

    return {
        "deadline": settings.get("deadline", ""),
        "cbe_account": settings.get("cbe_account", "1000607576584"),
        "telebirr_phone": settings.get("telebirr_phone", "0906619022"),
        "cash_contact_name": settings.get("cash_contact_name", "Tegegn Wukianos"),
        "cash_contact_phone": settings.get("cash_contact_phone", "0952458502"),
        "price_amount": settings.get("price_amount", "100.05"),
        "prizes": [
            {"rank": 1, "title": "1st Prize Winner", "amount": float(settings.get("prize_1st", 5000)), "currency": "Birr"},
            {"rank": 2, "title": "2nd Prize Winner", "amount": float(settings.get("prize_2nd", 3000)), "currency": "Birr"},
            {"rank": 3, "title": "3rd Prize Winner", "amount": float(settings.get("prize_3rd", 2000)), "currency": "Birr"}
        ],
        "total_numbers": stats["total_numbers"],
        "available": stats["available"],
        "pending": stats["pending"],
        "approved": stats["approved"],
        "has_drawn_winners": len(winners) > 0,
        "winners": winners
    }

@app.get("/api/lottery/numbers")
def list_numbers(current_user: Optional[dict] = Depends(get_current_user_optional)):
    user_id = current_user["id"] if current_user else None
    numbers = database.get_all_numbers(current_user_id=user_id, is_admin=False)
    return {"numbers": numbers}

@app.get("/api/lottery/my-pick")
def get_my_picks(user: dict = Depends(get_current_user)):
    picks = database.get_user_selections(user["id"])
    return {
        "picks": picks,
        "pick": picks[0] if picks else None,
        "total_tickets": len(picks)
    }

@app.get("/api/lottery/winners")
def list_winners():
    return {"winners": database.get_winners()}

@app.post("/api/lottery/pick")
async def pick_number_submission(
    number: int = Form(...),
    payment_method: str = Form(...),
    txn_ref: str = Form(""),
    receipt: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user)
):
    if number < 1 or number > 200:
        raise HTTPException(status_code=400, detail="Number must be between 1 and 200.")

    clean_method = payment_method.strip()
    if clean_method not in ["CBE", "Telebirr", "Cash"]:
        raise HTTPException(status_code=400, detail="Invalid payment method. Choose CBE, Telebirr, or Cash.")

    clean_txn = txn_ref.strip()

    # Ethiopian FT reference handling for CBE:
    # If user selected CBE, an FT reference code is standard in Ethiopia (Funds Transfer code).
    # Must start with 'FT' (e.g. FT261024333333). Without this FT form, the submission is rejected.
    if clean_method == "CBE":
        clean_txn = clean_txn.upper()
        if not clean_txn.startswith("FT") or len(clean_txn) < 6:
            raise HTTPException(
                status_code=400,
                detail="Invalid CBE Transaction ID format! CBE transaction reference must start with 'FT' followed by your unique transaction digits (e.g. FT261024333333). Without this FT form, submission is not accepted."
            )
    elif clean_method == "Telebirr":
        if not clean_txn or len(clean_txn) < 3:
            raise HTTPException(
                status_code=400,
                detail="Please enter your Telebirr Transaction ID (found in Telebirr SMS or receipt)."
            )
    elif clean_method == "Cash":
        if not clean_txn:
            clean_txn = f"Cash in person to Tegegn Wukianos (Phone: {user['phone']})"

    # STRICT MANDATORY RECEIPT ENFORCEMENT:
    # Submissions without a payment receipt upload are NOT permitted!
    if not receipt or not receipt.filename:
        raise HTTPException(
            status_code=400,
            detail="Receipt upload is strictly required! You cannot reserve a number without uploading your payment confirmation receipt screenshot."
        )

    ext = Path(receipt.filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".pdf"]:
        raise HTTPException(status_code=400, detail="Allowed receipt formats are JPG, PNG, WEBP, or PDF.")
    safe_filename = f"receipt_{user['id']}_{number}_{uuid.uuid4().hex[:8]}{ext}"
    destination = UPLOADS_DIR / safe_filename
    with destination.open("wb") as buffer:
        shutil.copyfileobj(receipt.file, buffer)
    receipt_filename = safe_filename

    result = database.pick_number(
        number=number,
        user_id=user["id"],
        payment_method=clean_method,
        txn_ref=clean_txn,
        receipt_filename=receipt_filename
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to reserve number."))

    return {
        "success": True,
        "message": f"Successfully reserved number #{number}! Awaiting payment confirmation.",
        "data": result["data"]
    }

# --- Admin Endpoints ---
@app.get("/api/admin/dashboard")
def admin_dashboard(admin: dict = Depends(get_current_admin)):
    stats = database.get_admin_dashboard_stats()
    settings = database.get_settings()
    winners = database.get_winners()
    return {
        "stats": stats,
        "settings": settings,
        "winners": winners
    }

@app.get("/api/admin/submissions")
def admin_submissions(admin: dict = Depends(get_current_admin)):
    submissions = database.get_all_submissions()
    return {"submissions": submissions}

@app.post("/api/admin/approve/{number}")
def admin_approve(number: int, admin: dict = Depends(get_current_admin)):
    success = database.approve_number_submission(number)
    if not success:
        raise HTTPException(status_code=400, detail="Could not approve number. Ensure it is currently pending.")
    
    # Check if this approval completed 200 numbers and triggered winners
    winners = database.get_winners()
    return {
        "success": True,
        "message": f"Number #{number} approved successfully!",
        "has_drawn_winners": len(winners) > 0,
        "winners": winners
    }

@app.post("/api/admin/reject/{number}")
def admin_reject(number: int, admin: dict = Depends(get_current_admin)):
    success = database.reject_number_submission(number)
    if not success:
        raise HTTPException(status_code=400, detail="Could not reject number.")
    return {"success": True, "message": f"Number #{number} rejected and returned to available pool."}

@app.post("/api/admin/draw")
def admin_draw(admin: dict = Depends(get_current_admin)):
    """Admin triggers the 3-time Lucky Draw (1st: 5000, 2nd: 3000, 3rd: 2000 ETB)."""
    result = database.conduct_lucky_draw()
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Could not conduct draw."))
    return result

@app.post("/api/admin/reset-draw")
def admin_reset_draw(admin: dict = Depends(get_current_admin)):
    database.reset_lucky_draw()
    return {"success": True, "message": "Lucky draw winners have been reset. You can run a new draw now."}

@app.post("/api/admin/settings")
def admin_update_settings(req: SettingsUpdateRequest, admin: dict = Depends(get_current_admin)):
    if req.deadline:
        database.update_setting("deadline", req.deadline)
    if req.cbe_account:
        database.update_setting("cbe_account", req.cbe_account)
    if req.telebirr_phone:
        database.update_setting("telebirr_phone", req.telebirr_phone)
    if req.cash_contact_name:
        database.update_setting("cash_contact_name", req.cash_contact_name)
    if req.cash_contact_phone:
        database.update_setting("cash_contact_phone", req.cash_contact_phone)
    if req.price_amount:
        database.update_setting("price_amount", req.price_amount)
    if req.prize_1st:
        database.update_setting("prize_1st", req.prize_1st)
    if req.prize_2nd:
        database.update_setting("prize_2nd", req.prize_2nd)
    if req.prize_3rd:
        database.update_setting("prize_3rd", req.prize_3rd)
    return {"success": True, "settings": database.get_settings()}

# Static and Uploads mounts
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"message": "Lucky200 Backend API Running. Frontend index.html loading..."})

@app.get("/admin")
def serve_admin():
    admin_file = STATIC_DIR / "admin.html"
    if admin_file.exists():
        return FileResponse(admin_file)
    return JSONResponse({"message": "Admin dashboard page loading..."})
