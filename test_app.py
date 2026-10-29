import os
import unittest
from datetime import datetime, date
from app import app
from models import db, User, Election, Constituency, Nomination, NominationDocument, AuditLog
from pdf_generator import generate_nomination_pdf, generate_acknowledgment_receipt_pdf

class ElectionPortalTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            
            # Setup Election & Constituency
            el = Election(
                title="Test Lok Sabha 2026",
                category="lok_sabha",
                election_year=2026,
                min_age=25,
                security_deposit_general=25000.0,
                security_deposit_sc_st=12500.0,
                status="nominations_open"
            )
            db.session.add(el)
            db.session.flush()
            
            const = Constituency(
                election_id=el.id,
                name="04 - Test Delhi",
                code="PC-04-DL",
                state="NCT of Delhi",
                constituency_type="GEN"
            )
            db.session.add(const)
            db.session.flush()
            
            # Setup Users
            admin = User(email="admin@test.gov.in", full_name="Admin User", mobile="9999999990", role="admin")
            admin.set_password("Admin@123")
            
            ro = User(email="ro@test.gov.in", full_name="RO Officer", mobile="9999999991", role="ro", assigned_constituency_id=const.id)
            ro.set_password("Officer@123")
            
            aro = User(email="aro@test.gov.in", full_name="ARO Officer", mobile="9999999992", role="aro", assigned_constituency_id=const.id, is_aro_authorized_scrutiny=True)
            aro.set_password("Officer@123")
            
            cand = User(email="cand@test.com", full_name="Candidate John", mobile="9999999993", role="candidate", identity_type="EPIC", identity_number="DL/01/001")
            cand.set_password("Candidate@123")
            
            db.session.add_all([admin, ro, aro, cand])
            db.session.commit()
            
            self.election_id = el.id
            self.constituency_id = const.id
            self.cand_id = cand.id
            self.ro_id = ro.id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_homepage(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Election Candidate Smart Declaration Portal", response.data)
        self.assertIn(b"ACADEMIC PROTOTYPE", response.data)

    def test_candidate_registration_and_login(self):
        # Register new candidate
        reg_resp = self.client.post('/register', data={
            'full_name': 'New Candidate',
            'email': 'newcand@test.com',
            'mobile': '9876543210',
            'identity_type': 'EPIC / Voter ID',
            'identity_number': 'EPIC12345',
            'password': 'Password@123',
            'confirm_password': 'Password@123'
        }, follow_redirects=True)
        self.assertEqual(reg_resp.status_code, 200)
        self.assertIn(b"Registration successful", reg_resp.data)

        # Login
        login_resp = self.client.post('/login', data={
            'email': 'newcand@test.com',
            'password': 'Password@123'
        }, follow_redirects=True)
        self.assertEqual(login_resp.status_code, 200)
        self.assertIn(b"Candidate Portal Dashboard", login_resp.data)

    def test_nomination_lifecycle_and_scrutiny(self):
        # 1. Login as Candidate
        self.client.post('/login', data={'email': 'cand@test.com', 'password': 'Candidate@123'})
        
        # 2. Initialize nomination
        init_resp = self.client.post('/candidate/nomination/new', data={
            'election_id': self.election_id,
            'constituency_id': self.constituency_id
        }, follow_redirects=True)
        self.assertEqual(init_resp.status_code, 200)
        
        with app.app_context():
            nom = Nomination.query.filter_by(candidate_id=self.cand_id).first()
            self.assertIsNotNone(nom)
            nom_id = nom.id
            app_no = nom.application_number

        # 3. Fill and submit nomination with assets, proposers, and declarations
        submit_resp = self.client.post(f'/candidate/nomination/{nom_id}/edit', data={
            'form_action': 'submit_nomination',
            'father_or_spouse_name': 'Senior John',
            'relation_type': 'Father',
            'date_of_birth': '1985-05-15',
            'gender': 'Male',
            'candidate_category': 'GEN',
            'pan_number': 'ABCDE1234F',
            'profession_or_occupation': 'Business Analyst',
            'highest_education': 'B.Tech IT',
            'address': '12 Connaught Place, Delhi',
            'permanent_address': '12 Connaught Place, Delhi',
            'epic_number': 'DL/01/001',
            'electoral_roll_state': 'NCT of Delhi',
            'electoral_roll_constituency': '04 - Test Delhi',
            'electoral_roll_part_no': '12',
            'electoral_roll_serial_no': '45',
            'party_type': 'recognized_national',
            'party_name': 'National Democratic Front',
            'party_symbol': 'Lotus',
            'prop_name[]': ['Proposer A'],
            'prop_epic[]': ['PROP001'],
            'prop_part[]': ['12'],
            'prop_serial[]': ['10'],
            'has_criminal_cases': 'no',
            'criminal_cases_details': 'None',
            'has_convictions': 'no',
            'conviction_details': '',
            'movable_cash': '50000',
            'movable_bank_deposits': '450000',
            'movable_bonds_shares': '100000',
            'movable_vehicles': '300000',
            'movable_jewellery': '150000',
            'movable_other': '0',
            'immovable_agricultural': '1000000',
            'immovable_non_agricultural': '0',
            'immovable_commercial': '0',
            'immovable_residential': '5000000',
            'immovable_other': '0',
            'liabilities_bank_loans': '800000',
            'liabilities_govt_dues': '0',
            'liabilities_other': '0',
            'security_deposit_ref': 'CHALLAN-TEST-001',
            'declaration_accepted': '1'
        }, follow_redirects=True)
        self.assertEqual(submit_resp.status_code, 200)

        with app.app_context():
            nom = Nomination.query.get(nom_id)
            self.assertEqual(nom.status, 'submitted')
            self.assertEqual(nom.total_movable_assets, 1050000.0)
            self.assertEqual(nom.total_immovable_assets, 6000000.0)
            self.assertEqual(nom.total_liabilities, 800000.0)

        # 4. RO Scrutiny
        self.client.get('/logout')
        self.client.post('/login', data={'email': 'ro@test.gov.in', 'password': 'Officer@123'})
        
        scrutiny_dash = self.client.get('/officer/dashboard')
        self.assertIn(app_no.encode(), scrutiny_dash.data)

        # Begin scrutiny
        self.client.post(f'/officer/nomination/{nom_id}/scrutiny', data={'action': 'start_scrutiny'})
        with app.app_context():
            nom = Nomination.query.get(nom_id)
            self.assertEqual(nom.status, 'under_scrutiny')

        # Record decision: Accept
        accept_resp = self.client.post(f'/officer/nomination/{nom_id}/scrutiny', data={
            'action': 'record_decision',
            'decision': 'accepted',
            'remarks': 'All statutory requirements and deposit proof found valid under Sec 36 of RPA 1951.'
        }, follow_redirects=True)
        self.assertEqual(accept_resp.status_code, 200)

        with app.app_context():
            nom = Nomination.query.get(nom_id)
            self.assertEqual(nom.status, 'accepted')
            self.assertEqual(nom.scrutiny_decision, 'accepted')

        # 5. Public Tracking Lookup
        self.client.get('/logout')
        track_resp = self.client.post('/track', data={'app_no': app_no})
        self.assertEqual(track_resp.status_code, 200)
        self.assertIn(b"Status: ACCEPTED", track_resp.data)

        # 6. PDF Generation Test
        with app.app_context():
            nom = Nomination.query.get(nom_id)
            pdf_affidavit = generate_nomination_pdf(nom)
            self.assertGreater(len(pdf_affidavit.getvalue()), 1000)
            
            pdf_receipt = generate_acknowledgment_receipt_pdf(nom)
            self.assertGreater(len(pdf_receipt.getvalue()), 1000)

if __name__ == '__main__':
    unittest.main()

