def test_homepage(client):
    """Sprawdza, czy strona główna działa"""
    response = client.get('/')
    assert response.status_code == 200
    assert "Akademia Korepetycji" in response.get_data(as_text=True)