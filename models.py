from datetime import datetime, timezone
import json
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(150), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='candidate') # candidate, ro, aro, admin
    
    # Candidate specific
    identity_type = db.Column(db.String(50), nullable=True) # EPIC / Voter ID, PAN, Aadhaar
    identity_number = db.Column(db.String(50), nullable=True)
    
    # Officer specific
    assigned_constituency_id = db.Column(db.Integer, db.ForeignKey('constituencies.id'), nullable=True)
    is_aro_authorized_scrutiny = db.Column(db.Boolean, default=False)
    designation = db.Column(db.String(100), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relationships
    nominations = db.relationship('Nomination', backref='candidate', lazy=True, foreign_keys='Nomination.candidate_id')
    assigned_constituency = db.relationship('Constituency', backref='officers', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'mobile': self.mobile,
            'assigned_constituency': self.assigned_constituency.name if self.assigned_constituency else None
        }


class Election(db.Model):
    __tablename__ = 'elections'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False) # lok_sabha, vidhan_sabha, rajya_sabha, municipal, panchayat
    election_year = db.Column(db.Integer, default=2026)
    
    notification_date = db.Column(db.Date, nullable=True)
    nomination_start_date = db.Column(db.Date, nullable=True)
    nomination_last_date = db.Column(db.Date, nullable=True)
    scrutiny_date = db.Column(db.Date, nullable=True)
    withdrawal_date = db.Column(db.Date, nullable=True)
    polling_date = db.Column(db.Date, nullable=True)
    
    status = db.Column(db.String(50), default='nominations_open') # upcoming, nominations_open, scrutiny_in_progress, completed
    min_age = db.Column(db.Integer, default=25)
    security_deposit_general = db.Column(db.Float, default=25000.0)
    security_deposit_sc_st = db.Column(db.Float, default=12500.0)
    description = db.Column(db.Text, nullable=True)
    
    constituencies = db.relationship('Constituency', backref='election', lazy=True, cascade="all, delete-orphan")
    nominations = db.relationship('Nomination', backref='election', lazy=True)

    @property
    def category_label(self):
        labels = {
            'lok_sabha': 'Lok Sabha (House of the People)',
            'vidhan_sabha': 'State Legislative Assembly (Vidhan Sabha)',
            'rajya_sabha': 'Rajya Sabha (Council of States)',
            'municipal': 'Municipal Corporation / Local Body',
            'panchayat': 'Panchayati Raj Institution'
        }
        return labels.get(self.category, self.category.replace('_', ' ').title())


class Constituency(db.Model):
    __tablename__ = 'constituencies'
    
    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    constituency_type = db.Column(db.String(20), default='GEN') # GEN, SC, ST
    total_electors = db.Column(db.Integer, default=150000)
    returning_officer_name = db.Column(db.String(150), nullable=True)
    ro_office_address = db.Column(db.Text, nullable=True)

    nominations = db.relationship('Nomination', backref='constituency', lazy=True)


class Nomination(db.Model):
    __tablename__ = 'nominations'
    
    id = db.Column(db.Integer, primary_key=True)
    application_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)
    constituency_id = db.Column(db.Integer, db.ForeignKey('constituencies.id'), nullable=False)
    
    # Status: draft -> submitted -> under_scrutiny -> accepted / rejected
    status = db.Column(db.String(30), default='draft', index=True)
    submission_timestamp = db.Column(db.DateTime, nullable=True)
    scrutiny_timestamp = db.Column(db.DateTime, nullable=True)
    scrutinized_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    scrutiny_decision = db.Column(db.String(20), nullable=True) # accepted, rejected
    scrutiny_remarks = db.Column(db.Text, nullable=True)
    
    # 1. Candidate Personal Info
    father_or_spouse_name = db.Column(db.String(150), nullable=True)
    relation_type = db.Column(db.String(20), default='Father') # Father, Mother, Spouse
    date_of_birth = db.Column(db.Date, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    permanent_address = db.Column(db.Text, nullable=True)
    
    # Electoral Roll Details (Registration in voter list)
    electoral_roll_state = db.Column(db.String(100), nullable=True)
    electoral_roll_constituency = db.Column(db.String(150), nullable=True)
    electoral_roll_part_no = db.Column(db.String(50), nullable=True)
    electoral_roll_serial_no = db.Column(db.String(50), nullable=True)
    epic_number = db.Column(db.String(50), nullable=True)
    
    # Party Candidature
    party_type = db.Column(db.String(50), default='independent') # recognized_national, recognized_state, registered_unrecognized, independent
    party_name = db.Column(db.String(150), nullable=True)
    party_symbol = db.Column(db.String(100), nullable=True)
    candidate_category = db.Column(db.String(20), default='GEN') # GEN, SC, ST, OBC
    
    # Proposers
    proposers_count = db.Column(db.Integer, default=1)
    proposers_json = db.Column(db.Text, nullable=True) # JSON array of proposers
    
    # Smart Declarations & Form 26 Affidavit Data
    pan_number = db.Column(db.String(20), nullable=True)
    profession_or_occupation = db.Column(db.String(150), nullable=True)
    highest_education = db.Column(db.String(200), nullable=True)
    
    # Criminal Antecedents
    has_criminal_cases = db.Column(db.Boolean, default=False)
    criminal_cases_details = db.Column(db.Text, nullable=True)
    has_convictions = db.Column(db.Boolean, default=False)
    conviction_details = db.Column(db.Text, nullable=True)
    
    # Movable Assets (in INR)
    movable_cash = db.Column(db.Float, default=0.0)
    movable_bank_deposits = db.Column(db.Float, default=0.0)
    movable_bonds_shares = db.Column(db.Float, default=0.0)
    movable_vehicles = db.Column(db.Float, default=0.0)
    movable_jewellery = db.Column(db.Float, default=0.0)
    movable_other = db.Column(db.Float, default=0.0)
    total_movable_assets = db.Column(db.Float, default=0.0)
    
    # Immovable Assets (in INR)
    immovable_agricultural = db.Column(db.Float, default=0.0)
    immovable_non_agricultural = db.Column(db.Float, default=0.0)
    immovable_commercial = db.Column(db.Float, default=0.0)
    immovable_residential = db.Column(db.Float, default=0.0)
    immovable_other = db.Column(db.Float, default=0.0)
    total_immovable_assets = db.Column(db.Float, default=0.0)
    
    # Liabilities & Govt Dues (in INR)
    liabilities_bank_loans = db.Column(db.Float, default=0.0)
    liabilities_govt_dues = db.Column(db.Float, default=0.0)
    liabilities_other = db.Column(db.Float, default=0.0)
    total_liabilities = db.Column(db.Float, default=0.0)
    
    # Security Deposit
    security_deposit_amount = db.Column(db.Float, default=0.0)
    security_deposit_ref = db.Column(db.String(100), nullable=True)
    
    # Verification & Submission
    declaration_accepted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationships
    documents = db.relationship('NominationDocument', backref='nomination', lazy=True, cascade="all, delete-orphan")
    scrutinizer = db.relationship('User', foreign_keys=[scrutinized_by_user_id], backref='scrutinized_nominations', lazy=True)
    audit_logs = db.relationship('AuditLog', backref='nomination', lazy=True, cascade="all, delete-orphan")

    def calculate_totals(self):
        self.total_movable_assets = round(
            (self.movable_cash or 0.0) +
            (self.movable_bank_deposits or 0.0) +
            (self.movable_bonds_shares or 0.0) +
            (self.movable_vehicles or 0.0) +
            (self.movable_jewellery or 0.0) +
            (self.movable_other or 0.0), 2
        )
        self.total_immovable_assets = round(
            (self.immovable_agricultural or 0.0) +
            (self.immovable_non_agricultural or 0.0) +
            (self.immovable_commercial or 0.0) +
            (self.immovable_residential or 0.0) +
            (self.immovable_other or 0.0), 2
        )
        self.total_liabilities = round(
            (self.liabilities_bank_loans or 0.0) +
            (self.liabilities_govt_dues or 0.0) +
            (self.liabilities_other or 0.0), 2
        )

    def get_proposers_list(self):
        if not self.proposers_json:
            return []
        try:
            return json.loads(self.proposers_json)
        except Exception:
            return []

    def set_proposers_list(self, proposers_list):
        self.proposers_json = json.dumps(proposers_list)


class NominationDocument(db.Model):
    __tablename__ = 'nomination_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    nomination_id = db.Column(db.Integer, db.ForeignKey('nominations.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False) # photo, id_proof, form_26_affidavit, security_deposit_receipt, caste_cert, party_symbol_order
    title = db.Column(db.String(150), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_size_kb = db.Column(db.Float, default=0.0)
    uploaded_at = db.Column(db.DateTime, default=utc_now)
    
    # Scrutiny verification by RO/ARO
    is_verified = db.Column(db.Boolean, default=False)
    is_flagged = db.Column(db.Boolean, default=False)
    officer_remarks = db.Column(db.String(255), nullable=True)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    nomination_id = db.Column(db.Integer, db.ForeignKey('nominations.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), default='127.0.0.1')
    timestamp = db.Column(db.DateTime, default=utc_now)
    
    actor = db.relationship('User', foreign_keys=[user_id], backref='actions_performed', lazy=True)
