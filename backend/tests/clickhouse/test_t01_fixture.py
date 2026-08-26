def test_fixture_connects(ch):
    assert ch.command("SELECT 1") == 1

def test_fixture_version_pinned(ch):
    assert ch.command("SELECT version()").startswith("26.3.22")

def test_fixture_timezone(ch):
    assert ch.command("SELECT timezone()") == "Asia/Ho_Chi_Minh"
