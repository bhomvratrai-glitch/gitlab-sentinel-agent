from app import calculate_checksum, get_user_query

def test_calculate_checksum():
    assert calculate_checksum(2) == 84
    assert calculate_checksum(0) == 0

def test_get_user_query():
    q = get_user_query(10)
    assert "WHERE id = 10" in q
