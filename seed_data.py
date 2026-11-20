import os
import sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from database import query_db, init_db, db_manager

def seed_database():
    print("[EventEase] Initializing tables...")
    init_db()

    # 1. Seed Categories
    categories = [
        ("Technology & Innovation", "technology-innovation", "Conferences, hackathons, AI workshops and developer summits.", "fas fa-laptop-code"),
        ("Music & Concerts", "music-concerts", "Live bands, symphony orchestras, DJ nights and acoustic sessions.", "fas fa-music"),
        ("Business & Networking", "business-networking", "Startup pitch nights, executive roundtables, and leadership symposiums.", "fas fa-briefcase"),
        ("Art, Design & Culture", "art-design-culture", "Contemporary galleries, photography walks, and digital design exhibitions.", "fas fa-palette"),
        ("Health, Fitness & Sports", "health-fitness-sports", "City marathons, yoga retreats, mindfulness summits, and cycling tours.", "fas fa-running"),
        ("Food & Culinary Arts", "food-culinary-arts", "Gourmet food festivals, wine tastings, pastry masterclasses, and chef popups.", "fas fa-utensils")
    ]

    print("[EventEase] Seeding Categories...")
    for name, slug, desc, icon in categories:
        existing = query_db("SELECT id FROM categories WHERE slug = %s", (slug,), one=True)
        if not existing:
            query_db(
                "INSERT INTO categories (name, slug, description, icon) VALUES (%s, %s, %s, %s)",
                (name, slug, desc, icon),
                commit=True
            )

    # 2. Seed Default Admins
    print("[EventEase] Seeding Admins...")
    admin_user = query_db("SELECT id FROM admins WHERE username = %s", ("admin",), one=True)
    admin_id = None
    if not admin_user:
        hashed_pw = generate_password_hash("Admin@123", method="pbkdf2:sha256")
        res = query_db(
            "INSERT INTO admins (username, full_name, email, password_hash, role) VALUES (%s, %s, %s, %s, %s)",
            ("admin", "EventEase Administrator", "admin@eventease.com", hashed_pw, "superadmin"),
            commit=True
        )
        admin_id = res['lastrowid']
    else:
        admin_id = admin_user['id']

    # 3. Seed Sample Users
    print("[EventEase] Seeding Demo Users...")
    demo_users = [
        ("John Doe", "john.doe@example.com", "User@123", "+1 (555) 234-5678"),
        ("Sarah Jenkins", "sarah.j@example.com", "User@123", "+1 (555) 876-5432"),
        ("Michael Chang", "m.chang@example.com", "User@123", "+1 (555) 432-1098"),
        ("Emma Watson", "emma.w@example.com", "User@123", "+1 (555) 901-2345")
    ]
    user_ids = []
    for full_name, email, password, phone in demo_users:
        u = query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)
        if not u:
            h_pw = generate_password_hash(password, method="pbkdf2:sha256")
            res = query_db(
                "INSERT INTO users (full_name, email, password_hash, phone) VALUES (%s, %s, %s, %s)",
                (full_name, email, h_pw, phone),
                commit=True
            )
            user_ids.append(res['lastrowid'])
        else:
            user_ids.append(u['id'])

    # Get category IDs
    cats = {c['slug']: c['id'] for c in query_db("SELECT id, slug FROM categories")}

    # 4. Seed Realistic Events
    now = datetime.now()
    events = [
        {
            "title": "Global Tech & AI Summit 2026",
            "slug": "global-tech-ai-summit-2026",
            "category_id": cats.get("technology-innovation", 1),
            "description": "Join 2,500+ global technologists, AI researchers, and engineering leads exploring Generative AI, Edge Computing, and Quantum Infrastructure. Features 4 keynote stages, 30 deep-dive workshops, and unmatched networking.",
            "location": "San Francisco, CA",
            "venue_name": "Moscone Convention Center, Hall B",
            "event_date": (now + timedelta(days=14)).strftime("%Y-%m-%d 09:00:00"),
            "banner_image": "tech_summit.svg",
            "ticket_price": 299.00,
            "total_tickets": 500,
            "available_tickets": 420,
            "status": "active"
        },
        {
            "title": "Neon Horizon Indie Music Festival",
            "slug": "neon-horizon-indie-music-festival",
            "category_id": cats.get("music-concerts", 2),
            "description": "An electrifying 3-day outdoor music celebration featuring 45 breakthrough indie, synthwave, and alternative rock artists. Vibrant light installations, artisan food trucks, and unforgettable sunset festival vibes.",
            "location": "Austin, TX",
            "venue_name": "Zilker Metropolitan Park Pavilion",
            "event_date": (now + timedelta(days=21)).strftime("%Y-%m-%d 16:30:00"),
            "banner_image": "music_fest.svg",
            "ticket_price": 125.00,
            "total_tickets": 1200,
            "available_tickets": 980,
            "status": "active"
        },
        {
            "title": "VentureConnect: Startup Pitch & Angel Gala",
            "slug": "ventureconnect-startup-pitch-angel-gala",
            "category_id": cats.get("business-networking", 3),
            "description": "The premier networking gala connecting early-stage founders with accredited angels, VC partners, and institutional investors. Fast-pitch competitions, cocktail hours, and deal-making lounges.",
            "location": "New York, NY",
            "venue_name": "Manhattan Skyline Ballroom, 42nd Fl",
            "event_date": (now + timedelta(days=28)).strftime("%Y-%m-%d 18:00:00"),
            "banner_image": "business_networking.svg",
            "ticket_price": 175.00,
            "total_tickets": 300,
            "available_tickets": 215,
            "status": "active"
        },
        {
            "title": "Prism Contemporary Art & Light Biennial",
            "slug": "prism-contemporary-art-light-biennial",
            "category_id": cats.get("art-design-culture", 4),
            "description": "Immersive audiovisual installations, spatial sculptures, and interactive digital art by renowned international creators. Includes curator-guided walk-throughs and tactile design workshops.",
            "location": "Chicago, IL",
            "venue_name": "Millennium Contemporary Arts Center",
            "event_date": (now + timedelta(days=35)).strftime("%Y-%m-%d 11:00:00"),
            "banner_image": "art_exhibit.svg",
            "ticket_price": 45.00,
            "total_tickets": 600,
            "available_tickets": 540,
            "status": "active"
        },
        {
            "title": "Coastal Sun Marathon & Wellness Expo",
            "slug": "coastal-sun-marathon-wellness-expo",
            "category_id": cats.get("health-fitness-sports", 5),
            "description": "Scenic 10K, Half-Marathon, and Full-Marathon along the stunning Pacific coast. Finisher medals, athletic recovery zones, sports nutrition expo, and post-race beach festival.",
            "location": "San Diego, CA",
            "venue_name": "Mission Bay Athletic Waterfront",
            "event_date": (now + timedelta(days=42)).strftime("%Y-%m-%d 06:30:00"),
            "banner_image": "marathon.svg",
            "ticket_price": 85.00,
            "total_tickets": 800,
            "available_tickets": 710,
            "status": "active"
        },
        {
            "title": "Epicurean Artisan Food & Wine Fair",
            "slug": "epicurean-artisan-food-wine-fair",
            "category_id": cats.get("food-culinary-arts", 6),
            "description": "Indulge in tastings from 60+ master sommeliers, Michelin-starred guest chefs, and regional artisan bakers. Features live cooking face-offs, pairing workshops, and gourmet market stalls.",
            "location": "Napa Valley, CA",
            "venue_name": "Silverado Vineyard Estates",
            "event_date": (now + timedelta(days=50)).strftime("%Y-%m-%d 12:00:00"),
            "banner_image": "culinary_fair.svg",
            "ticket_price": 110.00,
            "total_tickets": 450,
            "available_tickets": 390,
            "status": "active"
        }
    ]

    print("[EventEase] Seeding Events...")
    event_ids = []
    for ev in events:
        existing = query_db("SELECT id FROM events WHERE slug = %s", (ev['slug'],), one=True)
        if not existing:
            res = query_db(
                """INSERT INTO events 
                   (title, slug, category_id, description, location, venue_name, event_date, 
                    banner_image, ticket_price, total_tickets, available_tickets, status, created_by)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (ev['title'], ev['slug'], ev['category_id'], ev['description'], ev['location'],
                 ev['venue_name'], ev['event_date'], ev['banner_image'], ev['ticket_price'],
                 ev['total_tickets'], ev['available_tickets'], ev['status'], admin_id),
                commit=True
            )
            event_ids.append(res['lastrowid'])
        else:
            event_ids.append(existing['id'])

    # 5. Seed Initial Bookings & Payments for Dashboard Analytics
    print("[EventEase] Seeding Demo Bookings & Payments...")
    if user_ids and event_ids:
        sample_bookings = [
            ("EE-827491", user_ids[0], event_ids[0], 2, 598.00, "confirmed", "credit_card", "TXN-90214819"),
            ("EE-194820", user_ids[1], event_ids[1], 3, 375.00, "confirmed", "credit_card", "TXN-38291044"),
            ("EE-630291", user_ids[2], event_ids[2], 1, 175.00, "confirmed", "paypal", "TXN-17294820"),
            ("EE-449102", user_ids[3], event_ids[3], 4, 180.00, "confirmed", "debit_card", "TXN-55829103"),
            ("EE-918234", user_ids[0], event_ids[4], 1, 85.00, "confirmed", "credit_card", "TXN-77391029")
        ]

        for code, uid, eid, qty, total, status, pay_method, txn_id in sample_bookings:
            b = query_db("SELECT id FROM bookings WHERE booking_code = %s", (code,), one=True)
            if not b:
                res_b = query_db(
                    """INSERT INTO bookings 
                       (booking_code, user_id, event_id, tickets_count, total_amount, booking_status)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (code, uid, eid, qty, total, status),
                    commit=True
                )
                b_id = res_b['lastrowid']
                query_db(
                    """INSERT INTO payments 
                       (transaction_id, booking_id, amount, payment_method, payment_status)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (txn_id, b_id, total, pay_method, "completed"),
                    commit=True
                )

    print("[EventEase] Database seeding completed successfully!")

if __name__ == '__main__':
    seed_database()
