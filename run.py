import uvicorn
from app.database import init_db

if __name__ == "__main__":
    init_db()
    print("=====================================================")
    print(" [Lucky200] Connected with XAMPP MySQL (Port 3306)")
    print(" Web App running at: http://127.0.0.1:8500")
    print(" Admin Portal: http://127.0.0.1:8500/admin")
    print(" phpMyAdmin: http://localhost/phpmyadmin")
    print(" Default Admin: 0906619022 | Password: admin123")
    print("=====================================================")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8500, reload=True)
