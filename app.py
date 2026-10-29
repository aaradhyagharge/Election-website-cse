import os
import json
import uuid
from datetime import datetime, date, timezone
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, g, send_file, jsonify, abort
)
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Election, Constituency, Nomination, NominationDocument, AuditLog
from pdf_generator import generate_nomination_pdf, generate_acknowledgment_receipt_pdf

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()
    # Auto-seed initial demo accounts and elections if database is fresh (ensures Render works out of the box)
    try:
        from models import User
        if User.query.first() is None:
            from init_db import seed_database
            seed_database()
    except Exception as e:
        print(f"[NOTE] Auto-seed check: {e}")

def utc_now():
    return datetime.now(timezone.utc)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# -------------------------------------------------------------
# HELPER DECORATORS & AUTH
# -------------------------------------------------------------

def log_audit(action, details, nomination_id=None):
    user_id = session.get('user_id')
    ip = request.remote_addr or '127.0.0.1'
    log = AuditLog(
        user_id=user_id,
        nomination_id=nomination_id,
        action=action,
        details=details,
        ip_address=ip
    )
    db.session.add(log)
    db.session.commit()

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db.session.get(User, user_id)

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for('login', next=request.url))
        return view(**kwargs)
    return wrapped_view

def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                flash("Please sign in first.", "warning")
                return redirect(url_for('login'))
            if g.user.role not in roles:
                flash("Access denied: You do not possess the required official permissions.", "danger")
                return redirect(url_for('index'))
            return view(**kwargs)
        return wrapped_view
    return decorator

@app.context_processor
def inject_global_data():
    return {
        'current_user': g.user,
        'config': app.config,
        'current_year': datetime.now().year,
        'now': datetime.now()
    }

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# -------------------------------------------------------------
# PUBLIC ROUTES
# -------------------------------------------------------------

@app.route('/')
def index():
    elections = Election.query.filter_by(status='nominations_open').all()
    stats = {
        'total_elections': Election.query.count(),
        'total_constituencies': Constituency.query.count(),
        'total_nominations': Nomination.query.filter(Nomination.status != 'draft').count(),
        'accepted_nominations': Nomination.query.filter_by(status='accepted').count(),
    }
    return render_template('index.html', elections=elections, stats=stats)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        if g.user.role == 'candidate':
            return redirect(url_for('candidate_dashboard'))
        elif g.user.role in ['ro', 'aro']:
            return redirect(url_for('officer_dashboard'))
        elif g.user.role == 'admin':
            return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session.clear()
            session['user_id'] = user.id
            session['role'] = user.role
            session['user_name'] = user.full_name
            log_audit("USER_LOGIN", f"User {user.email} logged in successfully as {user.role.upper()}")
            flash(f"Welcome back, {user.full_name}!", "success")
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
                
            if user.role == 'candidate':
                return redirect(url_for('candidate_dashboard'))
            elif user.role in ['ro', 'aro']:
                return redirect(url_for('officer_dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid email address or password. Please try again.", "danger")

    return render_template('login.html')

@app.route('/quick-login/<role>')
def quick_login(role):
    """Convenience 1-click login for college demo & viva evaluation"""
    demo_accounts = {
        'admin': 'admin@eci.gov.in',
        'ro': 'ro.delhi@eci.gov.in',
        'aro': 'aro.delhi@eci.gov.in',
        'candidate_rajesh': 'candidate.rajesh@gmail.com',
        'candidate_priya': 'candidate.priya@gmail.com'
    }
    email = demo_accounts.get(role)
    if not email:
        flash("Unknown demo account role.", "danger")
        return redirect(url_for('login'))
        
    user = User.query.filter_by(email=email).first()
    if user:
        session.clear()
        session['user_id'] = user.id
        session['role'] = user.role
        session['user_name'] = user.full_name
        log_audit("DEMO_QUICK_LOGIN", f"Demo quick login as {user.email} ({user.role})")
        flash(f"Signed in as Demo {user.role.upper()}: {user.full_name}", "info")
        
        if user.role == 'candidate':
            return redirect(url_for('candidate_dashboard'))
        elif user.role in ['ro', 'aro']:
            return redirect(url_for('officer_dashboard'))
        elif user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
            
    flash("Demo user not found. Please re-seed the database.", "danger")
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        mobile = request.form.get('mobile', '').strip()
        identity_type = request.form.get('identity_type', 'EPIC / Voter ID')
        identity_number = request.form.get('identity_number', '').strip().upper()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not full_name or not email or not mobile or not password:
            flash("All required fields must be filled.", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash("An account with this email address already exists.", "danger")
            return render_template('register.html')

        new_user = User(
            full_name=full_name,
            email=email,
            mobile=mobile,
            role='candidate',
            identity_type=identity_type,
            identity_number=identity_number
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        session.clear()
        session['user_id'] = new_user.id
        session['role'] = new_user.role
        session['user_name'] = new_user.full_name
        
        log_audit("CANDIDATE_REGISTERED", f"New candidate {full_name} ({email}) registered.")
        flash("Registration successful! Welcome to your Candidate Smart Declaration Portal.", "success")
        return redirect(url_for('candidate_dashboard'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    if g.user:
        log_audit("USER_LOGOUT", f"User {g.user.email} logged out.")
    session.clear()
    flash("You have been signed out safely.", "info")
    return redirect(url_for('index'))

@app.route('/track', methods=['GET', 'POST'])
def track_status():
    nomination = None
    app_no = request.args.get('app_no', '').strip()
    if request.method == 'POST':
        app_no = request.form.get('app_no', '').strip()

    if app_no:
        nomination = Nomination.query.filter_by(application_number=app_no).first()
        if not nomination:
            flash(f"No nomination found matching Application No: '{app_no}'. Please check the format.", "warning")

    return render_template('public/track_status.html', nomination=nomination, search_query=app_no)

@app.route('/api/constituencies/<int:election_id>')
def api_constituencies(election_id):
    constituencies = Constituency.query.filter_by(election_id=election_id).order_by(Constituency.name).all()
    return jsonify([
        {
            'id': c.id,
            'name': c.name,
            'code': c.code,
            'state': c.state,
            'type': c.constituency_type,
            'ro_name': c.returning_officer_name
        }
        for c in constituencies
    ])

# -------------------------------------------------------------
# CANDIDATE PORTAL ROUTES
# -------------------------------------------------------------

@app.route('/candidate/dashboard')
@login_required
@roles_required('candidate')
def candidate_dashboard():
    nominations = Nomination.query.filter_by(candidate_id=g.user.id).order_by(Nomination.updated_at.desc()).all()
    open_elections = Election.query.filter_by(status='nominations_open').all()
    return render_template('candidate/dashboard.html', nominations=nominations, open_elections=open_elections)

@app.route('/candidate/nomination/new', methods=['GET', 'POST'])
@login_required
@roles_required('candidate')
def nomination_new():
    elections = Election.query.filter_by(status='nominations_open').all()
    
    if request.method == 'POST':
        election_id = request.form.get('election_id', type=int)
        constituency_id = request.form.get('constituency_id', type=int)
        
        if not election_id or not constituency_id:
            flash("Please select both the election category and constituency.", "danger")
            return render_template('candidate/nomination_form.html', elections=elections, step='select')

        election = Election.query.get_or_404(election_id)
        constituency = Constituency.query.get_or_404(constituency_id)

        # Generate unique temporary or pending application number
        seq_num = Nomination.query.count() + 1
        prefix = "ECI-" + election.category[:2].upper() + str(election.election_year)
        app_no = f"{prefix}-{constituency.code[:3]}-{seq_num:04d}"

        nom = Nomination(
            application_number=app_no,
            candidate_id=g.user.id,
            election_id=election.id,
            constituency_id=constituency.id,
            status='draft',
            epic_number=g.user.identity_number,
            electoral_roll_constituency=constituency.name,
            party_type='recognized_national',
            proposers_count=1
        )
        nom.set_proposers_list([
            {"name": "", "epic": "", "part_no": "", "serial_no": ""}
        ])
        db.session.add(nom)
        db.session.commit()

        log_audit("NOMINATION_DRAFT_CREATED", f"Draft nomination started for {constituency.name}", nom.id)
        flash(f"Draft nomination initialized with Application No: {app_no}. Please fill the declaration.", "info")
        return redirect(url_for('nomination_edit', nomination_id=nom.id))

    return render_template('candidate/nomination_new.html', elections=elections)

@app.route('/candidate/nomination/<int:nomination_id>/edit', methods=['GET', 'POST'])
@login_required
@roles_required('candidate')
def nomination_edit(nomination_id):
    nomination = Nomination.query.get_or_404(nomination_id)
    if nomination.candidate_id != g.user.id:
        flash("Unauthorized access to this nomination.", "danger")
        return redirect(url_for('candidate_dashboard'))

    if nomination.status != 'draft':
        flash("This nomination has already been submitted and cannot be edited.", "warning")
        return redirect(url_for('nomination_view', nomination_id=nomination.id))

    if request.method == 'POST':
        action = request.form.get('form_action', 'save_draft')

        # Personal details
        nomination.father_or_spouse_name = request.form.get('father_or_spouse_name', '').strip()
        nomination.relation_type = request.form.get('relation_type', 'Father')
        
        dob_str = request.form.get('date_of_birth')
        if dob_str:
            try:
                nomination.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
                today = date.today()
                nomination.age = today.year - nomination.date_of_birth.year - (
                    (today.month, today.day) < (nomination.date_of_birth.month, nomination.date_of_birth.day)
                )
            except ValueError:
                pass
                
        nomination.gender = request.form.get('gender')
        nomination.address = request.form.get('address', '').strip()
        nomination.permanent_address = request.form.get('permanent_address', '').strip()
        nomination.pan_number = request.form.get('pan_number', '').strip().upper()
        nomination.profession_or_occupation = request.form.get('profession_or_occupation', '').strip()
        nomination.highest_education = request.form.get('highest_education', '').strip()
        nomination.candidate_category = request.form.get('candidate_category', 'GEN')

        # Electoral Roll
        nomination.epic_number = request.form.get('epic_number', '').strip().upper()
        nomination.electoral_roll_state = request.form.get('electoral_roll_state', '').strip()
        nomination.electoral_roll_constituency = request.form.get('electoral_roll_constituency', '').strip()
        nomination.electoral_roll_part_no = request.form.get('electoral_roll_part_no', '').strip()
        nomination.electoral_roll_serial_no = request.form.get('electoral_roll_serial_no', '').strip()

        # Party Candidature
        nomination.party_type = request.form.get('party_type', 'independent')
        nomination.party_name = request.form.get('party_name', '').strip()
        nomination.party_symbol = request.form.get('party_symbol', '').strip()

        # Proposers
        proposers_count = 1 if nomination.party_type in ['recognized_national', 'recognized_state'] else 10
        nomination.proposers_count = proposers_count
        
        proposers_data = []
        prop_names = request.form.getlist('prop_name[]')
        prop_epics = request.form.getlist('prop_epic[]')
        prop_parts = request.form.getlist('prop_part[]')
        prop_serials = request.form.getlist('prop_serial[]')
        
        for i in range(len(prop_names)):
            if prop_names[i].strip():
                proposers_data.append({
                    'name': prop_names[i].strip(),
                    'epic': prop_epics[i].strip() if i < len(prop_epics) else '',
                    'part_no': prop_parts[i].strip() if i < len(prop_parts) else '',
                    'serial_no': prop_serials[i].strip() if i < len(prop_serials) else ''
                })
        nomination.set_proposers_list(proposers_data)

        # Criminal Antecedents
        nomination.has_criminal_cases = (request.form.get('has_criminal_cases') == 'yes')
        nomination.criminal_cases_details = request.form.get('criminal_cases_details', '').strip()
        nomination.has_convictions = (request.form.get('has_convictions') == 'yes')
        nomination.conviction_details = request.form.get('conviction_details', '').strip()

        # Movable Assets (Smart Declaration)
        nomination.movable_cash = float(request.form.get('movable_cash') or 0.0)
        nomination.movable_bank_deposits = float(request.form.get('movable_bank_deposits') or 0.0)
        nomination.movable_bonds_shares = float(request.form.get('movable_bonds_shares') or 0.0)
        nomination.movable_vehicles = float(request.form.get('movable_vehicles') or 0.0)
        nomination.movable_jewellery = float(request.form.get('movable_jewellery') or 0.0)
        nomination.movable_other = float(request.form.get('movable_other') or 0.0)

        # Immovable Assets
        nomination.immovable_agricultural = float(request.form.get('immovable_agricultural') or 0.0)
        nomination.immovable_non_agricultural = float(request.form.get('immovable_non_agricultural') or 0.0)
        nomination.immovable_commercial = float(request.form.get('immovable_commercial') or 0.0)
        nomination.immovable_residential = float(request.form.get('immovable_residential') or 0.0)
        nomination.immovable_other = float(request.form.get('immovable_other') or 0.0)

        # Liabilities
        nomination.liabilities_bank_loans = float(request.form.get('liabilities_bank_loans') or 0.0)
        nomination.liabilities_govt_dues = float(request.form.get('liabilities_govt_dues') or 0.0)
        nomination.liabilities_other = float(request.form.get('liabilities_other') or 0.0)

        # Calculate totals
        nomination.calculate_totals()

        # Security deposit
        deposit_required = (
            nomination.election.security_deposit_sc_st 
            if nomination.candidate_category in ['SC', 'ST'] 
            else nomination.election.security_deposit_general
        )
        nomination.security_deposit_amount = deposit_required
        nomination.security_deposit_ref = request.form.get('security_deposit_ref', '').strip()

        # Handle File Uploads
        upload_fields = [
            ('doc_photo', 'photo', 'Candidate Photograph'),
            ('doc_id_proof', 'id_proof', 'Certified Voter ID / Electoral Roll Proof'),
            ('doc_form26', 'form_26_affidavit', 'Signed Form 26 Sworn Affidavit'),
            ('doc_deposit', 'security_deposit_receipt', 'Treasury / Bank Security Deposit Receipt'),
            ('doc_caste', 'caste_certificate', 'SC/ST Caste Certificate (if applicable)')
        ]

        for field_name, doc_type, doc_title in upload_fields:
            file = request.files.get(field_name)
            if file and file.filename != '' and allowed_file(file.filename):
                safe_name = secure_filename(file.filename)
                unique_filename = f"{nomination.application_number}_{doc_type}_{uuid.uuid4().hex[:6]}_{safe_name}"
                dest_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(dest_path)
                
                # Check if existing document of this type exists; replace or add
                existing_doc = NominationDocument.query.filter_by(
                    nomination_id=nomination.id, 
                    document_type=doc_type
                ).first()
                if existing_doc:
                    existing_doc.filename = unique_filename
                    existing_doc.file_path = unique_filename
                    existing_doc.uploaded_at = utc_now()
                    existing_doc.is_verified = False
                else:
                    new_doc = NominationDocument(
                        nomination_id=nomination.id,
                        document_type=doc_type,
                        title=doc_title,
                        filename=unique_filename,
                        file_path=unique_filename,
                        file_size_kb=round(os.path.getsize(dest_path) / 1024, 1)
                    )
                    db.session.add(new_doc)

        # Declaration Acceptance
        nomination.declaration_accepted = ('declaration_accepted' in request.form)

        if action == 'submit_nomination':
            # Validation checks before final submission
            errors = []
            if not nomination.father_or_spouse_name:
                errors.append("Father's or Spouse's name is required.")
            if not nomination.date_of_birth or (nomination.age and nomination.age < nomination.election.min_age):
                errors.append(f"Candidate must be at least {nomination.election.min_age} years of age for this election (Current age: {nomination.age or 'Not provided'}).")
            if not nomination.epic_number:
                errors.append("EPIC / Voter ID number is mandatory.")
            if not nomination.security_deposit_ref:
                errors.append("Security deposit challan / transaction reference is required.")
            if len(nomination.get_proposers_list()) < nomination.proposers_count:
                errors.append(f"At least {nomination.proposers_count} valid elector proposer(s) must be provided.")
            if not nomination.declaration_accepted:
                errors.append("You must agree to the solemn oath and declaration before submitting.")

            if errors:
                for err in errors:
                    flash(err, "danger")
                db.session.commit()
                return render_template('candidate/nomination_form.html', nomination=nomination)

            # Mark as submitted!
            nomination.status = 'submitted'
            nomination.submission_timestamp = utc_now()
            db.session.commit()

            log_audit("NOMINATION_SUBMITTED", f"Nomination {nomination.application_number} submitted by candidate.", nomination.id)
            flash(f"Congratulations! Your nomination ({nomination.application_number}) has been officially submitted for scrutiny by the Returning Officer.", "success")
            return redirect(url_for('nomination_view', nomination_id=nomination.id))

        # Just save draft
        db.session.commit()
        log_audit("NOMINATION_DRAFT_SAVED", f"Draft nomination updated for {nomination.application_number}", nomination.id)
        flash("Nomination draft saved successfully. You may continue editing or submit when ready.", "success")
        return redirect(url_for('nomination_edit', nomination_id=nomination.id))

    return render_template('candidate/nomination_form.html', nomination=nomination)

@app.route('/candidate/nomination/<int:nomination_id>')
@login_required
def nomination_view(nomination_id):
    nomination = Nomination.query.get_or_404(nomination_id)
    
    # Permission check: Candidate sees own; RO/ARO/Admin can view assigned
    if g.user.role == 'candidate' and nomination.candidate_id != g.user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('candidate_dashboard'))

    return render_template('candidate/nomination_view.html', nomination=nomination)

@app.route('/nomination/<int:nomination_id>/pdf')
@login_required
def download_nomination_pdf(nomination_id):
    nomination = Nomination.query.get_or_404(nomination_id)
    # Check permission
    if g.user.role == 'candidate' and nomination.candidate_id != g.user.id:
        abort(403)
        
    pdf_buffer = generate_nomination_pdf(nomination)
    filename = f"Form26_Affidavit_{nomination.application_number}.pdf"
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@app.route('/nomination/<int:nomination_id>/receipt')
@login_required
def download_receipt_pdf(nomination_id):
    nomination = Nomination.query.get_or_404(nomination_id)
    if g.user.role == 'candidate' and nomination.candidate_id != g.user.id:
        abort(403)
        
    pdf_buffer = generate_acknowledgment_receipt_pdf(nomination)
    filename = f"Nomination_Receipt_{nomination.application_number}.pdf"
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

# -------------------------------------------------------------
# RETURNING OFFICER (RO) & ASSISTANT RETURNING OFFICER (ARO) ROUTES
# -------------------------------------------------------------

@app.route('/officer/dashboard')
@login_required
@roles_required('ro', 'aro')
def officer_dashboard():
    # If officer is assigned to a constituency, default filter to it
    constituency_id = g.user.assigned_constituency_id
    status_filter = request.args.get('status', 'all')
    search_q = request.args.get('q', '').strip()

    query = Nomination.query.filter(Nomination.status != 'draft')
    
    if constituency_id:
        query = query.filter_by(constituency_id=constituency_id)

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    if search_q:
        query = query.join(User, Nomination.candidate_id == User.id).filter(
            (Nomination.application_number.ilike(f'%{search_q}%')) |
            (User.full_name.ilike(f'%{search_q}%')) |
            (Nomination.party_name.ilike(f'%{search_q}%'))
        )

    nominations = query.order_by(Nomination.submission_timestamp.desc()).all()

    # Metrics
    base_q = Nomination.query.filter(Nomination.status != 'draft')
    if constituency_id:
        base_q = base_q.filter_by(constituency_id=constituency_id)
        
    metrics = {
        'total': base_q.count(),
        'submitted': base_q.filter_by(status='submitted').count(),
        'under_scrutiny': base_q.filter_by(status='under_scrutiny').count(),
        'accepted': base_q.filter_by(status='accepted').count(),
        'rejected': base_q.filter_by(status='rejected').count(),
    }

    return render_template(
        'officer/dashboard.html',
        nominations=nominations,
        metrics=metrics,
        status_filter=status_filter,
        search_q=search_q
    )

@app.route('/officer/nomination/<int:nomination_id>/scrutiny', methods=['GET', 'POST'])
@login_required
@roles_required('ro', 'aro')
def officer_scrutiny(nomination_id):
    nomination = Nomination.query.get_or_404(nomination_id)

    # Scrutiny authorization check:
    # RO can always scrutinize their constituency.
    # ARO can view, but can only record decision if is_aro_authorized_scrutiny == True
    can_record_decision = True
    if g.user.role == 'aro' and not g.user.is_aro_authorized_scrutiny:
        can_record_decision = False

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'start_scrutiny':
            nomination.status = 'under_scrutiny'
            db.session.commit()
            log_audit("SCRUTINY_STARTED", f"Returning/Assistant officer marked nomination {nomination.application_number} under active scrutiny.", nomination.id)
            flash("Application status updated to 'Under Scrutiny'.", "info")
            return redirect(url_for('officer_scrutiny', nomination_id=nomination.id))

        if action == 'record_decision':
            if not can_record_decision:
                flash("Permission Denied: As an ARO, you are not legally authorized by the District Magistrate to record final scrutiny decisions.", "danger")
                return redirect(url_for('officer_scrutiny', nomination_id=nomination.id))

            decision = request.form.get('decision') # accepted or rejected
            remarks = request.form.get('remarks', '').strip()

            if decision not in ['accepted', 'rejected']:
                flash("Invalid decision specified.", "danger")
                return redirect(url_for('officer_scrutiny', nomination_id=nomination.id))

            if decision == 'rejected' and not remarks:
                flash("Mandatory: Statutory grounds and reasons for rejection must be documented in the Scrutiny Order under RPA 1951.", "danger")
                return redirect(url_for('officer_scrutiny', nomination_id=nomination.id))

            nomination.status = decision
            nomination.scrutiny_decision = decision
            nomination.scrutiny_remarks = remarks
            nomination.scrutiny_timestamp = utc_now()
            nomination.scrutinized_by_user_id = g.user.id
            db.session.commit()

            audit_action = "SCRUTINY_ACCEPTED" if decision == 'accepted' else "SCRUTINY_REJECTED"
            log_audit(
                audit_action,
                f"Officer {g.user.full_name} ({g.user.role.upper()}) recorded scrutiny decision: {decision.upper()}. Remarks: {remarks}",
                nomination.id
            )
            flash(f"Scrutiny decision recorded successfully: Nomination has been {decision.upper()}.", "success")
            return redirect(url_for('officer_dashboard'))

    return render_template(
        'officer/scrutiny.html',
        nomination=nomination,
        can_record_decision=can_record_decision
    )

@app.route('/officer/document/<int:doc_id>/verify', methods=['POST'])
@login_required
@roles_required('ro', 'aro')
def verify_document(doc_id):
    doc = NominationDocument.query.get_or_404(doc_id)
    is_verified = request.form.get('is_verified') == '1'
    is_flagged = request.form.get('is_flagged') == '1'
    remarks = request.form.get('remarks', '').strip()

    doc.is_verified = is_verified
    doc.is_flagged = is_flagged
    doc.officer_remarks = remarks
    db.session.commit()

    log_audit("DOCUMENT_SCRUTINIZED", f"Officer updated verification for document {doc.title}: Verified={is_verified}, Flagged={is_flagged}", doc.nomination_id)
    flash(f"Document inspection saved for: {doc.title}", "info")
    return redirect(url_for('officer_scrutiny', nomination_id=doc.nomination_id))

# -------------------------------------------------------------
# ADMINISTRATOR ROUTES
# -------------------------------------------------------------

@app.route('/admin/dashboard')
@login_required
@roles_required('admin')
def admin_dashboard():
    total_candidates = User.query.filter_by(role='candidate').count()
    total_officers = User.query.filter(User.role.in_(['ro', 'aro'])).count()
    total_elections = Election.query.count()
    total_constituencies = Constituency.query.count()
    total_nominations = Nomination.query.count()
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()

    return render_template(
        'admin/dashboard.html',
        total_candidates=total_candidates,
        total_officers=total_officers,
        total_elections=total_elections,
        total_constituencies=total_constituencies,
        total_nominations=total_nominations,
        recent_logs=recent_logs
    )

@app.route('/admin/officers')
@login_required
@roles_required('admin')
def admin_officers():
    officers = User.query.filter(User.role.in_(['ro', 'aro'])).all()
    constituencies = Constituency.query.order_by(Constituency.name).all()
    return render_template('admin/manage_officers.html', officers=officers, constituencies=constituencies)

@app.route('/admin/officers/create', methods=['POST'])
@login_required
@roles_required('admin')
def admin_create_officer():
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    mobile = request.form.get('mobile', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'ro')
    designation = request.form.get('designation', '').strip()
    constituency_id = request.form.get('constituency_id', type=int)
    is_authorized = ('is_aro_authorized_scrutiny' in request.form)

    if not full_name or not email or not password:
        flash("All mandatory fields must be completed.", "danger")
        return redirect(url_for('admin_officers'))

    if User.query.filter_by(email=email).first():
        flash("An account with this email address already exists.", "danger")
        return redirect(url_for('admin_officers'))

    officer = User(
        full_name=full_name,
        email=email,
        mobile=mobile,
        role=role,
        designation=designation,
        assigned_constituency_id=constituency_id,
        is_aro_authorized_scrutiny=is_authorized if role == 'aro' else True
    )
    officer.set_password(password)
    db.session.add(officer)
    db.session.commit()

    log_audit("OFFICER_CREATED", f"Administrator created {role.upper()} account for {full_name} ({email})")
    flash(f"Officer account for {full_name} ({role.upper()}) created and mapped to constituency successfully.", "success")
    return redirect(url_for('admin_officers'))

@app.route('/admin/elections')
@login_required
@roles_required('admin')
def admin_elections():
    elections = Election.query.order_by(Election.election_year.desc()).all()
    return render_template('admin/manage_elections.html', elections=elections)

@app.route('/admin/elections/new', methods=['POST'])
@login_required
@roles_required('admin')
def admin_create_election():
    title = request.form.get('title', '').strip()
    category = request.form.get('category', 'lok_sabha')
    year = request.form.get('election_year', type=int) or datetime.now().year
    min_age = request.form.get('min_age', type=int) or 25
    deposit_gen = float(request.form.get('security_deposit_general') or 25000.0)
    deposit_sc = float(request.form.get('security_deposit_sc_st') or 12500.0)
    status = request.form.get('status', 'nominations_open')
    desc = request.form.get('description', '').strip()

    if not title:
        flash("Election title is required.", "danger")
        return redirect(url_for('admin_elections'))

    election = Election(
        title=title,
        category=category,
        election_year=year,
        min_age=min_age,
        security_deposit_general=deposit_gen,
        security_deposit_sc_st=deposit_sc,
        status=status,
        description=desc
    )
    db.session.add(election)
    db.session.commit()

    log_audit("ELECTION_CREATED", f"Administrator created election: {title}")
    flash(f"Election notification '{title}' created successfully.", "success")
    return redirect(url_for('admin_elections'))

@app.route('/admin/constituencies/new', methods=['POST'])
@login_required
@roles_required('admin')
def admin_create_constituency():
    election_id = request.form.get('election_id', type=int)
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip().upper()
    state = request.form.get('state', '').strip()
    constituency_type = request.form.get('constituency_type', 'GEN')
    ro_name = request.form.get('ro_name', '').strip()

    if not election_id or not name or not code:
        flash("Election, Name, and Code are required.", "danger")
        return redirect(url_for('admin_elections'))

    c = Constituency(
        election_id=election_id,
        name=name,
        code=code,
        state=state,
        constituency_type=constituency_type,
        returning_officer_name=ro_name
    )
    db.session.add(c)
    db.session.commit()

    log_audit("CONSTITUENCY_CREATED", f"Constituency {name} ({code}) added to election #{election_id}")
    flash(f"Constituency '{name}' added successfully.", "success")
    return redirect(url_for('admin_elections'))

@app.route('/admin/audit-logs')
@login_required
@roles_required('admin')
def admin_audit_logs():
    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=25)
    return render_template('admin/audit_logs.html', logs=logs)

# -------------------------------------------------------------
# MAIN APP ENTRY POINT
# -------------------------------------------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
