def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["message"] == "Hello, FastAPI! This app is Live!"

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "app" in body

def test_experiments_tests(client):
    r = client.get("/api/experiments/tests")
    assert r.status_code == 200
    body = r.json()
    assert "tests" in body


def test_db_health(client):
    r = client.get("/api/db/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ok", "error")
    assert "database" in body


def test_ab_tests(client):
    r = client.get("/api/ab/tests")
    assert r.status_code == 200
    body = r.json()
    assert "tests" in body


def test_ab_variant(client):
    r = client.get("/api/ab/variant/onboarding_gym_prompt", params={"userId": "u1"})
    assert r.status_code == 200
    body = r.json()
    assert body["testId"] == "onboarding_gym_prompt"
    assert body["userId"] == "u1"
    assert "variant" in body


def test_event_log(client):
    r = client.post("/api/events", json={"name": "conversion", "userId": "u1", "testId": "onboarding_gym_prompt"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "id" in body

def test_posts_like_requires_firestore(client):
    r = client.post("/api/posts/test-post/like", json={"userId": "u1"})
    assert r.status_code in (200, 503)

def test_gyms_join_requires_firestore(client):
    r = client.post("/api/gyms/test-gym/join", json={"userId": "u1"})
    assert r.status_code in (200, 503)

def test_experiments_results_requires_firestore(client):
    r = client.get("/api/experiments/results/onboarding_gym_prompt")
    assert r.status_code in (200, 503)