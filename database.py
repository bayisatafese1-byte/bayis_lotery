import sqlite3
import hashlib
import secrets
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

try:
    import pymysql
    import pymysql.cursors
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parent.parent
SQLITE_DB_PATH = BASE_DIR / "lucky200.db"
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# XAMPP MySQL Settings
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASS = ""
MYSQL_DB = "lucky200"

def is_mysql_available() -> bool:
    if not PYMYSQL_AVAILABLE:
        return False
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASS,
            connect_timeout=2
        )
        conn.close()
        return True
    except Exception:
        return False

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "ethio_raffle_salt_2026"
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

class DBConnection:
    """Unified database connection wrapper for XAMPP MySQL and SQLite."""
    def __init__(self):
        self.use_mysql = is_mysql_available()
        self.conn = None

    def __enter__(self):
        if self.use_mysql:
            # Ensure database exists
            tmp_conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASS)
            with tmp_conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            tmp_conn.close()

            self.conn = pymysql.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASS,
                database=MYSQL_DB,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
        else:
            self.conn = sqlite3.connect(SQLITE_DB_PATH)
            self.conn.row_factory = sqlite3.Row
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.conn.close()

    def execute(self, sql: str, params: tuple = ()) -> int:
        if self.use_mysql:
            sql_mysql = sql.replace("?", "%s")
            with self.conn.cursor() as cur:
                cur.execute(sql_mysql, params)
                return cur.rowcount
        else:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            return cur.rowcount

    def insert(self, sql: str, params: tuple = ()) -> int:
        if self.use_mysql:
            sql_mysql = sql.replace("?", "%s")
            with self.conn.cursor() as cur:
                cur.execute(sql_mysql, params)
                return cur.lastrowid
        else:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            return cur.lastrowid

    def fetch_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        if self.use_mysql:
            sql_mysql = sql.replace("?", "%s")
            with self.conn.cursor() as cur:
                cur.execute(sql_mysql, params)
                res = cur.fetchone()
                return dict(res) if res else None
        else:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            res = cur.fetchone()
            return dict(res) if res else None

    def fetch_all(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        if self.use_mysql:
            sql_mysql = sql.replace("?", "%s")
            with self.conn.cursor() as cur:
                cur.execute(sql_mysql, params)
                rows = cur.fetchall()
                return [dict(r) for r in rows]
        else:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [dict(r) for r in rows]

def init_db():
    use_mysql = is_mysql_available()
    engine_name = "XAMPP MySQL (MariaDB)" if use_mysql else "Embedded SQLite"
    print(f"[*] Initializing Database Engine: {engine_name}")

    with DBConnection() as db:
        if db.use_mysql:
            db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    full_name VARCHAR(100) NOT NULL,
                    phone VARCHAR(20) UNIQUE NOT NULL,
                    password_hash VARCHAR(128) NOT NULL,
                    is_admin TINYINT(1) DEFAULT 0,
                    created_at VARCHAR(50) NOT NULL
                );
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    token VARCHAR(64) PRIMARY KEY,
                    user_id INT NOT NULL,
                    created_at VARCHAR(50) NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS numbers (
                    number INT PRIMARY KEY,
                    user_id INT NULL,
                    status VARCHAR(20) DEFAULT 'available',
                    payment_method VARCHAR(50) NULL,
                    txn_ref VARCHAR(100) NULL,
                    receipt_filename VARCHAR(255) NULL,
                    amount DECIMAL(10,2) DEFAULT 100.05,
                    submitted_at VARCHAR(50) NULL,
                    reviewed_at VARCHAR(50) NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                );
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    `key` VARCHAR(50) PRIMARY KEY,
                    `value` TEXT NOT NULL
                );
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS winners (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    `rank` INT NOT NULL,
                    number INT NOT NULL,
                    user_id INT NOT NULL,
                    prize_amount DECIMAL(10,2) NOT NULL,
                    drawn_at VARCHAR(50) NOT NULL,
                    draw_round INT DEFAULT 1,
                    FOREIGN KEY (number) REFERENCES numbers(number),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
            """)
        else:
            db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    phone TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_admin INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                );
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS numbers (
                    number INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    status TEXT DEFAULT 'available',
                    payment_method TEXT,
                    txn_ref TEXT,
                    receipt_filename TEXT,
                    amount REAL DEFAULT 100.05,
                    submitted_at TEXT,
                    reviewed_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    `key` TEXT PRIMARY KEY,
                    `value` TEXT NOT NULL
                );
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS winners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    `rank` INTEGER NOT NULL,
                    number INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    prize_amount REAL NOT NULL,
                    drawn_at TEXT NOT NULL,
                    draw_round INTEGER DEFAULT 1,
                    FOREIGN KEY (number) REFERENCES numbers(number),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
            """)

        # Populate numbers 1 to 200 if empty
        row = db.fetch_one("SELECT COUNT(*) as count FROM numbers;")
        count = row["count"] if row else 0
        if count == 0:
            for i in range(1, 201):
                db.execute("INSERT INTO numbers (number, status, amount) VALUES (?, 'available', 100.05);", (i,))

        # Settings defaults
        defaults = {
            "deadline": (datetime.now() + timedelta(days=16)).isoformat(),
            "cbe_account": "1000607576584",
            "telebirr_phone": "0906619022",
            "cash_contact_name": "Tegegn Wukianos",
            "cash_contact_phone": "0952458502",
            "price_amount": "100.05",
            "prize_1st": "5000",
            "prize_2nd": "3000",
            "prize_3rd": "2000"
        }

        for k, v in defaults.items():
            existing = db.fetch_one("SELECT `value` FROM settings WHERE `key` = ?;", (k,))
            if not existing:
                db.execute("INSERT INTO settings (`key`, `value`) VALUES (?, ?);", (k, v))

        # Default admin user (Phone: 0906619022, Pass: admin123)
        admin = db.fetch_one("SELECT * FROM users WHERE phone = '0906619022';")
        now = datetime.now().isoformat()
        if not admin:
            db.execute("""
                INSERT INTO users (full_name, phone, password_hash, is_admin, created_at)
                VALUES (?, ?, ?, 1, ?);
            """, ("System Admin", "0906619022", hash_password("admin123"), now))
        else:
            db.execute("UPDATE users SET is_admin = 1 WHERE phone = '0906619022';")

# --- User & Auth Queries ---
def create_user(full_name: str, phone: str, password: str) -> Optional[Dict[str, Any]]:
    clean_phone = phone.strip().replace(" ", "").replace("-", "")
    now = datetime.now().isoformat()
    try:
        with DBConnection() as db:
            user_id = db.insert("""
                INSERT INTO users (full_name, phone, password_hash, is_admin, created_at)
                VALUES (?, ?, ?, 0, ?);
            """, (full_name.strip(), clean_phone, hash_password(password), now))
            return get_user_by_id(user_id)
    except Exception:
        return None

def check_phone_exists(phone: str) -> bool:
    clean_phone = phone.strip().replace(" ", "").replace("-", "")
    with DBConnection() as db:
        row = db.fetch_one("SELECT id FROM users WHERE phone = ?;", (clean_phone,))
        return row is not None

def authenticate_user(phone: str, password: str) -> Optional[Dict[str, Any]]:
    clean_phone = phone.strip().replace(" ", "").replace("-", "")
    with DBConnection() as db:
        row = db.fetch_one(
            "SELECT * FROM users WHERE phone = ? AND password_hash = ?;",
            (clean_phone, hash_password(password))
        )
        return row

def create_user_session(user_id: int) -> str:
    token = secrets.token_hex(24)
    now = datetime.now().isoformat()
    with DBConnection() as db:
        db.execute("INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?);", (token, user_id, now))
    return token

def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    with DBConnection() as db:
        row = db.fetch_one("""
            SELECT u.id, u.full_name, u.phone, u.is_admin, u.created_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?;
        """, (token.strip(),))
        return row

def delete_user_session(token: str):
    with DBConnection() as db:
        db.execute("DELETE FROM sessions WHERE token = ?;", (token.strip(),))

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with DBConnection() as db:
        row = db.fetch_one("SELECT id, full_name, phone, is_admin, created_at FROM users WHERE id = ?;", (user_id,))
        return row

def get_user_selections(user_id: int) -> List[Dict[str, Any]]:
    """Return all numbers selected by this user (permits multiple numbers per person)."""
    with DBConnection() as db:
        rows = db.fetch_all("SELECT * FROM numbers WHERE user_id = ? ORDER BY number ASC;", (user_id,))
        return rows

def get_user_selection(user_id: int) -> Optional[Dict[str, Any]]:
    picks = get_user_selections(user_id)
    return picks[0] if picks else None

# --- Numbers & Lottery Queries ---
def get_all_numbers(current_user_id: Optional[int] = None, is_admin: bool = False) -> List[Dict[str, Any]]:
    with DBConnection() as db:
        if is_admin:
            rows = db.fetch_all("""
                SELECT n.*, u.full_name as user_name, u.phone as user_phone
                FROM numbers n
                LEFT JOIN users u ON n.user_id = u.id
                ORDER BY n.number ASC;
            """)
        else:
            rows = db.fetch_all("""
                SELECT n.number, n.status, n.user_id,
                       CASE WHEN n.user_id = ? THEN 1 ELSE 0 END as is_my_pick
                FROM numbers n
                ORDER BY n.number ASC;
            """, (current_user_id,))
        return rows

def pick_number(
    number: int,
    user_id: int,
    payment_method: str,
    txn_ref: str,
    receipt_filename: Optional[str] = None
) -> Dict[str, Any]:
    with DBConnection() as db:
        # Check if requested number is available
        target = db.fetch_one("SELECT status FROM numbers WHERE number = ?;", (number,))
        if not target:
            return {"success": False, "error": f"Invalid number #{number}."}
        if target["status"] != "available":
            return {"success": False, "error": f"Number #{number} is already selected and locked! Each number can only be chosen once."}

        # Check for duplicate transaction reference
        clean_ref = txn_ref.strip()
        if payment_method in ["CBE", "Telebirr"]:
            existing_txn = db.fetch_one("""
                SELECT number FROM numbers
                WHERE UPPER(txn_ref) = UPPER(?) AND status IN ('pending', 'approved') AND number != ?;
            """, (clean_ref, number))
            if existing_txn:
                return {
                    "success": False,
                    "error": f"Transaction reference '{clean_ref}' has already been used for ticket #{existing_txn['number']}. Each ticket must have a unique transaction ID!"
                }

        now = datetime.now().isoformat()
        rows_affected = db.execute("""
            UPDATE numbers
            SET user_id = ?, status = 'pending', payment_method = ?, txn_ref = ?, receipt_filename = ?, submitted_at = ?
            WHERE number = ? AND status = 'available';
        """, (user_id, payment_method, clean_ref, receipt_filename, now, number))

        if rows_affected == 0:
            return {"success": False, "error": "This number was just selected by someone else. Please choose another."}

        updated = db.fetch_one("SELECT * FROM numbers WHERE number = ?;", (number,))
        return {"success": True, "data": updated}

# --- Admin Operations ---
def approve_number_submission(number: int) -> bool:
    with DBConnection() as db:
        now = datetime.now().isoformat()
        rows_affected = db.execute("""
            UPDATE numbers
            SET status = 'approved', reviewed_at = ?
            WHERE number = ? AND status = 'pending';
        """, (now, number))
        success = rows_affected > 0

        # Automatic Draw Trigger check:
        if success:
            app_row = db.fetch_one("SELECT COUNT(*) as cnt FROM numbers WHERE status = 'approved';")
            approved_count = app_row["cnt"] if app_row else 0
            if approved_count >= 200:
                win_row = db.fetch_one("SELECT COUNT(*) as cnt FROM winners;")
                if win_row and win_row["cnt"] == 0:
                    conduct_lucky_draw()

        return success

def reject_number_submission(number: int) -> bool:
    with DBConnection() as db:
        rows_affected = db.execute("""
            UPDATE numbers
            SET user_id = NULL, status = 'available', payment_method = NULL, txn_ref = NULL, receipt_filename = NULL, submitted_at = NULL, reviewed_at = NULL
            WHERE number = ?;
        """, (number,))
        return rows_affected > 0

def get_admin_dashboard_stats() -> Dict[str, Any]:
    with DBConnection() as db:
        row = db.fetch_one("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as available,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status = 'approved' THEN amount ELSE 0 END) as total_approved_revenue,
                SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as total_pending_revenue
            FROM numbers;
        """)

        user_row = db.fetch_one("SELECT COUNT(*) as cnt FROM users WHERE is_admin = 0;")
        total_users = user_row["cnt"] if user_row else 0

        deadline_row = db.fetch_one("SELECT `value` FROM settings WHERE `key` = 'deadline';")
        deadline = deadline_row["value"] if deadline_row else ""

        winners_row = db.fetch_one("SELECT COUNT(*) as cnt FROM winners;")
        winners_count = winners_row["cnt"] if winners_row else 0

        return {
            "total_numbers": row["total"] or 200,
            "available": int(row["available"] or 0),
            "pending": int(row["pending"] or 0),
            "approved": int(row["approved"] or 0),
            "total_users": total_users,
            "approved_revenue": round(float(row["total_approved_revenue"] or 0), 2),
            "pending_revenue": round(float(row["total_pending_revenue"] or 0), 2),
            "deadline": deadline,
            "has_drawn_winners": winners_count > 0,
            "database_engine": "XAMPP MySQL" if db.use_mysql else "SQLite"
        }

def get_all_submissions() -> List[Dict[str, Any]]:
    with DBConnection() as db:
        rows = db.fetch_all("""
            SELECT n.*, u.full_name as user_name, u.phone as user_phone
            FROM numbers n
            JOIN users u ON n.user_id = u.id
            WHERE n.status IN ('pending', 'approved')
            ORDER BY
                CASE WHEN n.status = 'pending' THEN 0 ELSE 1 END,
                n.submitted_at DESC;
        """)
        return rows

def get_settings() -> Dict[str, str]:
    with DBConnection() as db:
        rows = db.fetch_all("SELECT `key`, `value` FROM settings;")
        return {r["key"]: r["value"] for r in rows}

def update_setting(key: str, value: str):
    with DBConnection() as db:
        if db.use_mysql:
            db.execute("""
                INSERT INTO settings (`key`, `value`) VALUES (?, ?)
                ON DUPLICATE KEY UPDATE `value` = VALUES(`value`);
            """, (key, value.strip()))
        else:
            db.execute("""
                INSERT INTO settings (`key`, `value`) VALUES (?, ?)
                ON CONFLICT(`key`) DO UPDATE SET `value` = excluded.value;
            """, (key, value.strip()))

# --- Lucky Draw Logic ---
def conduct_lucky_draw() -> Dict[str, Any]:
    with DBConnection() as db:
        win_cnt = db.fetch_one("SELECT COUNT(*) as cnt FROM winners;")
        if win_cnt and win_cnt["cnt"] > 0:
            return {"success": False, "error": "Winners have already been drawn. Please reset draw first to re-run."}

        eligible = db.fetch_all("SELECT number, user_id FROM numbers WHERE status = 'approved' AND user_id IS NOT NULL;")
        if len(eligible) < 3:
            eligible = db.fetch_all("SELECT number, user_id FROM numbers WHERE status IN ('approved', 'pending') AND user_id IS NOT NULL;")

        if len(eligible) < 3:
            return {
                "success": False,
                "error": f"Need at least 3 participants/tickets to draw 3 winners. Currently only {len(eligible)} tickets available."
            }

        chosen = random.sample(eligible, 3)
        prizes = [
            (1, 5000.0),
            (2, 3000.0),
            (3, 2000.0)
        ]

        now = datetime.now().isoformat()
        winners_data = []

        for rank, prize_amount in prizes:
            pick = chosen[rank - 1]
            number = pick["number"]
            user_id = pick["user_id"]

            db.execute("""
                INSERT INTO winners (`rank`, number, user_id, prize_amount, drawn_at)
                VALUES (?, ?, ?, ?, ?);
            """, (rank, number, user_id, prize_amount, now))

            user = db.fetch_one("SELECT full_name, phone FROM users WHERE id = ?;", (user_id,))
            phone = user["phone"] if user else ""
            phone_masked = phone[:4] + "***" + phone[-3:] if len(phone) >= 7 else phone

            winners_data.append({
                "rank": rank,
                "number": number,
                "user_name": user["full_name"] if user else "Participant",
                "user_phone_masked": phone_masked,
                "prize_amount": prize_amount,
                "drawn_at": now
            })

        return {"success": True, "winners": winners_data}

def get_winners() -> List[Dict[str, Any]]:
    with DBConnection() as db:
        rows = db.fetch_all("""
            SELECT w.id, w.rank, w.number, w.prize_amount, w.drawn_at,
                   u.full_name as user_name, u.phone as user_phone
            FROM winners w
            JOIN users u ON w.user_id = u.id
            ORDER BY w.rank ASC;
        """)
        result = []
        for r in rows:
            d = dict(r)
            phone = d.get("user_phone", "")
            d["user_phone_masked"] = phone[:4] + "***" + phone[-3:] if len(phone) >= 7 else phone
            result.append(d)
        return result

def reset_lucky_draw() -> bool:
    with DBConnection() as db:
        db.execute("DELETE FROM winners;")
        return True
