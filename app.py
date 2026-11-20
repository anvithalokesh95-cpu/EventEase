import os
import re
import secrets
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, g, abort, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from database import query_db, init_db, db_manager

app = Flask(__name__)
app.config.from_object(Config)

# Ensure tables are initialized on startup
with app.app_context():
    init_db()


# -------------------------------------------------------------
# Context Processors & Template Helpers
# -------------------------------------------------------------
@app.context_processor
def inject_global_data():
    return {
        'db_type': db_manager.db_type,
        'current_year': datetime.now().year
    }


# -------------------------------------------------------------
# Authentication & Authorization Decorators
# -------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_id'):
            flash('Administrator authentication required.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# -------------------------------------------------------------
# Client / Public Routes
# -------------------------------------------------------------
@app.route('/')
def index():
    categories = query_db("SELECT * FROM categories ORDER BY name ASC")
    events = query_db("""
        SELECT e.*, c.name AS category_name, c.slug AS category_slug 
        FROM events e 
        JOIN categories c ON e.category_id = c.id 
        WHERE e.status = 'active'
        ORDER BY e.event_date ASC 
        LIMIT 6
    """)
    return render_template('index.html', categories=categories, events=events)


@app.route('/events')
def events():
    search_query = request.args.get('q', '').strip()
    category_slug = request.args.get('category', '').strip()

    categories = query_db("SELECT * FROM categories ORDER BY name ASC")
    
    sql = """
        SELECT e.*, c.name AS category_name, c.slug AS category_slug, c.icon AS category_icon
        FROM events e 
        JOIN categories c ON e.category_id = c.id 
        WHERE 1=1
    """
    params = []

    if category_slug and category_slug != 'all':
        sql += " AND c.slug = %s"
        params.append(category_slug)

    if search_query:
        sql += " AND (e.title LIKE %s OR e.description LIKE %s OR e.location LIKE %s OR e.venue_name LIKE %s)"
        like_term = f"%{search_query}%"
        params.extend([like_term, like_term, like_term, like_term])

    sql += " ORDER BY e.event_date ASC"

    all_events = query_db(sql, tuple(params))
    return render_template(
        'events.html', 
        events=all_events, 
        categories=categories, 
        current_category=category_slug,
        current_search=search_query
    )


@app.route('/events/<slug>')
def event_details(slug):
    event = query_db("""
        SELECT e.*, c.name AS category_name, c.slug AS category_slug, c.icon AS category_icon
        FROM events e 
        JOIN categories c ON e.category_id = c.id 
        WHERE e.slug = %s
    """, (slug,), one=True)

    if not event:
        flash('Event not found or has been removed.', 'danger')
        return redirect(url_for('events'))

    return render_template('event_details.html', event=event)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Flash positive confirmation
        flash(f'Thank you, {name}! Your inquiry regarding "{subject}" has been received. Our team will contact {email} shortly.', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')


# -------------------------------------------------------------
# User Authentication Routes
# -------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('profile'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()

        if not full_name or not email or not password:
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('register'))

        existing_user = query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)
        if existing_user:
            flash('An account with this email address already exists. Please log in.', 'warning')
            return redirect(url_for('login'))

        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        result = query_db(
            "INSERT INTO users (full_name, email, password_hash, phone) VALUES (%s, %s, %s, %s)",
            (full_name, email, password_hash, phone),
            commit=True
        )

        session['user_id'] = result['lastrowid']
        session['user_name'] = full_name
        session['user_email'] = email
        flash('Welcome to EventEase! Your account has been created successfully.', 'success')
        return redirect(url_for('profile'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('profile'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = query_db("SELECT * FROM users WHERE email = %s", (email,), one=True)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['user_email'] = user['email']
            flash(f"Welcome back, {user['full_name']}!", 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('profile'))
        else:
            flash('Invalid email address or password. Please try again.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    flash('You have been signed out safely.', 'info')
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    user = query_db("SELECT * FROM users WHERE id = %s", (session['user_id'],), one=True)
    bookings = query_db("""
        SELECT b.*, e.title AS event_title, e.slug AS event_slug, e.event_date, 
               e.banner_image, e.venue_name, e.location
        FROM bookings b
        JOIN events e ON b.event_id = e.id
        WHERE b.user_id = %s
        ORDER BY b.booking_date DESC
    """, (session['user_id'],))
    
    return render_template('profile.html', user=user, bookings=bookings)


@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()

    if full_name:
        query_db(
            "UPDATE users SET full_name = %s, phone = %s WHERE id = %s",
            (full_name, phone, session['user_id']),
            commit=True
        )
        session['user_name'] = full_name
        flash('Your profile information has been updated.', 'success')

    return redirect(url_for('profile'))


# -------------------------------------------------------------
# Booking Management & Checkout Routes
# -------------------------------------------------------------
@app.route('/booking/checkout/<slug>', methods=['GET'])
@login_required
def booking_checkout(slug):
    event = query_db("""
        SELECT e.*, c.name AS category_name 
        FROM events e 
        JOIN categories c ON e.category_id = c.id 
        WHERE e.slug = %s
    """, (slug,), one=True)

    if not event or event['status'] != 'active':
        flash('This event is currently unavailable for booking.', 'danger')
        return redirect(url_for('events'))

    if event['available_tickets'] <= 0:
        flash('Sorry, this event is already sold out.', 'warning')
        return redirect(url_for('event_details', slug=slug))

    quantity = int(request.args.get('quantity', 1))
    quantity = max(1, min(quantity, min(event['available_tickets'], 10)))

    user = query_db("SELECT * FROM users WHERE id = %s", (session['user_id'],), one=True)

    return render_template('booking.html', event=event, user=user, quantity=quantity)


@app.route('/booking/process/<slug>', methods=['POST'])
@login_required
def process_booking(slug):
    event = query_db("SELECT * FROM events WHERE slug = %s", (slug,), one=True)
    if not event or event['status'] != 'active':
        flash('Event is unavailable.', 'danger')
        return redirect(url_for('events'))

    try:
        quantity = int(request.form.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1

    if quantity < 1:
        flash('Invalid ticket quantity.', 'error')
        return redirect(url_for('booking_checkout', slug=slug))

    # Atomic inventory availability check
    if event['available_tickets'] < quantity:
        flash(f"Only {event['available_tickets']} ticket(s) remain for this event.", 'warning')
        return redirect(url_for('booking_checkout', slug=slug))

    # Calculate total amount
    total_amount = float(event['ticket_price']) * quantity
    payment_method = request.form.get('payment_method', 'credit_card')

    # Generate unique alphanumeric booking reference
    booking_code = f"EE-{secrets.token_hex(3).upper()}"
    while query_db("SELECT id FROM bookings WHERE booking_code = %s", (booking_code,), one=True):
        booking_code = f"EE-{secrets.token_hex(3).upper()}"

    transaction_id = f"TXN-{secrets.token_hex(6).upper()}"

    try:
        # 1. Decrement available ticket inventory
        query_db(
            "UPDATE events SET available_tickets = available_tickets - %s WHERE id = %s",
            (quantity, event['id']),
            commit=True
        )

        # 2. Insert booking record
        res_booking = query_db(
            """INSERT INTO bookings 
               (booking_code, user_id, event_id, tickets_count, total_amount, booking_status) 
               VALUES (%s, %s, %s, %s, %s, 'confirmed')""",
            (booking_code, session['user_id'], event['id'], quantity, total_amount),
            commit=True
        )
        booking_id = res_booking['lastrowid']

        # 3. Record simulated payment transaction
        query_db(
            """INSERT INTO payments 
               (transaction_id, booking_id, amount, payment_method, payment_status) 
               VALUES (%s, %s, %s, %s, 'completed')""",
            (transaction_id, booking_id, total_amount, payment_method),
            commit=True
        )

        flash('Your tickets have been reserved and confirmed successfully!', 'success')
        return redirect(url_for('booking_confirmation', code=booking_code))

    except Exception as e:
        flash(f'An error occurred while confirming your reservation: {str(e)}', 'danger')
        return redirect(url_for('event_details', slug=slug))


@app.route('/booking/confirmation/<code>')
def booking_confirmation(code):
    booking = query_db("""
        SELECT b.*, e.title AS event_title, e.event_date, e.venue_name, e.location,
               u.full_name AS user_name, u.email AS user_email,
               p.transaction_id, p.payment_method
        FROM bookings b
        JOIN events e ON b.event_id = e.id
        JOIN users u ON b.user_id = u.id
        LEFT JOIN payments p ON p.booking_id = b.id
        WHERE b.booking_code = %s
    """, (code,), one=True)

    if not booking:
        flash('Booking reference code not found.', 'danger')
        return redirect(url_for('index'))

    return render_template('booking_success.html', booking=booking)


@app.route('/booking/cancel/<code>', methods=['POST'])
@login_required
def cancel_booking(code):
    booking = query_db(
        "SELECT * FROM bookings WHERE booking_code = %s AND user_id = %s", 
        (code, session['user_id']), 
        one=True
    )

    if not booking:
        flash('Booking not found or access denied.', 'danger')
        return redirect(url_for('profile'))

    if booking['booking_status'] == 'cancelled':
        flash('This booking is already cancelled.', 'info')
        return redirect(url_for('profile'))

    # Update booking status to cancelled
    query_db(
        "UPDATE bookings SET booking_status = 'cancelled', cancellation_date = CURRENT_TIMESTAMP WHERE id = %s",
        (booking['id'],),
        commit=True
    )

    # Return tickets back to event available inventory!
    query_db(
        "UPDATE events SET available_tickets = available_tickets + %s WHERE id = %s",
        (booking['tickets_count'], booking['event_id']),
        commit=True
    )

    # Update payment status
    query_db(
        "UPDATE payments SET payment_status = 'refunded' WHERE booking_id = %s",
        (booking['id'],),
        commit=True
    )

    flash(f"Booking {booking['booking_code']} has been cancelled. {booking['tickets_count']} ticket(s) released.", 'success')
    return redirect(url_for('profile'))


# -------------------------------------------------------------
# Admin Dashboard & Management Routes
# -------------------------------------------------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_id'):
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        admin = query_db(
            "SELECT * FROM admins WHERE username = %s OR email = %s", 
            (username, username), 
            one=True
        )

        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_id'] = admin['id']
            session['admin_name'] = admin['full_name']
            session['admin_user'] = admin['username']
            session['admin_role'] = admin['role']
            flash(f"Welcome to Admin Console, {admin['full_name']}!", 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid administrator credentials.', 'danger')

    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    session.pop('admin_user', None)
    session.pop('admin_role', None)
    flash('Admin console closed safely.', 'info')
    return redirect(url_for('admin_login'))


@app.route('/admin')
@admin_required
def admin_dashboard():
    # Metrics
    tot_events = query_db("SELECT COUNT(*) AS count FROM events WHERE status = 'active'", one=True)['count']
    tot_bookings = query_db("SELECT COUNT(*) AS count FROM bookings", one=True)['count']
    tot_users = query_db("SELECT COUNT(*) AS count FROM users", one=True)['count']
    
    rev_row = query_db("SELECT SUM(total_amount) AS rev FROM bookings WHERE booking_status = 'confirmed'", one=True)
    tot_revenue = float(rev_row['rev']) if rev_row and rev_row['rev'] else 0.0

    stats = {
        'total_events': tot_events,
        'total_bookings': tot_bookings,
        'total_users': tot_users,
        'total_revenue': tot_revenue
    }

    # Recent bookings
    recent_bookings = query_db("""
        SELECT b.*, e.title AS event_title, u.full_name AS user_name, u.email AS user_email
        FROM bookings b
        JOIN events e ON b.event_id = e.id
        JOIN users u ON b.user_id = u.id
        ORDER BY b.booking_date DESC
        LIMIT 6
    """)

    # Low capacity watchlist
    low_capacity_events = query_db("""
        SELECT * FROM events 
        WHERE status = 'active' AND available_tickets < 100 
        ORDER BY available_tickets ASC 
        LIMIT 4
    """)

    return render_template(
        'admin/dashboard.html', 
        stats=stats, 
        recent_bookings=recent_bookings,
        low_capacity_events=low_capacity_events
    )


@app.route('/admin/events')
@admin_required
def admin_events():
    events_list = query_db("""
        SELECT e.*, c.name AS category_name 
        FROM events e 
        JOIN categories c ON e.category_id = c.id 
        ORDER BY e.created_at DESC
    """)
    return render_template('admin/events.html', events=events_list)


@app.route('/admin/events/new', methods=['GET', 'POST'])
@admin_required
def admin_event_new():
    categories = query_db("SELECT * FROM categories ORDER BY name ASC")

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category_id = request.form.get('category_id')
        description = request.form.get('description', '').strip()
        venue_name = request.form.get('venue_name', '').strip()
        location = request.form.get('location', '').strip()
        event_date_str = request.form.get('event_date')
        banner_image = request.form.get('banner_image', 'tech_summit.svg')
        ticket_price = float(request.form.get('ticket_price', 0.0))
        total_tickets = int(request.form.get('total_tickets', 100))
        status = request.form.get('status', 'active')

        # Generate slug
        base_slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
        slug = base_slug
        counter = 1
        while query_db("SELECT id FROM events WHERE slug = %s", (slug,), one=True):
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Format datetime
        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M')
        except Exception:
            event_date = datetime.now() + timedelta(days=14)

        query_db(
            """INSERT INTO events 
               (title, slug, category_id, description, location, venue_name, event_date,
                banner_image, ticket_price, total_tickets, available_tickets, status, created_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (title, slug, category_id, description, location, venue_name, event_date,
             banner_image, ticket_price, total_tickets, total_tickets, status, session['admin_id']),
            commit=True
        )

        flash(f'Event "{title}" published successfully!', 'success')
        return redirect(url_for('admin_events'))

    return render_template('admin/event_form.html', categories=categories, event=None)


@app.route('/admin/events/<int:event_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_event_edit(event_id):
    event = query_db("SELECT * FROM events WHERE id = %s", (event_id,), one=True)
    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('admin_events'))

    categories = query_db("SELECT * FROM categories ORDER BY name ASC")

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category_id = request.form.get('category_id')
        description = request.form.get('description', '').strip()
        venue_name = request.form.get('venue_name', '').strip()
        location = request.form.get('location', '').strip()
        event_date_str = request.form.get('event_date')
        banner_image = request.form.get('banner_image', event['banner_image'])
        ticket_price = float(request.form.get('ticket_price', 0.0))
        new_total_tickets = int(request.form.get('total_tickets', event['total_tickets']))
        status = request.form.get('status', 'active')

        # Adjust available tickets difference
        diff = new_total_tickets - event['total_tickets']
        new_available = max(0, event['available_tickets'] + diff)

        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M')
        except Exception:
            event_date = event['event_date']

        query_db(
            """UPDATE events 
               SET title = %s, category_id = %s, description = %s, location = %s,
                   venue_name = %s, event_date = %s, banner_image = %s, ticket_price = %s,
                   total_tickets = %s, available_tickets = %s, status = %s
               WHERE id = %s""",
            (title, category_id, description, location, venue_name, event_date,
             banner_image, ticket_price, new_total_tickets, new_available, status, event_id),
            commit=True
        )

        flash(f'Event "{title}" updated successfully!', 'success')
        return redirect(url_for('admin_events'))

    # Format date for datetime-local input
    formatted_date = ""
    if event['event_date']:
        if isinstance(event['event_date'], datetime):
            formatted_date = event['event_date'].strftime('%Y-%m-%dT%H:%M')
        else:
            try:
                dt = datetime.strptime(str(event['event_date'])[:19], '%Y-%m-%d %H:%M:%S')
                formatted_date = dt.strftime('%Y-%m-%dT%H:%M')
            except Exception:
                formatted_date = str(event['event_date'])[:16]

    return render_template(
        'admin/event_form.html', 
        categories=categories, 
        event=event, 
        formatted_date=formatted_date
    )


@app.route('/admin/events/<int:event_id>/delete', methods=['POST'])
@admin_required
def admin_event_delete(event_id):
    event = query_db("SELECT * FROM events WHERE id = %s", (event_id,), one=True)
    if event:
        # Check if active bookings exist
        bookings = query_db("SELECT COUNT(*) AS count FROM bookings WHERE event_id = %s AND booking_status = 'confirmed'", (event_id,), one=True)
        if bookings and bookings['count'] > 0:
            # Set to cancelled instead of deleting foreign-key referenced event
            query_db("UPDATE events SET status = 'cancelled' WHERE id = %s", (event_id,), commit=True)
            flash(f'Event "{event["title"]}" has active bookings, so its status was marked as Cancelled.', 'warning')
        else:
            # Safe to delete bookings and event
            query_db("DELETE FROM bookings WHERE event_id = %s", (event_id,), commit=True)
            query_db("DELETE FROM events WHERE id = %s", (event_id,), commit=True)
            flash(f'Event "{event["title"]}" has been permanently removed.', 'success')

    return redirect(url_for('admin_events'))


@app.route('/admin/bookings')
@admin_required
def admin_bookings():
    all_bookings = query_db("""
        SELECT b.*, e.title AS event_title, u.full_name AS user_name, 
               u.email AS user_email, u.phone AS user_phone,
               p.payment_method, p.payment_status
        FROM bookings b
        JOIN events e ON b.event_id = e.id
        JOIN users u ON b.user_id = u.id
        LEFT JOIN payments p ON p.booking_id = b.id
        ORDER BY b.booking_date DESC
    """)
    return render_template('admin/bookings.html', bookings=all_bookings)


@app.route('/admin/bookings/<int:booking_id>/cancel', methods=['POST'])
@admin_required
def admin_booking_cancel(booking_id):
    booking = query_db("SELECT * FROM bookings WHERE id = %s", (booking_id,), one=True)
    if booking and booking['booking_status'] == 'confirmed':
        query_db("UPDATE bookings SET booking_status = 'cancelled' WHERE id = %s", (booking_id,), commit=True)
        query_db("UPDATE events SET available_tickets = available_tickets + %s WHERE id = %s", (booking['tickets_count'], booking['event_id']), commit=True)
        query_db("UPDATE payments SET payment_status = 'refunded' WHERE booking_id = %s", (booking_id,), commit=True)
        flash(f"Booking {booking['booking_code']} cancelled and {booking['tickets_count']} ticket(s) refunded.", 'success')

    return redirect(url_for('admin_bookings'))


@app.route('/admin/users')
@admin_required
def admin_users():
    users_list = query_db("""
        SELECT u.*, 
               COUNT(b.id) AS booking_count, 
               COALESCE(SUM(b.total_amount), 0) AS total_spend
        FROM users u
        LEFT JOIN bookings b ON u.id = b.user_id AND b.booking_status = 'confirmed'
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """)
    return render_template('admin/users.html', users=users_list)


@app.route('/admin/reports')
@admin_required
def admin_reports():
    rev_row = query_db("SELECT SUM(total_amount) AS rev FROM bookings WHERE booking_status = 'confirmed'", one=True)
    total_revenue = float(rev_row['rev']) if rev_row and rev_row['rev'] else 0.0

    tix_row = query_db("SELECT SUM(tickets_count) AS tix FROM bookings WHERE booking_status = 'confirmed'", one=True)
    total_tickets_sold = int(tix_row['tix']) if tix_row and tix_row['tix'] else 0

    tot_bookings = query_db("SELECT COUNT(*) AS count FROM bookings WHERE booking_status = 'confirmed'", one=True)['count']
    avg_order_value = (total_revenue / tot_bookings) if tot_bookings > 0 else 0.0

    cap_row = query_db("SELECT SUM(total_tickets) AS cap FROM events WHERE status != 'cancelled'", one=True)
    total_capacity = int(cap_row['cap']) if cap_row and cap_row['cap'] else 1
    sell_through_rate = round((total_tickets_sold / total_capacity) * 100, 1)

    # Category Breakdown
    category_stats = query_db("""
        SELECT c.name, 
               COUNT(DISTINCT e.id) AS event_count, 
               COALESCE(SUM(b.tickets_count), 0) AS tickets_sold,
               COALESCE(SUM(b.total_amount), 0) AS revenue
        FROM categories c
        LEFT JOIN events e ON c.id = e.category_id
        LEFT JOIN bookings b ON e.id = b.event_id AND b.booking_status = 'confirmed'
        GROUP BY c.id
        ORDER BY revenue DESC
    """)

    # Ranking
    event_rankings = query_db("""
        SELECT * FROM events 
        ORDER BY (total_tickets - available_tickets) DESC
    """)

    return render_template(
        'admin/reports.html',
        total_revenue=total_revenue,
        total_tickets_sold=total_tickets_sold,
        avg_order_value=avg_order_value,
        sell_through_rate=sell_through_rate,
        category_stats=category_stats,
        event_rankings=event_rankings
    )


# -------------------------------------------------------------
# Standalone Execution Runner
# -------------------------------------------------------------
if __name__ == '__main__':
    # Default local dev port 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
