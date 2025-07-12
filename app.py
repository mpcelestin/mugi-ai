from flask import Flask, request, jsonify, render_template
import difflib
from duckduckgo_search import DDGS
import sqlite3
from datetime import datetime
import random, uuid
from flask import session
from collections import defaultdict



app = Flask(__name__)
app.secret_key = 'd29c234ca310aa6990092d4b6cd4c4854585c51e1f73bf4de510adca03f5bc4e'

# === BIC DATA ===
bic_data = {
    "about": "Business Insurance and Reinsurance Company (BIC Non-Vie SA) is a leading Burundian insurance company established in 2017, specializing in general insurance (Non-Vie) services. We provide comprehensive risk management solutions to individuals and businesses across Burundi.",
    "mission": "To deliver exceptional insurance services through innovation, professionalism, and client-centric solutions that mitigate risks and protect our clients' assets.",
    "vision": "To be the most trusted and technologically advanced insurance provider in Burundi and the Great Lakes region by 2030.",
    "values": ["Client focus & availability", "Integrity & fairness", "Teamwork", "Professionalism", "Dependability", "Solidarity & trust"],
    "products": {
        "auto": {
            "description": "Comprehensive motor vehicle insurance covering accidents, theft, third-party liability, and own damage.",
            "sub_products": ["Third-Party Liability", "Comprehensive", "COMESA Yellow Card"],
            "documents": ["Carte rose", "Valid ID", "Previous insurance certificate (if any)"],
            "claims": ["Police report", "Photos of damage", "Completed claim form"],
            "premium_factors": ["Vehicle value", "Driver age", "Claims history", "Coverage type"]
        },
        "fire": {
            "description": "Property insurance covering buildings and contents against fire, lightning, explosion, and related perils.",
            "coverage": ["Fire damage", "Lightning", "Explosion", "Aircraft damage"],
            "exclusions": ["War risks", "Nuclear risks", "Intentional damage"],
            "premium_factors": ["Property value", "Construction type", "Fire protection measures"]
        },
        "accident": {
            "description": "Personal accident coverage providing compensation for bodily injuries from unforeseen events.",
            "benefits": ["Medical expenses", "Temporary disability", "Permanent disability", "Death benefit"],
            "premium_factors": ["Occupation risk", "Coverage amount", "Number of insured"]
        },
        "travel": {
            "description": "International travel insurance covering medical emergencies, trip cancellations, and lost luggage.",
            "coverage": ["Medical expenses abroad", "Trip cancellation", "Lost luggage", "Repatriation"],
            "premium_factors": ["Destination", "Trip duration", "Age of traveler"]
        },
        "marine": {
            "description": "Insurance for watercraft and marine cargo, covering physical damage and liability risks.",
            "types": ["Hull insurance", "Protection & Indemnity", "Cargo insurance"],
            "premium_factors": ["Vessel value", "Navigation area", "Cargo type"]
        },
        "engineering": {
            "description": "Coverage for construction projects, machinery, and erection risks.",
            "policies": ["Contractors All Risks (CAR)", "Erection All Risks (EAR)", "Machinery Breakdown"],
            "premium_factors": ["Project value", "Contract duration", "Safety measures"]
        },
        "liability": {
            "description": "Protection against legal liabilities to third parties.",
            "types": ["Public Liability", "Product Liability", "Professional Indemnity"],
            "premium_factors": ["Business type", "Revenue", "Claims history"]
        },
        "health": {
            "description": "Group and individual health insurance policies.",
            "plans": ["Inpatient", "Outpatient", "Dental", "Maternity"],
            "premium_factors": ["Age", "Medical history", "Coverage scope"]
        },
        "history": "BIC Non-Vie SA was established in 2017 in Burundi. It has rapidly grown to become one of the most innovative insurers in the country, with a network of over 30 branches nationwide. The company specializes in non-life insurance products and has been recognized for its digital transformation in the insurance sector."
    },
    "procedures": {
        "claims": {
            "process": [
                "1. Notify BIC immediately after incident",
                "2. Complete claim form (available at any branch)",
                "3. Submit supporting documents",
                "4. Assessment by claims adjuster",
                "5. Approval and payment"
            ],
            "timeframe": "Most claims are processed within 14 working days after complete documentation is received."
        },
        "underwriting": {
            "process": [
                "1. Risk assessment and evaluation",
                "2. Premium calculation based on risk factors",
                "3. Policy issuance",
                "4. Continuous risk monitoring"
            ]
        },
        "reinsurance": {
            "process": [
                "1. Risk analysis and cession decision",
                "2. Placement with reinsurers",
                "3. Treaty negotiation",
                "4. Premium payment and risk transfer"
            ],
            "partners": ["African Reinsurance Corporation", "Kenya Re", "ZEP-RE", "Hannover Re"]
        }
    },
    "contact": {
        "email": "info@bic.bi",
        "phone": "+257 22 28 0042",
        "website": "www.bic.bi",
        "emergency": "+257 79 900 000",
        "location": "Avenue de l'ONU No.6, Rohero I, Bujumbura, Burundi",
        "working_hours": "Monday-Friday: 8:00 AM - 5:00 PM\nSaturday: 9:00 AM - 1:00 PM"
    },
    "financial": {
        "rating": "A- (Stable outlook) by ARCA",
        "capital": "5 billion BIF",
        "solvency": "150% of regulatory requirement"
    },
    "branches": [
        {'name': 'BIC SIEGE', 'phone': '+25762555777', 'location': 'Bujumbura'},
        {'name': 'AGENCE KAMENGE', 'phone': '+25779721192', 'location': 'Bujumbura'},
        {'name': 'AGENCE KINAMA II', 'phone': '+25769100024', 'location': 'Bujumbura'},
        {'name': 'AGENCE CARAMA II', 'phone': '+25765183560', 'location': 'Bujumbura'},
        {'name': 'AGENCE NGOZI', 'phone': '+25779726410', 'location': 'Ngozi'},
        {'name': 'AGENCE KIRUNDO', 'phone': '+25779884523', 'location': 'Kirundo'},
        {'name': 'AGENCE MUYINGA/KOBERO I', 'phone': '+25769776088', 'location': 'Muyinga'},
        {'name': 'AGENCE RUYIGI', 'phone': '+25769487436', 'location': 'Ruyigi'},
        {'name': 'AGENCE KAYANZA V', 'phone': '+25769305007', 'location': 'Kayanza'},
        {'name': 'AGENCE KAYANZA II', 'phone': '+25761685573', 'location': 'Kayanza'},
        {'name': 'AGENCE RUBIRIZI', 'phone': '+25769406473', 'location': 'Bujumbura'},
        {'name': 'AGENCE GITEGA', 'phone': '+25762274776', 'location': 'Gitega'},
        {'name': 'AGENCE RUTANA', 'phone': '+25767539556', 'location': 'Rutana'},
        {'name': 'AGENCE RUTANA/GIHARO', 'phone': '+25768147654', 'location': 'Rutana'},
        {'name': 'AGENCE RUMONGE', 'phone': '+25761186688', 'location': 'Rumonge'},
        {'name': 'CANKUZO', 'phone': '+25762183760', 'location': 'Cankuzo'},
        {'name': 'AGENCE MATANA', 'phone': '+25767269307', 'location': 'Matana'},
        {'name': 'AGENCE RUGOMBO', 'phone': '+25761508088', 'location': 'Rugombo'},
        {'name': 'AGENCE CIBITOKE E-HOME', 'phone': '+25767676373', 'location': 'Cibitoke'},
        {'name': 'AGENCE BUKEYE', 'phone': '+25771988517', 'location': 'Bukeye'},
        {'name': 'AGENCE NGOZI I', 'phone': '+25768596164', 'location': 'Ngozi'},
        {'name': 'AGENCE MASANGANZIRA', 'phone': '+25761140429', 'location': 'Masanganzira'},
        {'name': 'AGENCE MAKAMBA', 'phone': '+25762387745', 'location': 'Makamba'},
        {'name': 'AGENCE NYANZA LAC', 'phone': '+25762692223', 'location': 'Nyanza Lac'},
        {'name': 'AGENCE MUSENYI', 'phone': '+25779918552', 'location': 'Musenyi'},
        {'name': 'AGENCE BUBANZA', 'phone': '+25779999811', 'location': 'Bubanza'},
        {'name': 'AGENCE KINAMA A', 'phone': '+25779999811', 'location': 'Bujumbura'},
        {'name': 'GUICHER MARCHER KINAMA', 'phone': '+25779918735', 'location': 'Bujumbura'},
        {'name': 'GUICHET MAIRIE', 'phone': '+25779746410', 'location': 'Bujumbura'},
        {'name': 'GUICHET COTEBU E-HOME', 'phone': '+25768026070', 'location': 'Bujumbura'}
    ]
}

# === KNOWLEDGE BASE ===
knowledge_entries = [
    # Company Information
    (["about bic", "what is bic", "bic company", "bic overview", "bic non vie"],bic_data["about"]),
 
    (["mission", "bic mission", "company mission"], bic_data["mission"]),
    (["values", "bic values", "company values"], bic_data["values"]),
    (["vision", "bic vision", "company vision"], bic_data["vision"]),
    (["history of bic", "bic history", "how bic started", "when was bic created"], bic_data["products"]["history"]),

    # Products and Services
    (
        ["products", "insurance types", "what do you offer", "services", "coverages"],
        "<b>BIC Products:</b><br><ul>" + "".join(
            f"<li><b>{p.title()}</b>: {d['description']} <i>(Ask me for details about {p} insurance)</i></li>" 
            for p, d in bic_data["products"].items() if isinstance(d, dict)
        ) + "</ul>"
    ),
    
    # Claims Process
    (
        ["how to make a claim", "claims process", "file a claim", "claim procedure"],
        "<b>Claims Process:</b><br><ol>" + "".join(
            f"<li>{step}</li>" for step in bic_data["procedures"]["claims"]["process"]
        ) + f"</ol><br><b>Typical processing time:</b> {bic_data['procedures']['claims']['timeframe']}"
    ),
    
    # Underwriting
    (
        ["underwriting process", "how policies are issued", "risk assessment"],
        "<b>Underwriting Process:</b><br><ol>" + "".join(
            f"<li>{step}</li>" for step in bic_data["procedures"]["underwriting"]["process"]
        ) + "</ol>"
    ),
    
    # Reinsurance
    (
        ["reinsurance process", "how reinsurance works at bic", "ceded business"],
        "<b>Reinsurance Process:</b><br><ol>" + "".join(
            f"<li>{step}</li>" for step in bic_data["procedures"]["reinsurance"]["process"]
        ) + f"</ol><br><b>Main Reinsurers:</b> {', '.join(bic_data['procedures']['reinsurance']['partners'])}"
    ),
    
    # Financial Information
    (
        ["financial rating", "bic financial strength", "company rating"],
        f"BIC Non-Vie SA has a financial rating of <b>{bic_data['financial']['rating']}</b> with a capital base of <b>{bic_data['financial']['capital']}</b> and solvency ratio of <b>{bic_data['financial']['solvency']}</b>."
    ),
    
    # Contact Information
    (
        ["contact bic", "how to reach bic", "bic contacts", "customer service"],
        f"<b>Contact BIC:</b><br>Email: <a href='mailto:{bic_data['contact']['email']}'>{bic_data['contact']['email']}</a><br>"
        f"Phone: <a href='tel:{bic_data['contact']['phone']}'>{bic_data['contact']['phone']}</a><br>"
        f"Emergency: <a href='tel:{bic_data['contact']['emergency']}'>{bic_data['contact']['emergency']}</a><br>"
        f"Website: <a href='https://{bic_data['contact']['website']}' target='_blank'>{bic_data['contact']['website']}</a><br>"
        f"Location: {bic_data['contact']['location']}<br>"
        f"Working Hours: {bic_data['contact']['working_hours'].replace('\n', '<br>')}"
    ),
    
    # AI Information
    (
        ["who are you", "what is your name", "who is this", "what are you", "uri igiki"],
        "I am Mugi AI - The official digital assistant for BIC Non-Vie SA. I can help you with insurance information, claims, products, and more!"
    ),
    (
        ["who developed you", "who created you", "who made you"],
        "I was developed by BIC's Digital Transformation Team, led by MUGISHA PIERRE CELESTIN."
    ),
    (
        ["how can i contact your developer","Who is him","who is MUGISHA","who is Pierre","Who is celestin","what is him", "developer contact", "contact developer", "developer email", "developer phone"],
        "You can contact my developer at:<br>Email: <a href='mailto:mugishapc1@gmail.com'>mugishapc1@gmail.com</a><br>"
        "Phone: <a href='https://wa.me/25725768596164' target='_blank'>+257 25 768 596 164 (WhatsApp)</a>"
    ),
    
    # Greetings and Friendship
    (
        ["hello", "hi", "hey", "good morning", "good evening", "good afternoon", "salut", "bonjour"],
        random.choice([
            "Hello! I'm Mugi AI, your BIC insurance assistant. How can I help you today?",
            "Hi there! Ready to assist with all your insurance needs.",
            "Good day! What insurance question can I answer for you today?"
        ])
    ),
    (
        ["how are you", "how are you doing", "are you okay", "ça va"],
        random.choice([
            "I'm functioning perfectly, thank you! How can I assist you today?",
            "Doing great! Ready to help with your insurance queries.",
            "I'm always at my best when helping BIC clients like you!"
        ])
    ),
    (
        ["thank you", "thanks", "merci", "thanks a lot", "thank you very much"],
        random.choice([
            "You're welcome! Protecting what matters to you is our pleasure.",
            "Happy to help! Let me know if you have any other questions.",
            "Thank you for choosing BIC! We appreciate your trust."
        ])
    ),
    (
        ["when were you born", "your birthday", "when was mugi ai born"],
        "I was launched in July 2025 as part of BIC's digital transformation initiative to enhance customer service."
    ),
    (
        ["tell me a joke", "say something funny", "make me laugh"],
        random.choice([
            "Why did the insurance agent bring a ladder to work? To reach the high premiums!",
            "How does an insurance company stay cool? With premium air conditioning!",
            "Why was the insurance policy a good comedian? It always had the best coverage!"
        ])
    ),
    (
        ["you are amazing", "you are smart", "you are helpful"],
        random.choice([
            "Thank you! I'm here to make insurance easy for you.",
            "You're too kind! I'm just doing my job to serve BIC clients.",
            "Merci beaucoup! Your satisfaction is my top priority."
        ])
    ),
    
    # Insurance Terms
    (
        ["what is a premium", "define premium", "insurance premium"],
        "A premium is the amount you pay for your insurance policy, typically monthly or annually. It's calculated based on the risk being insured."
    ),
    (
        ["what is a deductible", "define deductible", "excess in insurance"],
        "A deductible is the amount you agree to pay out-of-pocket before your insurance coverage kicks in. Higher deductibles usually mean lower premiums."
    ),
    (
        ["what is underwriting", "define underwriting"],
        "Underwriting is the process where insurers evaluate the risks of insuring a person or asset and determine the appropriate premium and policy terms."
    ),
    (
        ["what is reinsurance", "define reinsurance"],
        "Reinsurance is insurance for insurance companies. It allows insurers to transfer portions of their risk portfolios to other parties to reduce the likelihood of paying large obligations."
    ),
    
    # Regulatory Information
    (
        ["insurance regulations in burundi", "arca regulations", "legal framework"],
        "The insurance sector in Burundi is regulated by ARCA (Autorité de Régulation et de Contrôle des Assurances). They oversee solvency requirements, policy terms, and market conduct."
    ),
    (
        ["solvency requirements", "capital requirements"],
        f"BIC maintains a solvency ratio of {bic_data['financial']['solvency']}, well above the regulatory minimum set by ARCA."
    ),

    # === SCENARIOS ADDED HERE ===
    # 1. Accident Claims Scenario
    (
        ["car accident", "had an accident", "vehicle crash", "road accident", "what to do after accident"],
        "Sorry to hear about the accident! Here's what to do:<br><br>"
        "1. Call BIC Emergency: <a href='tel:+25779900000'>+257 79 900 000</a><br>"
        "2. Get a police report (required for claims)<br>"
        "3. Take photos of the damage<br>"
        "4. Visit any BIC branch within 24 hours to file your claim<br><br>"
        "Need help locating the nearest branch?"
    ),

    # 2. COMESA Insurance Inquiry
    (
        ["COMESA insurance", "cross-border insurance", "traveling to Rwanda", "traveling to DRC", "yellow card"],
        "Yes! COMESA Yellow Card is mandatory for cross-border travel. At BIC, you'll need:<br><br>"
        "1. Your Carte Rose<br>"
        "2. ID Copy<br>"
        "3. Payment<br><br>"
        "Processing takes 20 minutes at any branch. Would you like branch locations?"
    ),

    # 3. Fire Insurance for Businesses
    (
        ["shop fire insurance", "business fire coverage", "fire protection for shop", "kayanza shop insurance"],
        "BIC's fire insurance covers:<br>"
        "✔ Fire damage<br>"
        "✔ Lightning strikes<br>"
        "✔ Explosion damage<br><br>"
        "Exclusions: Intentional fires or war risks.<br>"
        "Premium starts at 15,000 BIF/month based on shop value. Need a quote?"
    ),

    # 4. Delayed Claim Follow-Up
    (
        ["claim not paid", "delayed claim", "claim status", "where is my claim money"],
        "Claims typically process in 14 working days. Let me check:<br><br>"
        "1. Was your documentation complete? (Police report, photos, form)<br>"
        "2. You can call Claims Dept: <a href='tel:+25722280042'>+257 22 28 0042</a> (Ext. 112)<br><br>"
        "Or share your claim number for deeper checks."
    ),

    # 5. Premium Payment Issues
    (
        ["can't pay premium", "lost job can't pay", "payment difficulties", "financial problems"],
        "We understand. You can:<br><br>"
        "1. Adjust coverage to lower costs<br>"
        "2. Request 3-month grace period (fees apply)<br>"
        "3. Suspend policy temporarily<br><br>"
        "Visit any branch with your ID to discuss. Would you like the nearest location?"
    ),

    # 6. Policy Renewal Reminder
    (
        ["when does my policy expire", "renewal date", "auto insurance expiry"],
        "Your policy (ID: ****1234) expires on 15/10/2024.<br>"
        "Renew 30 days early to avoid lapses! Options:<br><br>"
        "1. Walk-in renewal at branches<br>"
        "2. Mobile money payment (Tigo Cash: *123#)<br><br>"
        "Need the renewal form?"
    ),

    # 7. Fake Policy Alert
    (
        ["fake policy", "verify insurance", "agent fraud", "scam insurance"],
        "⚠️ Only buy from official BIC branches/website. To verify:<br><br>"
        "1. Send policy number to <a href='mailto:info@bic.bi'>info@bic.bi</a><br>"
        "2. Call Fraud Hotline: <a href='tel:+25779111222'>+257 79 111 222</a><br>"
        "3. Visit our head office for free validation<br><br>"
        "Never share money with unauthorized agents!"
    ),

    # 8. Health Insurance for Families
    (
        ["maternity coverage", "pregnancy insurance", "health insurance for family"],
        "Yes! Our health plans include:<br><br>"
        "✔ Prenatal care<br>"
        "✔ Delivery costs<br>"
        "✔ Newborn coverage (first 3 months)<br><br>"
        "Waiting period: 6 months. Premium starts at 50,000 BIF/month. Want to compare plans?"
    ),

    # 9. Rejected Claim Appeal
    (
        ["claim denied", "appeal rejected claim", "negligence claim"],
        "You can:<br><br>"
        "1. Request written explanation from <a href='mailto:claims@bic.bi'>claims@bic.bi</a><br>"
        "2. Appeal within 30 days with new evidence<br>"
        "3. ARCA mediation if unresolved<br><br>"
        "Need help drafting your appeal letter?"
    ),

    # 10. Business Package Inquiry
    (
        ["hotel insurance", "business package", "commercial coverage", "Gitega business"],
        "Recommended package:<br><br>"
        "✔ Fire Insurance (building & contents)<br>"
        "✔ Public Liability (guest injuries)<br>"
        "✔ Business Interruption (closure coverage)<br>"
        "✔ Marine (if near Lake Tanganyika)<br><br>"
        "Let me connect you to our Commercial Risk Advisor?"
    ),

    # Bonus: Casual Scenarios
    (
        ["you're cute", "can we be friends", "i like you"],
        "😊 I'd love to be your insurance friend! How about I help you save 20% on your car insurance instead?"
    ),
    (
        ["tell me a kirundi proverb", "kirundi saying", "burundi wisdom"],
        "'Uburundi si buhiriye' – Burundi isn't inherited (work hard!). Now, can I help insure what you've worked for?"
    ),
    (
        ["i'm bored", "entertain me", "tell me something fun"],
        "Why did the insured tomato stay calm? Because it had peace of mind coverage! 🍅 Now, how about checking your policy expiry date?"
    ),

    # Additional Scenarios
    # 1. Motorcycle Taxi (Taxi-Moto) Insurance in Bujumbura
    (
        ["moto-taxi insurance", "taxi-moto coverage", "motorcycle insurance"],
        "For taxi-motos, we offer:<br><br>"
        "1. Third-Party Only: 25,000 BIF/month (covers damage to others)<br>"
        "2. Full Coverage: 45,000 BIF/month (includes your bike)<br><br>"
        "Required: Carte Rose + Driver's License. Visit AGENCE KAMENGE for quick processing!"
    ),

    # 2. Cross-Border Trucking (DRC Route)
    (
        ["truck insurance", "bukavu route", "cross-border trucking"],
        "You need:<br><br>"
        "1. COMESA Yellow Card (Mandatory)<br>"
        "2. Cargo Insurance (Covers goods in transit)<br>"
        "3. Political Violence Rider (For DRC routes)<br><br>"
        "Processing at BIC SIEGE takes 1 hour. Bring: Vehicle documents + DRC entry permits."
    ),

    # 3. Lake Tanganyika Fishing Boats (Rumonge)
    (
        ["fishing boat insurance", "marine coverage", "rumonge boats"],
        "Yes! Our Marine Package covers:<br><br>"
        "✔ Hull damage (storms/collisions)<br>"
        "✔ Equipment theft<br>"
        "✔ Crew liability<br><br>"
        "Discount available for fleet owners. Visit AGENCE RUMONGE or call <a href='tel:+25761186688'>+257 61 186 688</a>."
    ),

    # 4. Coffee Cooperative (Kayanza)
    (
        ["coffee insurance", "harvest season coverage", "kayanza cooperative"],
        "Recommended:<br><br>"
        "✔ Seasonal Fire Policy (June-August)<br>"
        "✔ Covers storage sheds + drying beds<br>"
        "✔ Premium: 2% of insured value<br><br>"
        "Kayanza farmers get 15% discount! Visit AGENCE KAYANZA V with your harvest estimates."
    ),

    # 5. School Insurance (Ngozi Province)
    (
        ["school insurance", "education coverage", "ngozi school"],
        "BIC's Education Package includes:<br><br>"
        "✔ Building Fire Insurance<br>"
        "✔ Student Accident Coverage<br>"
        "✔ Liability Protection (if a student gets hurt)<br><br>"
        "Exclusive: Pay via mobile money (Lumicash: *555#). Ask for Headmaster Discount!"
    ),

    # 6. Construction Site (Gitega Highway Project)
    (
        ["construction insurance", "engineering coverage", "highway project"],
        "Essential for your project:<br><br>"
        "✔ CAR Insurance (Contractors All Risks)<br>"
        "✔ Delay in Startup Coverage<br>"
        "✔ Third-Party Liability<br><br>"
        "Our engineer will visit your site for assessment. Call <a href='tel:+25779222333'>+257 79 222 333</a> (Ask for Engineering Dept)."
    ),

    # 7. Refugee Camp Clinic (Kibondo Border)
    (
        ["ngo insurance", "clinic coverage", "humanitarian insurance"],
        "Yes! Special NGO Package covers:<br><br>"
        "✔ Medical equipment<br>"
        "✔ Malpractice liability<br>"
        "✔ Refugee patient injuries<br><br>"
        "Note: Requires UNHCR partnership documents. Email <a href='mailto:humanitarian@bic.bi'>humanitarian@bic.bi</a> for fast-tracking."
    ),

    # 8. Kirundi-French Mixed Query
    (
        ["amafaranga ya assurance", "prix assurance voiture", "combien coûte l'assurance"],
        "Bonjour! Premium ya assurance y'umuduga itangura ku:<br><br>"
        "1. 25,000 BIF (Third-Party)<br>"
        "2. 45,000 BIF (Couverture complète)<br><br>"
        "Twakira amafaranga na: MPesa, Tigo Cash, cash muri banki. Ushaka gufata assurance nonaha?"
    ),

    # 9. Flood-Prone Shop (Giharo, Rutana)
    (
        ["flood insurance", "ghiaro coverage", "natural disaster"],
        "Our Natural Disaster Rider (added to fire policy) covers:<br><br>"
        "✔ Flood damage<br>"
        "✔ Mudslide destruction<br>"
        "✔ Storm debris removal<br><br>"
        "Exclusion: Must install sandbags/water barriers. Visit AGENCE RUTANA before November rains!"
    ),

    # 10. Taxi Driver (Night Shift Risk)
    (
        ["taxi insurance", "night coverage", "buja taxi"],
        "Night drivers add:<br><br>"
        "✔ Robbery Coverage (for cash/carjacking)<br>"
        "✔ Passenger Accident Top-Up<br><br>"
        "Costs 10% more but includes 24/7 SOS towing. Present your taxi license at AGENCE RUBIRIZI."
    ),

    # 11. Conflict Zone Coverage (Cibitoke Border)
    (
        ["war risk", "conflict zone", "cibitoke coverage"],
        "Special Conflict Zone Endorsement available through our reinsurer Hannover Re.<br>"
        "Covers:<br><br>"
        "✔ Looting<br>"
        "✔ Border closure losses<br>"
        "✔ Armed damage<br><br>"
        "Requires GPS tracking installation. Contact AGENCE CIBITOKE E-HOME."
    ),

    # 12. Mobile Money Agent Insurance
    (
        ["lumicash insurance", "mobile money coverage", "cash protection"],
        "Mobile Money Agent Package includes:<br><br>"
        "✔ Cash theft (up to 5M BIF/day)<br>"
        "✔ Electronic equipment damage<br>"
        "✔ Customer liability<br><br>"
        "Bonus: Free security stickers from BIC to deter thieves!"
    ),

    # 13. Funeral Parlor Insurance (Makamba)
    (
        ["funeral home insurance", "mortuary coverage", "makamba business"],
        "Professional Services Policy covers:<br><br>"
        "✔ Refrigeration equipment failure<br>"
        "✔ Liability for handling remains<br>"
        "✔ Vehicle fleet for hearses<br><br>"
        "Makamba clients get free first aid kits! Visit AGENCE MAKAMBA."
    ),

    # 14. University Student Query (Ngozi Campus)
    (
        ["student insurance", "laptop coverage", "university protection"],
        "Yes! Student Belongings Policy covers:<br><br>"
        "✔ Theft (with police report)<br>"
        "✔ Accidental damage<br>"
        "✔ Power surge damage<br><br>"
        "Premium: Only 10,000 BIF/month. Valid in dormitories. Sign up at AGENCE NGOZI I."
    ),

    # 15. Post-Election Business Protection
    (
        ["riot coverage", "election insurance", "political violence"],
        "Political Violence Add-On covers:<br><br>"
        "✔ Broken windows/looting<br>"
        "✔ Forced closure losses<br>"
        "✔ Inventory damage<br><br>"
        "Activate 48h before elections. Submit recent property photos to underwriting."
    )
]

# Add detailed product information
for product, details in bic_data["products"].items():
    if isinstance(details, dict):
        # Product description
        knowledge_entries.append((
            [product, f"{product} insurance", f"what is {product} insurance"],
            f"<b>{product.title()} Insurance:</b><br>{details['description']}"
        ))
        
        # Coverage details
        if 'coverage' in details:
            knowledge_entries.append((
                [f"what does {product} cover", f"{product} coverage", f"what's included in {product}"],
                f"<b>{product.title()} Coverage Includes:</b><br><ul>" + 
                "".join(f"<li>{item}</li>" for item in details['coverage']) + "</ul>"
            ))
        
        # Exclusions
        if 'exclusions' in details:
            knowledge_entries.append((
                [f"what doesn't {product} cover", f"{product} exclusions", f"what's excluded from {product}"],
                f"<b>{product.title()} Exclusions:</b><br><ul>" + 
                "".join(f"<li>{item}</li>" for item in details['exclusions']) + "</ul>"
            ))
        
        # Documents required
        if 'documents' in details:
            knowledge_entries.append((
                [f"documents for {product}", f"what do i need for {product}", f"{product} requirements"],
                f"<b>Documents needed for {product.title()} Insurance:</b><br><ul>" + 
                "".join(f"<li>{item}</li>" for item in details['documents']) + "</ul>"
            ))
        
        # Claims process
        if 'claims' in details:
            knowledge_entries.append((
                [f"how to claim {product}", f"{product} claims", f"claim process for {product}"],
                f"<b>{product.title()} Claims Process:</b><br>"
                f"{'<br>'.join(bic_data['procedures']['claims']['process'])}<br>"
                f"<b>Specific documents needed:</b><br><ul>" +
                "".join(f"<li>{item}</li>" for item in details['claims']) + "</ul>"
            ))
        
        # Premium factors
        if 'premium_factors' in details:
            knowledge_entries.append((
                [f"what affects {product} premium", f"{product} premium factors", f"how is {product} premium calculated"],
                f"<b>{product.title()} Premium Factors:</b><br><ul>" + 
                "".join(f"<li>{item}</li>" for item in details['premium_factors']) + "</ul>"
            ))

# === INTELLIGENT RESPONSE ENGINE ===
def fuzzy_search_answer(user_input):
    user_input_lower = user_input.lower()

    # 1. Show all branches
    if any(keyword in user_input_lower for keyword in [
        "all branches", "all agencies", "list of branches", "list of agencies",
        "give me all bic branches", "give me all bic agencies", "bic agences", "bic branches"
    ]):
        full_list = "<b>All BIC Agencies:</b><br><ul>"
        for b in bic_data["branches"]:
            full_list += f"<li><b>{b['name']}</b> ({b['location']}): <a href='tel:{b['phone']}'>{b['phone']}</a></li>"
        full_list += "</ul>"
        return full_list

    # 2. Contact Info
    if "bic" in user_input_lower and any(w in user_input_lower for w in ["contact", "phone", "email", "website"]):
        return (f"<b>Contact BIC:</b><br>Email: <a href='mailto:{bic_data['contact']['email']}'>{bic_data['contact']['email']}</a><br>"
                f"Phone: <a href='tel:{bic_data['contact']['phone']}'>{bic_data['contact']['phone']}</a><br>"
                f"Website: <a href='https://{bic_data['contact']['website']}' target='_blank'>{bic_data['contact']['website']}</a>")

    # 3. Location Info
    if "bic" in user_input_lower and any(w in user_input_lower for w in ["location", "address", "where", "adresse"]):
        return f"<b>Location:</b> {bic_data['contact']['location']}"

    # 4. Emergency contact
    if "emergency" in user_input_lower or "urgent" in user_input_lower or "urgence" in user_input_lower:
        return f"<b>BIC Emergency Contact:</b><br><a href='tel:{bic_data['contact']['emergency']}'>{bic_data['contact']['emergency']}</a>"

    # 5. Working hours
    if any(w in user_input_lower for w in ["working hours", "opening time", "closing time", "heures d'ouverture"]):
        return f"<b>BIC Working Hours:</b><br>{bic_data['contact']['working_hours'].replace('\n', '<br>')}"

    # 6. Premium calculation
    if "calculate premium" in user_input_lower or "how much does" in user_input_lower:
        return ("Premium calculation depends on several factors. For an accurate quote, please visit any BIC branch or "
               "contact our customer service. Generally, premiums are based on: "
               "<ul><li>Value of insured item</li><li>Risk factors</li><li>Coverage type</li><li>Deductible amount</li></ul>")

    # 7. Knowledge base match
    best_match = None
    best_score = 0.0
    for keywords, answer in knowledge_entries:
        for kw in keywords:
            score = difflib.SequenceMatcher(None, user_input_lower, kw).ratio()
            if score > best_score:
                best_score = score
                best_match = answer
    if best_score > 0.4:
        return best_match

    # 8. Match branch name
    matched_branches = []
    for branch in bic_data["branches"]:
        name = branch["name"].lower()
        if name in user_input_lower or any(p in user_input_lower for p in name.split()):
            matched_branches.append(branch)
    if matched_branches:
        response = "Here are the BIC branches related to your query:<br><ul>"
        for b in matched_branches:
            response += f"<li><b>{b['name']}</b> ({b['location']}): <a href='tel:{b['phone']}'>{b['phone']}</a></li>"
        response += "</ul>"
        return response

    return None

def init_db():
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            bot_reply TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Add session_id column if it doesn't exist
    try:
        c.execute("ALTER TABLE chats ADD COLUMN session_id TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()
    conn.close()

# Call it during app startup
init_db()

# === IMPROVED DUCKDUCKGO SEARCH ===
def search_duckduckgo(query):
    try:
        with DDGS() as ddgs:
            # First try to find official BIC pages
            official_results = list(ddgs.text(f"site:bic.bi {query}", max_results=1))
            if official_results:
                return f"I found this on BIC's website: <a href='{official_results[0]['href']}' target='_blank'>{official_results[0]['title']}</a>"
            
            # Then try general insurance information
            general_results = list(ddgs.text(f"insurance {query}", max_results=2))
            if general_results:
                return (f"Here's some general information about '{query}':<br>"
                       f"1. <a href='{general_results[0]['href']}' target='_blank'>{general_results[0]['title']}</a>: {general_results[0]['body']}<br>"
                       f"2. <a href='{general_results[1]['href']}' target='_blank'>{general_results[1]['title']}</a>: {general_results[1]['body']}<br>"
                       f"For BIC-specific information, please contact our offices.")
    except Exception as e:
        print(f"Search error: {e}")
    return ("I couldn't find specific information about that. "
            "For BIC-specific queries, please contact us directly at "
            f"<a href='tel:{bic_data['contact']['phone']}'>{bic_data['contact']['phone']}</a> "
            f"or email <a href='mailto:{bic_data['contact']['email']}'>{bic_data['contact']['email']}</a>.")

# === ROUTES ===
@app.route("/")
def index():
    return render_template("index.html")

# === UPDATED CHAT ROUTE ===
@app.route("/chat", methods=["POST"])
def chat():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"reply": "Please enter a message."})

    if len(user_input) < 2:
        return jsonify({"reply": "Could you please provide more details about your query?"})

    answer = fuzzy_search_answer(user_input)
    if not answer:
        answer = search_duckduckgo(user_input)

    # Save to database
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO chats (user_message, bot_reply, session_id)
        VALUES (?, ?, ?)
    """, (user_input, answer, session['session_id']))
    conn.commit()
    conn.close()

    return jsonify({"reply": answer})


# === New Chat API ===
@app.route("/new-chat", methods=["POST"])
def new_chat():
    session.clear()
    session['session_id'] = str(uuid.uuid4())
    return jsonify({"status": "success", "message": "New chat started."})


# === History Page ===
@app.route("/history")
def history():
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("""
        SELECT user_message, bot_reply, timestamp, session_id
        FROM chats
        ORDER BY id DESC
        LIMIT 200
    """)
    rows = c.fetchall()
    conn.close()

    grouped = defaultdict(list)
    for user_msg, bot_msg, timestamp, session_id in rows:
        if session_id:
            grouped[session_id].append({
                "user_message": user_msg,
                "bot_reply": bot_msg,
                "timestamp": timestamp
            })

    return render_template("history.html", grouped_history=grouped, now=datetime.now)

@app.route("/clear-history", methods=["POST"])
def clear_history():
    current_session = session.get("session_id")
    if current_session:
        conn = sqlite3.connect("chat_history.db")
        c = conn.cursor()
        c.execute("DELETE FROM chats WHERE session_id = ?", (current_session,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Chat history cleared for this session."})
    else:
        return jsonify({"status": "error", "message": "No active session found."})
# === MAIN START ===
if __name__ == "__main__":
    app.run(debug=True) 