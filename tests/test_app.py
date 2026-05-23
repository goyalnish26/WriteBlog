import os
import tempfile
import pytest
from app import create_app, db

@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
    })
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()
    os.close(db_fd)
    os.remove(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'All Posts' in response.data

def test_register_and_login_flow(client):
    response = client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password',
    }, follow_redirects=True)
    assert b'Registration successful' in response.data

    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password',
    }, follow_redirects=True)
    assert b'Logged in successfully' in response.data

def test_create_and_view_post(client):
    # Register
    client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password',
    }, follow_redirects=True)
    # Login
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password',
    }, follow_redirects=True)
    
    # Create post
    response = client.post('/create', data={
        'title': 'Test Post Title',
        'content': 'This is some test markdown content.',
        'tags': 'test, markdown',
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Test Post Title' in response.data

    # Test posting with empty thumbnail (simulates browser submit on empty file input)
    import io
    response = client.post('/create', data={
        'title': 'Test Post with Empty Thumbnail',
        'content': 'Content here.',
        'tags': 'tag1',
        'thumbnail': (io.BytesIO(), '')
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Test Post with Empty Thumbnail' in response.data

