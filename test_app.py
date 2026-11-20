import unittest
from app import app
from database import query_db, init_db

class EventEaseTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_homepage_renders(self):
        """Test landing page renders successfully with events and categories"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'EventEase', response.data)
        self.assertIn(b'Discover, Book', response.data)

    def test_02_events_catalog_and_filter(self):
        """Test event catalog listing and category filtering"""
        response = self.client.get('/events')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Events Catalog', response.data)

        # Test filter by category
        res_cat = self.client.get('/events?category=technology-innovation')
        self.assertEqual(res_cat.status_code, 200)

        # Test search
        res_search = self.client.get('/events?q=Summit')
        self.assertEqual(res_search.status_code, 200)

    def test_03_event_details(self):
        """Test single event details view"""
        event = query_db("SELECT slug FROM events LIMIT 1", one=True)
        self.assertIsNotNone(event)
        response = self.client.get(f"/events/{event['slug']}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Reserve Your Pass', response.data)

    def test_04_user_authentication_flow(self):
        """Test user login and profile access"""
        # Test valid login
        res_login = self.client.post('/login', data={
            'email': 'john.doe@example.com',
            'password': 'User@123'
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b'Welcome back', res_login.data)

        # Access profile
        res_prof = self.client.get('/profile')
        self.assertEqual(res_prof.status_code, 200)
        self.assertIn(b'My Event Registrations', res_prof.data)

        # Logout
        res_logout = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(res_logout.status_code, 200)

    def test_05_booking_and_cancellation_flow(self):
        """Test complete booking cycle with ticket inventory decrement and refund"""
        # 1. Login user
        self.client.post('/login', data={
            'email': 'john.doe@example.com',
            'password': 'User@123'
        })

        # 2. Pick an active event
        event = query_db("SELECT id, slug, available_tickets FROM events WHERE status = 'active' AND available_tickets > 5 LIMIT 1", one=True)
        self.assertIsNotNone(event)
        orig_tickets = event['available_tickets']

        # 3. Process booking for 2 tickets
        res_book = self.client.post(f"/booking/process/{event['slug']}", data={
            'quantity': 2,
            'payment_method': 'credit_card'
        }, follow_redirects=True)
        self.assertEqual(res_book.status_code, 200)
        self.assertIn(b"You're Going!", res_book.data)

        # Verify tickets decremented by 2
        updated_event = query_db("SELECT available_tickets FROM events WHERE id = %s", (event['id'],), one=True)
        self.assertEqual(updated_event['available_tickets'], orig_tickets - 2)

        # 4. Get the latest booking code created
        latest_b = query_db("SELECT booking_code FROM bookings WHERE user_id = (SELECT id FROM users WHERE email = 'john.doe@example.com') ORDER BY id DESC LIMIT 1", one=True)
        b_code = latest_b['booking_code']

        # 5. Cancel the booking
        res_cancel = self.client.post(f"/booking/cancel/{b_code}", follow_redirects=True)
        self.assertEqual(res_cancel.status_code, 200)

        # Verify tickets returned to inventory
        restocked_event = query_db("SELECT available_tickets FROM events WHERE id = %s", (event['id'],), one=True)
        self.assertEqual(restocked_event['available_tickets'], orig_tickets)

    def test_06_admin_dashboard_and_crud(self):
        """Test admin authentication, dashboard metrics, and event creation/deletion"""
        # 1. Admin login
        res_admin_login = self.client.post('/admin/login', data={
            'username': 'admin',
            'password': 'Admin@123'
        }, follow_redirects=True)
        self.assertEqual(res_admin_login.status_code, 200)
        self.assertIn(b'Dashboard Overview', res_admin_login.data)

        # 2. Access Admin Events
        res_events = self.client.get('/admin/events')
        self.assertEqual(res_events.status_code, 200)

        # 3. Create a new event
        res_create = self.client.post('/admin/events/new', data={
            'title': 'Automated Test Hackathon 2026',
            'category_id': 1,
            'description': 'Test event created during automated test execution.',
            'venue_name': 'Dev Center',
            'location': 'Seattle, WA',
            'event_date': '2026-12-15T10:00',
            'banner_image': 'tech_summit.svg',
            'ticket_price': '49.99',
            'total_tickets': '150',
            'status': 'active'
        }, follow_redirects=True)
        self.assertEqual(res_create.status_code, 200)
        self.assertIn(b'published successfully', res_create.data)

        # Verify in DB
        created_ev = query_db("SELECT id, title FROM events WHERE title = 'Automated Test Hackathon 2026'", one=True)
        self.assertIsNotNone(created_ev)

        # 4. Delete the test event
        res_del = self.client.post(f"/admin/events/{created_ev['id']}/delete", follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)
        self.assertIn(b'permanently removed', res_del.data)

        # 5. Check Reports
        res_reports = self.client.get('/admin/reports')
        self.assertEqual(res_reports.status_code, 200)
        self.assertIn(b'Executive Performance Summary', res_reports.data)

if __name__ == '__main__':
    unittest.main()
