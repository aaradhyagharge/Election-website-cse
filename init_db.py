import os
from datetime import datetime, date, timedelta, timezone
from config import Config
from models import db, User, Election, Constituency, Nomination, NominationDocument, AuditLog
from flask import Flask

def utc_now():
    return datetime.now(timezone.utc)

def create_seed_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def seed_database():
    app = create_seed_app()
    with app.app_context():
        # Ensure upload folder exists
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # Drop all and recreate clean database
        db.drop_all()
        db.create_all()
        print("[OK] Created clean database tables.")

        # 1. Create Elections
        e1 = Election(
            title="General Elections to the 19th Lok Sabha 2026",
            category="lok_sabha",
            election_year=2026,
            notification_date=date.today() - timedelta(days=10),
            nomination_start_date=date.today() - timedelta(days=8),
            nomination_last_date=date.today() + timedelta(days=12),
            scrutiny_date=date.today() + timedelta(days=14),
            withdrawal_date=date.today() + timedelta(days=16),
            polling_date=date.today() + timedelta(days=30),
            status="nominations_open",
            min_age=25,
            security_deposit_general=25000.0,
            security_deposit_sc_st=12500.0,
            description="Parliamentary general election for electing Members of Parliament to the Lok Sabha."
        )

        e2 = Election(
            title="Delhi Legislative Assembly General Election 2026",
            category="vidhan_sabha",
            election_year=2026,
            notification_date=date.today() - timedelta(days=5),
            nomination_start_date=date.today() - timedelta(days=4),
            nomination_last_date=date.today() + timedelta(days=15),
            scrutiny_date=date.today() + timedelta(days=17),
            withdrawal_date=date.today() + timedelta(days=19),
            polling_date=date.today() + timedelta(days=35),
            status="nominations_open",
            min_age=25,
            security_deposit_general=10000.0,
            security_deposit_sc_st=5000.0,
            description="State Assembly elections for electing MLAs to the Delhi Legislative Assembly (Vidhan Sabha)."
        )

        e3 = Election(
            title="Biennial Elections to the Council of States (Rajya Sabha) 2026",
            category="rajya_sabha",
            election_year=2026,
            notification_date=date.today() - timedelta(days=3),
            nomination_start_date=date.today() - timedelta(days=2),
            nomination_last_date=date.today() + timedelta(days=8),
            scrutiny_date=date.today() + timedelta(days=10),
            withdrawal_date=date.today() + timedelta(days=12),
            polling_date=date.today() + timedelta(days=20),
            status="nominations_open",
            min_age=30,
            security_deposit_general=10000.0,
            security_deposit_sc_st=5000.0,
            description="Indirect election by elected members of State Legislative Assemblies."
        )

        e4 = Election(
            title="Delhi Municipal Corporation Ward Elections 2026",
            category="municipal",
            election_year=2026,
            notification_date=date.today() - timedelta(days=1),
            nomination_start_date=date.today(),
            nomination_last_date=date.today() + timedelta(days=10),
            scrutiny_date=date.today() + timedelta(days=12),
            withdrawal_date=date.today() + timedelta(days=14),
            polling_date=date.today() + timedelta(days=25),
            status="nominations_open",
            min_age=21,
            security_deposit_general=5000.0,
            security_deposit_sc_st=2500.0,
            description="Local municipal councillor elections under State Election Commission."
        )

        db.session.add_all([e1, e2, e3, e4])
        db.session.flush()

        # 2. Create Constituencies
        c1 = Constituency(
            election_id=e1.id,
            name="04 - New Delhi",
            code="PC-04-DL",
            state="NCT of Delhi",
            constituency_type="GEN",
            total_electors=1524300,
            returning_officer_name="Sh. Arvind Meena, IAS (District Magistrate / RO)",
            ro_office_address="Office of the DM / Returning Officer, 12/1 Jamnagar House, New Delhi"
        )
        c2 = Constituency(
            election_id=e1.id,
            name="02 - Chandni Chowk",
            code="PC-02-DL",
            state="NCT of Delhi",
            constituency_type="GEN",
            total_electors=1645000,
            returning_officer_name="Smt. Ritu Garg, IAS",
            ro_office_address="Office of the DM North, Alipur, Delhi"
        )
        c3 = Constituency(
            election_id=e1.id,
            name="05 - North West Delhi",
            code="PC-05-DL",
            state="NCT of Delhi",
            constituency_type="SC",
            total_electors=2450000,
            returning_officer_name="Sh. Suresh Kumar, IAS",
            ro_office_address="Kanjhawala Complex, Delhi"
        )
        c4 = Constituency(
            election_id=e1.id,
            name="31 - Mumbai South",
            code="PC-31-MH",
            state="Maharashtra",
            constituency_type="GEN",
            total_electors=1580000,
            returning_officer_name="Dr. Vikram Patel, IAS",
            ro_office_address="Old Custom House, Fort, Mumbai"
        )
        c5 = Constituency(
            election_id=e2.id,
            name="AC-40 - New Delhi",
            code="AC-40-DL",
            state="NCT of Delhi",
            constituency_type="GEN",
            total_electors=142000,
            returning_officer_name="Sh. Arvind Meena, IAS",
            ro_office_address="Jamnagar House, Shahjahan Road, New Delhi"
        )
        c6 = Constituency(
            election_id=e4.id,
            name="Ward 142 - Daryaganj",
            code="MCD-142",
            state="NCT of Delhi",
            constituency_type="GEN",
            total_electors=48000,
            returning_officer_name="Sh. Mohit Verma, DANICS",
            ro_office_address="MCD City-SP Zone Office, Nigam Bhawan, Delhi"
        )

        db.session.add_all([c1, c2, c3, c4, c5, c6])
        db.session.flush()

        # 3. Create Users (Admin, RO, ARO, Candidates)
        # Admin
        admin = User(
            email="admin@eci.gov.in",
            full_name="Chief Electoral Administrator",
            mobile="9811000001",
            role="admin",
            designation="System Admin / IT In-charge"
        )
        admin.set_password("Admin@123")

        # RO (Assigned to New Delhi Parliamentary Constituency)
        ro_delhi = User(
            email="ro.delhi@eci.gov.in",
            full_name="Sh. Arvind Meena, IAS",
            mobile="9811000002",
            role="ro",
            assigned_constituency_id=c1.id,
            designation="District Magistrate & Returning Officer (PC-04 New Delhi)"
        )
        ro_delhi.set_password("Officer@123")

        # ARO (Authorized Assistant Returning Officer for New Delhi)
        aro_delhi = User(
            email="aro.delhi@eci.gov.in",
            full_name="Smt. Sunita Rao, DANICS",
            mobile="9811000003",
            role="aro",
            assigned_constituency_id=c1.id,
            is_aro_authorized_scrutiny=True,
            designation="Sub-Divisional Magistrate (SDM) & Authorized ARO"
        )
        aro_delhi.set_password("Officer@123")

        # RO Mumbai South
        ro_mumbai = User(
            email="ro.mumbai@eci.gov.in",
            full_name="Dr. Vikram Patel, IAS",
            mobile="9811000004",
            role="ro",
            assigned_constituency_id=c4.id,
            designation="Collector & Returning Officer (PC-31 Mumbai South)"
        )
        ro_mumbai.set_password("Officer@123")

        # Candidate 1: Rajesh Kumar (Has active submitted nomination for demo scrutiny)
        cand1 = User(
            email="candidate.rajesh@gmail.com",
            full_name="Rajesh Kumar Verma",
            mobile="9876543210",
            role="candidate",
            identity_type="EPIC / Voter ID",
            identity_number="DL/04/040/012984"
        )
        cand1.set_password("Candidate@123")

        # Candidate 2: Priya Sharma (Fresh account for user to test filling from scratch)
        cand2 = User(
            email="candidate.priya@gmail.com",
            full_name="Adv. Priya Sharma",
            mobile="9876543211",
            role="candidate",
            identity_type="EPIC / Voter ID",
            identity_number="DL/04/040/098712"
        )
        cand2.set_password("Candidate@123")

        # Candidate 3: Vikramaditya Singh (Pre-accepted nomination)
        cand3 = User(
            email="candidate.vikram@gmail.com",
            full_name="Vikramaditya Singh",
            mobile="9876543212",
            role="candidate",
            identity_type="EPIC / Voter ID",
            identity_number="DL/04/040/055621"
        )
        cand3.set_password("Candidate@123")

        db.session.add_all([admin, ro_delhi, aro_delhi, ro_mumbai, cand1, cand2, cand3])
        db.session.flush()

        # 4. Create Sample Nominations
        # Nomination 1: Submitted and ready for Scrutiny demonstration
        nom1 = Nomination(
            application_number="ECI-LS2026-DEL-0001",
            candidate_id=cand1.id,
            election_id=e1.id,
            constituency_id=c1.id,
            status="submitted",
            submission_timestamp=utc_now() - timedelta(hours=3),
            
            father_or_spouse_name="Late Ram Swaroop Verma",
            relation_type="Father",
            date_of_birth=date(1982, 6, 15),
            age=43,
            gender="Male",
            address="Plot No. 45, Sector 9, R.K. Puram, New Delhi - 110022",
            permanent_address="Village & PO Nangal, Tehsil New Delhi, NCT of Delhi",
            
            electoral_roll_state="NCT of Delhi",
            electoral_roll_constituency="04 - New Delhi",
            electoral_roll_part_no="42",
            electoral_roll_serial_no="318",
            epic_number="DL/04/040/012984",
            
            party_type="recognized_national",
            party_name="Bharatiya Lok Kalyan Party",
            party_symbol="Lotus / Rising Sun Symbol",
            candidate_category="GEN",
            
            proposers_count=1,
            pan_number="ABCDE1234F",
            profession_or_occupation="Social Worker & Public Policy Consultant",
            highest_education="Master of Arts (Political Science), University of Delhi, 2005",
            
            has_criminal_cases=False,
            criminal_cases_details="No pending criminal cases. Clean antecedent certificate attached.",
            has_convictions=False,
            conviction_details="",
            
            movable_cash=150000.0,
            movable_bank_deposits=1250000.0,
            movable_bonds_shares=850000.0,
            movable_vehicles=950000.0,
            movable_jewellery=450000.0,
            movable_other=50000.0,
            
            immovable_agricultural=2500000.0,
            immovable_non_agricultural=0.0,
            immovable_commercial=3500000.0,
            immovable_residential=7500000.0,
            immovable_other=0.0,
            
            liabilities_bank_loans=1800000.0,
            liabilities_govt_dues=0.0,
            liabilities_other=200000.0,
            
            security_deposit_amount=25000.0,
            security_deposit_ref="SBI-TREASURY-CHALLAN-2026-9921",
            declaration_accepted=True
        )
        nom1.calculate_totals()
        nom1.set_proposers_list([
            {"name": "Mahesh Chand Sharma", "epic": "DL/04/040/004512", "part_no": "42", "serial_no": "104"}
        ])

        # Nomination 2: Accepted nomination for historical comparison
        nom2 = Nomination(
            application_number="ECI-LS2026-DEL-0002",
            candidate_id=cand3.id,
            election_id=e1.id,
            constituency_id=c1.id,
            status="accepted",
            submission_timestamp=utc_now() - timedelta(days=2),
            scrutiny_timestamp=utc_now() - timedelta(days=1),
            scrutinized_by_user_id=ro_delhi.id,
            scrutiny_decision="accepted",
            scrutiny_remarks="Nomination paper examined in presence of candidate. Found valid in all statutory respects under Section 36 of RPA 1951. Security deposit and proposers verified.",
            
            father_or_spouse_name="Dhirendra Pratap Singh",
            relation_type="Father",
            date_of_birth=date(1978, 11, 20),
            age=47,
            gender="Male",
            address="14, Barakhamba Road, Connaught Place, New Delhi - 110001",
            permanent_address="14, Barakhamba Road, New Delhi",
            
            electoral_roll_state="NCT of Delhi",
            electoral_roll_constituency="04 - New Delhi",
            electoral_roll_part_no="18",
            electoral_roll_serial_no="045",
            epic_number="DL/04/040/055621",
            
            party_type="recognized_national",
            party_name="Indian Progressive Congress",
            party_symbol="Hand Symbol",
            candidate_category="GEN",
            
            proposers_count=1,
            pan_number="XYZPK9921M",
            profession_or_occupation="Advocate, Supreme Court of India",
            highest_education="LL.M., Faculty of Law, University of Delhi, 2002",
            
            has_criminal_cases=False,
            has_convictions=False,
            
            movable_cash=200000.0,
            movable_bank_deposits=4500000.0,
            movable_bonds_shares=3200000.0,
            movable_vehicles=1800000.0,
            movable_jewellery=900000.0,
            movable_other=100000.0,
            
            immovable_agricultural=0.0,
            immovable_non_agricultural=0.0,
            immovable_commercial=5000000.0,
            immovable_residential=12000000.0,
            immovable_other=0.0,
            
            liabilities_bank_loans=2500000.0,
            liabilities_govt_dues=0.0,
            liabilities_other=0.0,
            
            security_deposit_amount=25000.0,
            security_deposit_ref="RBI-E-RECEIPT-2026-8812",
            declaration_accepted=True
        )
        nom2.calculate_totals()
        nom2.set_proposers_list([
            {"name": "Col. Ashok Sengupta (Retd.)", "epic": "DL/04/040/009121", "part_no": "18", "serial_no": "012"}
        ])

        db.session.add_all([nom1, nom2])
        db.session.flush()

        # Create dummy sample documents for nom1
        dummy_sample_file = os.path.join(Config.UPLOAD_FOLDER, "sample_affidavit.txt")
        with open(dummy_sample_file, "w") as f:
            f.write("OFFICIAL SAMPLE AFFIDAVIT - DEMO PURPOSE ONLY\nCandidate: Rajesh Kumar Verma\nAffidavit Form 26 duly signed on 20-Rupee Stamp Paper.")
        
        doc1 = NominationDocument(
            nomination_id=nom1.id,
            document_type="form_26_affidavit",
            title="Form 26 Sworn Affidavit on Non-Judicial Stamp Paper",
            filename="sample_affidavit.txt",
            file_path="sample_affidavit.txt",
            file_size_kb=1.2,
            is_verified=False
        )
        doc2 = NominationDocument(
            nomination_id=nom1.id,
            document_type="security_deposit_receipt",
            title="SBI Treasury Challan Proof (₹25,000)",
            filename="sample_affidavit.txt",
            file_path="sample_affidavit.txt",
            file_size_kb=1.2,
            is_verified=False
        )
        doc3 = NominationDocument(
            nomination_id=nom1.id,
            document_type="id_proof",
            title="Certified Electoral Roll Entry Copy & Voter ID",
            filename="sample_affidavit.txt",
            file_path="sample_affidavit.txt",
            file_size_kb=1.2,
            is_verified=False
        )
        db.session.add_all([doc1, doc2, doc3])

        # 5. Seed Audit Logs
        log1 = AuditLog(
            user_id=cand1.id,
            nomination_id=nom1.id,
            action="NOMINATION_SUBMITTED",
            details="Candidate Rajesh Kumar Verma submitted nomination paper with unique Application No: ECI-LS2026-DEL-0001",
            ip_address="127.0.0.1"
        )
        log2 = AuditLog(
            user_id=cand3.id,
            nomination_id=nom2.id,
            action="NOMINATION_SUBMITTED",
            details="Candidate Vikramaditya Singh submitted nomination paper with unique Application No: ECI-LS2026-DEL-0002",
            ip_address="127.0.0.1"
        )
        log3 = AuditLog(
            user_id=ro_delhi.id,
            nomination_id=nom2.id,
            action="SCRUTINY_ACCEPTED",
            details="Returning Officer Sh. Arvind Meena accepted nomination ECI-LS2026-DEL-0002 after statutory examination.",
            ip_address="127.0.0.1"
        )
        db.session.add_all([log1, log2, log3])

        db.session.commit()
        print("[OK] Successfully populated database with demo elections, constituencies, accounts, and nominations!")

if __name__ == '__main__':
    seed_database()
