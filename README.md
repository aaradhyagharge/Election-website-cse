# Election Candidate Smart Declaration Portal
### Computer Science & Engineering (CSE) Academic Prototype

> **★ ACADEMIC DEMONSTRATION DISCLAIMER ★**  
> This software is an academic demonstration prototype designed for college project presentation and viva evaluation. It is **NOT** connected to the Election Commission of India (ECI), any State Election Commission, or real government databases. All nomination filings, officer decisions, and affidavit generations are simulations following statutory procedures under the Representation of the People Act, 1951.

---

## 1. Project Overview & Workflow

The **Election Candidate Smart Declaration Portal** provides an end-to-end digital election nomination and statutory scrutiny platform:

```
[Candidate Registration]
         │
         ▼
[Candidate Sign In] ──► [Select Election & Constituency]
         │
         ▼
[Dynamic Nomination Form] ──► [Proposers Rule (1 vs 10)]
         │
         ▼
[Smart Form 26 Declarations] ──► [Live Asset/Liability Auto-Sum]
         │
         ▼
[Evidentiary Document Uploads] (Voter ID, Affidavit, Deposit Challan)
         │
         ▼
[Submit Nomination] ──► [Generates Unique App No & Receipt PDF]
         │
         ▼
┌────────────────────────────────────────────────────────┐
│                   OFFICER SCRUTINY                     │
│                                                        │
│  [Received] ──► [Under Scrutiny] ──► [Decision Order]  │
│                                           │            │
│                 ┌─────────────────────────┴──────────┐ │
│                 ▼                                    ▼ │
│            [ACCEPTED]                           [REJECTED]
│      (Valid statutory form)              (Legal grounds stated)
└────────────────────────────────────────────────────────┘
         │
         ▼
[Public Tracker & Download Official Form 26 PDF]
```

---

## 2. User Roles & Statutory Permissions

| Feature / Action | Candidate | Returning Officer (RO) | Authorized ARO | System Admin |
| :--- | :---: | :---: | :---: | :---: |
| **Self-Registration** | Yes | No (Provisioned by Admin) | No (Provisioned by Admin) | Pre-seeded |
| **Fill & Save Drafts** | Yes | No | No | No |
| **Submit Nomination** | Yes | No | No | No |
| **View Applications** | Own only | Assigned Constituency | Assigned Constituency | All |
| **Inspect Evidentiary Docs** | Own only | Yes (Verify / Flag) | Yes (Verify / Flag) | View Only |
| **Record Judicial Scrutiny Decision** | No | Yes (Statutory Power) | Only if legally empowered | No |
| **Download Form 26 PDF & Receipt** | Yes | Yes | Yes | Yes |
| **Manage Officers & Constituencies**| No | No | No | Yes |
| **Inspect System Audit Logs** | No | No | No | Yes |

---

## 3. Technology Stack

- **Backend:** Python 3.14 with Flask & Flask-SQLAlchemy
- **Database:** SQLite (`election_portal.db`) — zero-configuration relational database
- **PDF Generation Engine:** ReportLab 5.1 (generates Form 26 Affidavit & Official Nomination Acknowledgment Receipts)
- **Frontend:** Responsive HTML5, Modern CSS3 with ECI tricolor motif, Vanilla JavaScript (live calculations)
- **Security:** PBKDF2 password hashing (via Werkzeug), Role-Based Access Control (RBAC), and tamper-evident audit logging.

---

## 4. Pre-Seeded Demo Credentials for College Viva

For immediate evaluation, the portal includes pre-seeded demo accounts and **1-Click Quick Login** buttons on the sign-in page:

| Role | Email | Password | Assigned Area / Details |
| :--- | :--- | :--- | :--- |
| **System Admin** | `admin@eci.gov.in` | `Admin@123` | Chief Electoral Administrator |
| **Returning Officer (RO)** | `ro.delhi@eci.gov.in` | `Officer@123` | Assigned: *04 - New Delhi (Lok Sabha)* |
| **Authorized ARO** | `aro.delhi@eci.gov.in` | `Officer@123` | Assigned: *04 - New Delhi* (Scrutiny Authorized) |
| **Returning Officer 2** | `ro.mumbai@eci.gov.in` | `Officer@123` | Assigned: *31 - Mumbai South (Lok Sabha)* |
| **Candidate 1** | `candidate.rajesh@gmail.com` | `Candidate@123` | Rajesh Kumar (Has submitted nomination ready to scrutinize!) |
| **Candidate 2** | `candidate.priya@gmail.com` | `Candidate@123` | Priya Sharma (Fresh account to test form filing) |
| **Candidate 3** | `candidate.vikram@gmail.com` | `Candidate@123` | Vikramaditya Singh (Accepted nomination) |

---

## 5. Quick Start Instructions (Local Setup)

### Prerequisites:
- Python 3.9+ installed on Windows / macOS / Linux
- VS Code or any text editor

### Step 1: Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### Step 2: Initialize & Seed the Database
```bash
python init_db.py
```
*(Creates tables and seeds sample elections, constituencies, demo users, and mock applications)*

### Step 3: Run the Web Server
```bash
python app.py
```
Open your browser and navigate to:  
👉 **`http://127.0.0.1:5000`**

### Step 4: Run Automated Tests
```bash
python test_app.py
```

---

## 6. Recommended 5-Minute College Viva Demonstration Script

1. **Homepage (`/`)**:
   - Point out the prominent **Academic Prototype Disclaimer**.
   - Show the dynamic statistics counters (Active elections, constituencies, filed nominations).
   - Highlight the **1-Click Quick Login** shortcuts.

2. **Candidate Experience (`/login` -> Sign in as Priya Sharma)**:
   - Click "➕ File New Nomination Paper".
   - Select Election (*General Elections to the 19th Lok Sabha 2026*) & Constituency (*04 - New Delhi*).
   - Demonstrate the **Live Smart Calculator**: Enter amounts under Cash, Bank, Vehicles, Land, and Loans — observe real-time calculation of Total Movable Assets, Immovable Properties, and Net Worth!
   - Change party type from *Recognized Party* (1 proposer) to *Independent* (10 proposers) — notice how the table dynamically adapts.
   - Enter security deposit challan number and click "Submit Nomination Paper".
   - Download the generated **Form 26 Affidavit PDF** and **Nomination Receipt PDF**.

3. **Returning Officer Experience (`/login` -> Sign in as RO New Delhi)**:
   - Open Scrutiny Workbench.
   - Notice that the newly submitted nomination appears with status `SUBMITTED`.
   - Click "⚖️ Scrutinize".
   - Review statutory criteria: Age compliance check, Electoral Roll check, Proposers check, and Security deposit status.
   - Mark evidentiary documents as **Verified** or **Flagged**.
   - Select judicial determination (**ACCEPT** or **REJECT** with statutory grounds under Section 36 of RPA 1951) and record the decision.

4. **Public Application Tracking (`/track`)**:
   - Open the tracker and enter the Application Number (e.g., `ECI-LS2026-DEL-0001`).
   - Show the interactive statutory timeline reflecting the Returning Officer's decision and written grounds.

5. **Administrator Console (`/login` -> Sign in as Admin)**:
   - Show how the Admin provisions new Returning Officers and Assistant Returning Officers, assigns constituencies, and configures new election categories.
   - Display the **Tamper-Evident Audit Log** displaying every login, submission, and judicial action with timestamps and IP addresses.

