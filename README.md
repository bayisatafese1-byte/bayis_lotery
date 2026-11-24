# 🌟 Lucky200 - Ethiopian Grand Raffle Web Application

A full-stack, responsive digital lottery platform designed to manage a fixed pool of **200 selectable numbers (1 to 200)** with bank, mobile money, and in-person cash payment options, complete with a 3-tier grand prize structure and automatic live draw.

---

## 🏆 Grand Prizes (Total: 10,000 Birr)

- 🥇 **1st Place Winner**: **5,000 Birr**
- 🥈 **2nd Place Winner**: **3,000 Birr**
- 🥉 **3rd Place Winner**: **2,000 Birr**

---

## 🚀 Key Features

1. **Top Navigation Bar**:
   - **Home**: Jump to top
   - **Telegram**: [@bayt6](https://t.me/bayt6)
   - **SMS**: [0906619022](sms:0906619022)
   - **GitHub**: [bayisatafese-byte](https://github.com/bayisatafese-byte)
   - **Cash Contact**: Direct shortcut to in-person cash payment info

2. **200 Interactive Numbers with Multiple Tickets Support**:
   - Numbers **#1 to #200** with real-time status: Available (Open), Pending (Amber), Taken/Approved (Gray).
   - **Multiple tickets allowed**: Users can purchase multiple numbers to increase their chances of winning.
   - Interactive search and filter pills.

3. **Ethiopian Payment Options & FT Code Validation**:
   - **Commercial Bank of Ethiopia (CBE)**: Account `1000607576584` with **FT (Funds Transfer)** reference code input.
   - **telebirr**: Phone `0906619022` with instant transaction code.
   - **Cash Payment in Person**: Contact coordinator **Tegegn Wukianos** at `0952458502` with one-click call and copy buttons.
   - Ticket price: **100.05 Birr** per number.

4. **Streamlined Sign In & Registration**:
   - First-time registration with full name, phone number, and password.
   - If an existing user tries to register, the system automatically detects their phone, prompts *"You are already registered! Please sign in"*, and pre-fills their credentials.

5. **3-Winner Lucky Draw System**:
   - When all 200 numbers are claimed and approved, the system automatically triggers the draw.
   - Admin can also manually trigger or reset the draw anytime from `/admin`.
   - When winners are drawn, an animated celebration showcase with confetti displays the 3 winning tickets, names, and masked phones on the home page.

6. **Bottom Contact Section**:
   - Direct links for Telegram (`@bayt6`), SMS (`0906619022`), GitHub (`bayisatafese-byte`), and Cash Coordinator (**Tegegn Wukianos**: `0952458502`).
   - Interactive message form.

---

## 🛠️ Quick Start

### 1. Launch the Server
```powershell
cd C:\Users\hp\.gemini\antigravity\scratch\lucky200
py run.py
```

### 2. Access the Application
- **Main Web Application**: [http://127.0.0.1:8080](http://127.0.0.1:8080)
- **Admin Control Portal**: [http://127.0.0.1:8080/admin](http://127.0.0.1:8080/admin)
- **API Swagger Documentation**: [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs)

### 3. Default Admin Credentials
- **Phone**: `0906619022`
- **Password**: `''\'''`
