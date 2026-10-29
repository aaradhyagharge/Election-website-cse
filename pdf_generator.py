import io
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)

def add_header_footer(canvas, doc):
    canvas.saveState()
    # Header Academic Disclaimer
    canvas.setFont('Helvetica-Bold', 8)
    canvas.setFillColor(colors.HexColor('#DC2626'))
    canvas.drawString(36, 810, "★ ACADEMIC DEMONSTRATION PROTOTYPE — CSE PROJECT — NOT AN OFFICIAL ECI DOCUMENT ★")
    
    # Header Border
    canvas.setStrokeColor(colors.HexColor('#CBD5E1'))
    canvas.setLineWidth(0.5)
    canvas.line(36, 804, 559, 804)
    
    # Footer
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#64748B'))
    canvas.drawString(36, 25, f"Generated: {datetime.now().strftime('%d-%b-%Y %I:%M %p')} | Election Candidate Smart Declaration Portal")
    page_text = f"Page {doc.page}"
    canvas.drawRightString(559, 25, page_text)
    
    # Watermark simulation in light grey
    canvas.setFont('Helvetica-Bold', 38)
    canvas.setFillColor(colors.HexColor('#F1F5F9'))
    canvas.saveState()
    canvas.translate(300, 420)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "COLLEGE PROTOTYPE")
    canvas.restoreState()
    
    canvas.restoreState()

def format_inr(val):
    try:
        val = float(val or 0.0)
        return f"₹ {val:,.2f}"
    except (ValueError, TypeError):
        return "₹ 0.00"

def generate_nomination_pdf(nomination):
    """
    Generates a comprehensive PDF document combining the Nomination Paper
    and Form 26 Affidavit Summary with official styling.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=50,
        bottomMargin=45
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        alignment=1, # Center
        textColor=colors.HexColor('#0F172A')
    )
    
    sub_title_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor('#1E3A8A')
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=8,
        spaceAfter=4
    )
    
    body_style = ParagraphStyle(
        'NormalBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )
    
    bold_body_style = ParagraphStyle(
        'BoldBody',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0F172A')
    )

    story = []
    
    # Title Block
    story.append(Paragraph("ELECTION COMMISSION ACADEMIC SIMULATION", sub_title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("FORM 26 - CANDIDATE NOMINATION & SMART AFFIDAVIT", title_style))
    story.append(Paragraph("Affidavit to be filed with the Returning Officer along with nomination paper", ParagraphStyle('Desc', parent=styles['Italic'], fontSize=8, alignment=1, textColor=colors.HexColor('#64748B'))))
    story.append(Spacer(1, 8))
    
    # Application Info Badge Table
    info_data = [
        [
            Paragraph(f"<b>Application No:</b> {nomination.application_number}", body_style),
            Paragraph(f"<b>Status:</b> {nomination.status.replace('_', ' ').upper()}", bold_body_style)
        ],
        [
            Paragraph(f"<b>Election:</b> {nomination.election.title}", body_style),
            Paragraph(f"<b>Constituency:</b> {nomination.constituency.name} ({nomination.constituency.constituency_type})", body_style)
        ],
        [
            Paragraph(f"<b>Submitted On:</b> {nomination.submission_timestamp.strftime('%d-%m-%Y %H:%M:%S') if nomination.submission_timestamp else 'Draft'}", body_style),
            Paragraph(f"<b>Security Deposit:</b> {format_inr(nomination.security_deposit_amount)} (Ref: {nomination.security_deposit_ref or 'N/A'})", body_style)
        ]
    ]
    info_table = Table(info_data, colWidths=[260, 260])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))
    
    # Part 1: Candidate Particulars
    story.append(Paragraph("PART A: CANDIDATE PARTICULARS", section_style))
    part_a_data = [
        [Paragraph("<b>Candidate Full Name:</b>", body_style), Paragraph(nomination.candidate.full_name, bold_body_style),
         Paragraph("<b>Relation:</b>", body_style), Paragraph(f"{nomination.relation_type}: {nomination.father_or_spouse_name or 'N/A'}", body_style)],
        [Paragraph("<b>Age & Gender:</b>", body_style), Paragraph(f"{nomination.age or 'N/A'} yrs | {nomination.gender or 'N/A'}", body_style),
         Paragraph("<b>Date of Birth:</b>", body_style), Paragraph(nomination.date_of_birth.strftime('%d-%m-%Y') if nomination.date_of_birth else 'N/A', body_style)],
        [Paragraph("<b>Category:</b>", body_style), Paragraph(nomination.candidate_category, body_style),
         Paragraph("<b>PAN Number:</b>", body_style), Paragraph(nomination.pan_number or 'N/A', bold_body_style)],
        [Paragraph("<b>Mobile / Email:</b>", body_style), Paragraph(f"{nomination.candidate.mobile} / {nomination.candidate.email}", body_style),
         Paragraph("<b>Identity (EPIC):</b>", body_style), Paragraph(nomination.epic_number or nomination.candidate.identity_number or 'N/A', body_style)],
        [Paragraph("<b>Electoral Roll Entry:</b>", body_style), Paragraph(f"Part No: {nomination.electoral_roll_part_no or 'N/A'}, Serial No: {nomination.electoral_roll_serial_no or 'N/A'} ({nomination.electoral_roll_constituency or 'N/A'}, {nomination.electoral_roll_state or 'N/A'})", body_style),
         Paragraph("<b>Party / Affiliation:</b>", body_style), Paragraph(f"{nomination.party_name or 'Independent'} ({nomination.party_type.replace('_', ' ').title()})", bold_body_style)],
        [Paragraph("<b>Present Address:</b>", body_style), Paragraph(nomination.address or 'N/A', body_style),
         Paragraph("<b>Permanent Address:</b>", body_style), Paragraph(nomination.permanent_address or nomination.address or 'N/A', body_style)],
        [Paragraph("<b>Profession/Occupation:</b>", body_style), Paragraph(nomination.profession_or_occupation or 'N/A', body_style),
         Paragraph("<b>Highest Education:</b>", body_style), Paragraph(nomination.highest_education or 'N/A', body_style)]
    ]
    t_part_a = Table(part_a_data, colWidths=[110, 150, 110, 150])
    t_part_a.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_part_a)
    story.append(Spacer(1, 8))
    
    # Part B: Criminal Antecedents
    story.append(Paragraph("PART B: CRIMINAL ANTECEDENTS DECLARATION", section_style))
    has_crim = "YES" if nomination.has_criminal_cases else "NO (Clean Record Declared)"
    has_conv = "YES" if nomination.has_convictions else "NO (No Convictions Declared)"
    
    crim_color = colors.HexColor('#DC2626') if (nomination.has_criminal_cases or nomination.has_convictions) else colors.HexColor('#16A34A')
    
    crim_data = [
        [
            Paragraph("<b>Pending Criminal Cases:</b>", body_style),
            Paragraph(f"<font color='{crim_color}'><b>{has_crim}</b></font>", bold_body_style),
            Paragraph("<b>Convictions & Penalties:</b>", body_style),
            Paragraph(f"<font color='{crim_color}'><b>{has_conv}</b></font>", bold_body_style)
        ],
        [
            Paragraph("<b>Details of Cases:</b>", body_style),
            Paragraph(nomination.criminal_cases_details or "No pending criminal cases reported by candidate under Section 33A of the Representation of the People Act, 1951.", body_style),
            Paragraph("<b>Conviction Particulars:</b>", body_style),
            Paragraph(nomination.conviction_details or "No record of conviction for offenses mentioned in Section 8(1), (2), (3) of RPA 1951.", body_style)
        ]
    ]
    t_crim = Table(crim_data, colWidths=[110, 150, 110, 150])
    t_crim.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_crim)
    story.append(Spacer(1, 8))
    
    # Part C: Smart Asset & Liability Declaration
    story.append(Paragraph("PART C: SMART DECLARATION OF ASSETS & LIABILITIES (INR)", section_style))
    nomination.calculate_totals()
    
    asset_data = [
        [Paragraph("<b>Category</b>", bold_body_style), Paragraph("<b>Item / Head</b>", bold_body_style), Paragraph("<b>Declared Amount</b>", bold_body_style)],
        [Paragraph("Movable Assets", body_style), Paragraph("1. Cash in hand", body_style), Paragraph(format_inr(nomination.movable_cash), body_style)],
        [Paragraph("", body_style), Paragraph("2. Bank Deposits & Accounts", body_style), Paragraph(format_inr(nomination.movable_bank_deposits), body_style)],
        [Paragraph("", body_style), Paragraph("3. Bonds, Debentures, Shares, Mutual Funds", body_style), Paragraph(format_inr(nomination.movable_bonds_shares), body_style)],
        [Paragraph("", body_style), Paragraph("4. Motor Vehicles / Aircraft / Yachts", body_style), Paragraph(format_inr(nomination.movable_vehicles), body_style)],
        [Paragraph("", body_style), Paragraph("5. Jewellery, Bullion & Valuable items", body_style), Paragraph(format_inr(nomination.movable_jewellery), body_style)],
        [Paragraph("", body_style), Paragraph("6. Other movable assets / receivables", body_style), Paragraph(format_inr(nomination.movable_other), body_style)],
        [Paragraph("<b>SUB-TOTAL MOVABLE</b>", bold_body_style), Paragraph("", body_style), Paragraph(f"<b>{format_inr(nomination.total_movable_assets)}</b>", bold_body_style)],
        
        [Paragraph("Immovable Assets", body_style), Paragraph("1. Agricultural Land", body_style), Paragraph(format_inr(nomination.immovable_agricultural), body_style)],
        [Paragraph("", body_style), Paragraph("2. Non-Agricultural Land", body_style), Paragraph(format_inr(nomination.immovable_non_agricultural), body_style)],
        [Paragraph("", body_style), Paragraph("3. Commercial Buildings & Shops", body_style), Paragraph(format_inr(nomination.immovable_commercial), body_style)],
        [Paragraph("", body_style), Paragraph("4. Residential Buildings & Apartments", body_style), Paragraph(format_inr(nomination.immovable_residential), body_style)],
        [Paragraph("", body_style), Paragraph("5. Others (e.g. inherited interest in property)", body_style), Paragraph(format_inr(nomination.immovable_other), body_style)],
        [Paragraph("<b>SUB-TOTAL IMMOVABLE</b>", bold_body_style), Paragraph("", body_style), Paragraph(f"<b>{format_inr(nomination.total_immovable_assets)}</b>", bold_body_style)],
        
        [Paragraph("Liabilities", body_style), Paragraph("1. Loans from Banks / Financial Institutions", body_style), Paragraph(format_inr(nomination.liabilities_bank_loans), body_style)],
        [Paragraph("", body_style), Paragraph("2. Government Dues (Taxes, Electricity, Municipal)", body_style), Paragraph(format_inr(nomination.liabilities_govt_dues), body_style)],
        [Paragraph("", body_style), Paragraph("3. Other liabilities & private loans", body_style), Paragraph(format_inr(nomination.liabilities_other), body_style)],
        [Paragraph("<b>TOTAL LIABILITIES</b>", bold_body_style), Paragraph("", body_style), Paragraph(f"<b>{format_inr(nomination.total_liabilities)}</b>", bold_body_style)],
        
        [Paragraph("<b>NET WORTH (Assets - Liabilities)</b>", bold_body_style), Paragraph("", body_style), 
         Paragraph(f"<b>{format_inr((nomination.total_movable_assets + nomination.total_immovable_assets) - nomination.total_liabilities)}</b>", bold_body_style)],
    ]
    
    t_asset = Table(asset_data, colWidths=[150, 220, 150])
    t_asset.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BACKGROUND', (0,7), (-1,7), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,13), (-1,13), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,17), (-1,17), colors.HexColor('#FEE2E2')),
        ('BACKGROUND', (0,18), (-1,18), colors.HexColor('#DCFCE7')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('ALIGN', (2,0), (2,-1), 'RIGHT'),
    ]))
    story.append(t_asset)
    story.append(Spacer(1, 8))
    
    # Proposers Summary
    proposers = nomination.get_proposers_list()
    story.append(Paragraph(f"PART D: ELECTOR PROPOSERS (Total: {len(proposers)} of required {nomination.proposers_count})", section_style))
    if proposers:
        prop_rows = [[Paragraph("<b>#</b>", bold_body_style), Paragraph("<b>Proposer Name</b>", bold_body_style), Paragraph("<b>EPIC / Voter ID</b>", bold_body_style), Paragraph("<b>Electoral Roll Part/Sl</b>", bold_body_style)]]
        for idx, p in enumerate(proposers, start=1):
            prop_rows.append([
                Paragraph(str(idx), body_style),
                Paragraph(p.get('name', 'N/A'), body_style),
                Paragraph(p.get('epic', 'N/A'), body_style),
                Paragraph(f"Part {p.get('part_no', '-')}, Sl {p.get('serial_no', '-')}", body_style)
            ])
        t_prop = Table(prop_rows, colWidths=[30, 200, 140, 150])
        t_prop.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_prop)
    else:
        story.append(Paragraph("No proposers recorded yet.", body_style))
        
    story.append(Spacer(1, 10))
    
    # Verification & Signatures block
    story.append(Paragraph("PART E: SOLEMN VERIFICATION & RETURNING OFFICER SCRUTINY ORDER", section_style))
    
    verif_text = (
        "I, the candidate above-named, do hereby verify and declare that the contents of this affidavit "
        "are true and correct to the best of my knowledge and belief and no part of it is false and nothing "
        "material has been concealed therefrom. (Academic Demonstration Prototype)"
    )
    story.append(Paragraph(verif_text, ParagraphStyle('Verif', parent=body_style, fontSize=8, leading=10, textColor=colors.HexColor('#475569'))))
    story.append(Spacer(1, 10))
    
    scrutiny_status_text = f"DECISION: {nomination.scrutiny_decision.upper() if nomination.scrutiny_decision else 'PENDING SCRUTINY'}"
    scrutiny_remarks_text = nomination.scrutiny_remarks or "Nomination paper under statutory scrutiny by the Returning Officer / Assistant Returning Officer."
    
    sig_data = [
        [
            Paragraph("<b>Candidate Electronic Signature / Affirmation</b><br/><br/>"
                      f"Signed by: <b>{nomination.candidate.full_name}</b><br/>"
                      f"Identity Ref: {nomination.epic_number or nomination.candidate.identity_number or 'Voter ID'}<br/>"
                      f"Submitted: {nomination.submission_timestamp.strftime('%d-%m-%Y %H:%M') if nomination.submission_timestamp else 'Draft'}", body_style),
            Paragraph(f"<b>Returning Officer Scrutiny Record</b><br/><br/>"
                      f"<b>{scrutiny_status_text}</b><br/>"
                      f"Remarks: {scrutiny_remarks_text}<br/>"
                      f"Scrutinized On: {nomination.scrutiny_timestamp.strftime('%d-%m-%Y %H:%M') if nomination.scrutiny_timestamp else 'Awaiting hearing'}<br/>"
                      f"Office of the RO, {nomination.constituency.name}", body_style)
        ]
    ]
    t_sig = Table(sig_data, colWidths=[260, 260])
    t_sig.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#0F172A')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_sig)
    
    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    buffer.seek(0)
    return buffer

def generate_acknowledgment_receipt_pdf(nomination):
    """
    Generates an official Acknowledgment Receipt given to the candidate
    upon physical/online nomination delivery.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=50,
        bottomMargin=45
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('RecTitle', parent=styles['Heading1'], fontSize=16, alignment=1, textColor=colors.HexColor('#1E3A8A'))
    sub_title_style = ParagraphStyle('RecSubTitle', parent=styles['Normal'], fontSize=9, alignment=1, textColor=colors.HexColor('#475569'))
    body_style = ParagraphStyle('RecBody', parent=styles['Normal'], fontSize=9.5, leading=14, textColor=colors.HexColor('#1E293B'))
    bold_style = ParagraphStyle('RecBold', parent=styles['Normal'], fontSize=9.5, leading=14, fontName='Helvetica-Bold', textColor=colors.HexColor('#0F172A'))
    
    story = []
    story.append(Paragraph("ELECTION COMMISSION ACADEMIC SIMULATION PORTAL", sub_title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("ACKNOWLEDGMENT RECEIPT OF NOMINATION PAPER", title_style))
    story.append(Paragraph("[See Rule 4 of the Conduct of Elections Rules, 1961 (Simulated Prototype)]", sub_title_style))
    story.append(Spacer(1, 15))
    
    receipt_data = [
        [Paragraph("<b>Receipt / Application No:</b>", body_style), Paragraph(nomination.application_number, bold_style)],
        [Paragraph("<b>Election Title:</b>", body_style), Paragraph(nomination.election.title, body_style)],
        [Paragraph("<b>Constituency:</b>", body_style), Paragraph(f"{nomination.constituency.name} ({nomination.constituency.state})", bold_style)],
        [Paragraph("<b>Candidate Name:</b>", body_style), Paragraph(nomination.candidate.full_name, bold_style)],
        [Paragraph("<b>Father's / Spouse's Name:</b>", body_style), Paragraph(nomination.father_or_spouse_name or 'N/A', body_style)],
        [Paragraph("<b>Party Affiliation:</b>", body_style), Paragraph(nomination.party_name or 'Independent', body_style)],
        [Paragraph("<b>Submission Date & Time:</b>", body_style), Paragraph(nomination.submission_timestamp.strftime('%d-%B-%Y at %I:%M %p') if nomination.submission_timestamp else 'In Progress', body_style)],
        [Paragraph("<b>Security Deposit Received:</b>", body_style), Paragraph(f"{format_inr(nomination.security_deposit_amount)} (Challan/Ref: {nomination.security_deposit_ref or 'Verified'})", body_style)],
        [Paragraph("<b>Current Scrutiny Status:</b>", body_style), Paragraph(f"<b>{nomination.status.replace('_', ' ').upper()}</b>", bold_style)],
        [Paragraph("<b>Scheduled Scrutiny Date:</b>", body_style), Paragraph(nomination.election.scrutiny_date.strftime('%d-%B-%Y') if nomination.election.scrutiny_date else 'As notified by RO', body_style)],
    ]
    
    t_receipt = Table(receipt_data, colWidths=[180, 335])
    t_receipt.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#1E3A8A')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F8FAFC')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_receipt)
    story.append(Spacer(1, 20))
    
    note_text = (
        "<b>Important Notice for Candidate:</b><br/>"
        "1. This receipt acknowledges electronic transmission of the nomination paper & smart affidavit (Form 26).<br/>"
        "2. The candidate or their authorized representative is requested to be present at the Office of the Returning Officer "
        "on the date fixed for scrutiny of nomination papers.<br/>"
        "3. This is an educational demonstration document produced by the Election Candidate Smart Declaration Portal prototype."
    )
    story.append(Paragraph(note_text, ParagraphStyle('Notice', parent=body_style, fontSize=8.5, leading=12, textColor=colors.HexColor('#475569'))))
    story.append(Spacer(1, 25))
    
    # Official Signature Box
    sig_table = Table([
        [
            Paragraph("<b>Authorized Candidate / Proposer</b><br/><br/><br/>________________________<br/>Signature", body_style),
            Paragraph("<b>Office of the Returning Officer</b><br/><br/><br/>________________________<br/>Signature & Official Seal", body_style)
        ]
    ], colWidths=[250, 265])
    sig_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))
    story.append(sig_table)
    
    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    buffer.seek(0)
    return buffer

