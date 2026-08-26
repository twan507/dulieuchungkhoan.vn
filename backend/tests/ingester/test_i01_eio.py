import json

from ingester.eio import Ack, Control, Event, Open, build_subscribe, chunk, parse_packet


def test_parse_open():
    p = parse_packet('0{"sid":"abc","upgrades":[],"pingInterval":25000,"pingTimeout":60000}')
    assert p == Open(25000, 60000)


def test_parse_controls():
    assert parse_packet("40") == Control("40")
    assert parse_packet("3") == Control("3")


def test_parse_event_t():
    raw = ('42["t",{"TD":"10/08/2026","FT":"13:08:56","SB":"ACV","FV":"100","LC":"S",'
           '"FMP":"42100.0","FCV":"1000.0","SM":"74027","AVO":"590000","AVA":"24983210000.0"}]')
    p = parse_packet(raw)
    assert isinstance(p, Event) and p.name == "t" and p.payload["SB"] == "ACV"


def test_parse_ack():
    p = parse_packet('431[{"body":{"result":[]},"statusCode":200}]')
    assert isinstance(p, Ack) and p.ack_id == 1


def test_parse_garbage_returns_none():
    assert parse_packet("42tào lao") is None
    assert parse_packet("9xyz") is None


def test_build_subscribe_matches_sails_envelope():
    s = build_subscribe(1, ["i:BID", "o10:BID"])
    assert s.startswith("421[")
    body = json.loads(s[3:])
    assert body[0] == "get"
    assert body[1]["url"] == "/client/subscribe"
    assert body[1]["data"] == {"op": "subscribe", "args": ["i:BID", "o10:BID"]}


def test_chunk():
    assert list(chunk(list(range(5)), 2)) == [[0, 1], [2, 3], [4]]
