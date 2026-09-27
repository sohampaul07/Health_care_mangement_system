import os
import sys
import pytest

# Ensure healthsync_ai is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import User, PHC, Medicine, Alert, Redistribution, FederatedRound

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def authenticated_client(client, app):
    # Log in as the seeded admin
    client.post('/login', data={
        'email': 'admin@healthsync.gov',
        'password': 'admin2026'
    }, follow_redirects=True)
    return client


# 1. Test Login & Logout
def test_login_success(client):
    response = client.post('/login', data={
        'email': 'admin@healthsync.gov',
        'password': 'admin2026'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"National Command Overview" in response.data or b"HEALTHSYNC AI" in response.data

def test_login_invalid_password(client):
    response = client.post('/login', data={
        'email': 'admin@healthsync.gov',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid national officer credentials" in response.data

def test_logout(authenticated_client):
    response = authenticated_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"Authenticate & Enter Command Center" in response.data


# 2. Test Protected Views
def test_unauthenticated_redirect(client):
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_authenticated_dashboard(authenticated_client):
    response = authenticated_client.get('/dashboard')
    assert response.status_code == 200
    assert b"National Command Overview" in response.data
    assert b"12,540" in response.data
    assert b"Resource Risk Index" in response.data

def test_all_pages_render(authenticated_client):
    endpoints = [
        '/phcs', '/medicines', '/patients', '/beds',
        '/staff', '/forecast', '/alerts', '/redistribution',
        '/federated', '/reports'
    ]
    for ep in endpoints:
        res = authenticated_client.get(ep)
        assert res.status_code == 200, f"Failed at endpoint {ep}"


# 3. Test Dashboard API
def test_api_dashboard_stats(authenticated_client):
    response = authenticated_client.get('/api/dashboard/stats')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'kpis' in data
    assert 'risk_index' in data
    assert data['kpis']['phcs_connected'] == "12,540"


# 4. Test PHC API (GET, POST, GET single, DELETE)
def test_api_phcs_crud(authenticated_client):
    # GET list
    get_res = authenticated_client.get('/api/phcs')
    assert get_res.status_code == 200
    data = get_res.get_json()
    assert data['success'] is True
    assert data['count'] >= 20

    # POST new
    post_res = authenticated_client.post('/api/phcs', json={
        'phc_code': 'PHC-999',
        'name': 'Test Rural Health Post',
        'district': 'TestDistrict',
        'state': 'West Bengal',
        'total_beds': 30,
        'occupied_beds': 10,
        'staff_total': 15,
        'staff_present': 14,
        'patients_today': 120,
        'status': 'NORMAL'
    })
    assert post_res.status_code == 201
    new_id = post_res.get_json()['phc']['id']

    # GET single
    single_res = authenticated_client.get(f'/api/phcs/{new_id}')
    assert single_res.status_code == 200
    assert single_res.get_json()['phc']['phc_code'] == 'PHC-999'

    # DELETE
    del_res = authenticated_client.delete(f'/api/phcs/{new_id}')
    assert del_res.status_code == 200
    assert del_res.get_json()['success'] is True


# 5. Test Medicine API (GET, POST, PUT stock, DELETE)
def test_api_medicines_crud(authenticated_client):
    # GET list
    get_res = authenticated_client.get('/api/medicines')
    assert get_res.status_code == 200
    data = get_res.get_json()
    assert data['success'] is True
    assert data['count'] >= 15

    # POST new
    post_res = authenticated_client.post('/api/medicines', json={
        'name': 'Testicillin 500mg',
        'category': 'Antibiotic',
        'current_stock': 600,
        'daily_usage': 40,
        'minimum_stock': 300,
        'unit': 'capsules'
    })
    assert post_res.status_code == 201
    med_id = post_res.get_json()['medicine']['id']

    # PUT stock
    put_res = authenticated_client.put(f'/api/medicines/{med_id}', json={
        'current_stock': 850
    })
    assert put_res.status_code == 200
    assert put_res.get_json()['medicine']['current_stock'] == 850

    # DELETE
    del_res = authenticated_client.delete(f'/api/medicines/{med_id}')
    assert del_res.status_code == 200


# 6. Test Forecast & What-If API
def test_api_forecast(authenticated_client):
    res = authenticated_client.get('/api/forecast')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert len(data['forecasts']) >= 15

def test_api_what_if_simulation(authenticated_client):
    res = authenticated_client.post('/api/forecast/what-if', json={
        'demand_increase': 30.0
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    sim = data['simulation']
    assert sim['demand_increase_pct'] == 30.0
    assert sim['simulated_bed_occupancy'] > 84.2
    assert sim['simulated_alert_count'] > 126


# 7. Test Alerts API & Resolution
def test_api_alerts_and_resolve(authenticated_client):
    get_res = authenticated_client.get('/api/alerts')
    assert get_res.status_code == 200
    data = get_res.get_json()
    assert data['count'] >= 5
    first_id = data['alerts'][0]['id']

    # Resolve
    resolve_res = authenticated_client.post(f'/api/alerts/{first_id}/resolve')
    assert resolve_res.status_code == 200
    assert resolve_res.get_json()['alert']['status'] == 'RESOLVED'


# 8. Test Redistribution API & Approval
def test_api_redistribution(authenticated_client):
    get_res = authenticated_client.get('/api/redistribution?status=PENDING')
    assert get_res.status_code == 200
    proposals = get_res.get_json()['proposals']
    assert len(proposals) > 0
    target_id = proposals[0]['id']

    # Approve
    app_res = authenticated_client.post(f'/api/redistribution/{target_id}/approve')
    assert app_res.status_code == 200
    assert app_res.get_json()['proposal']['status'] == 'APPROVED'


# 9. Test Federated AI API
def test_api_federated(authenticated_client):
    get_res = authenticated_client.get('/api/federated')
    assert get_res.status_code == 200
    data = get_res.get_json()['federated_state']
    assert data['participating_nodes_count'] == 5
    assert len(data['brics_nodes']) == 5

    # Run federated round
    post_res = authenticated_client.post('/api/federated/run')
    assert post_res.status_code == 200
    result = post_res.get_json()
    assert result['success'] is True
    assert result['details']['round_number'] >= 5
    assert result['details']['accuracy'] >= 92.5


# 10. Test Reports CSV Export
def test_api_reports_csv_export(authenticated_client):
    res = authenticated_client.get('/api/reports/export-csv?type=audit')
    assert res.status_code == 200
    assert res.mimetype == 'text/csv'
    assert 'attachment;filename=healthsync_audit_log' in res.headers['Content-Disposition']
