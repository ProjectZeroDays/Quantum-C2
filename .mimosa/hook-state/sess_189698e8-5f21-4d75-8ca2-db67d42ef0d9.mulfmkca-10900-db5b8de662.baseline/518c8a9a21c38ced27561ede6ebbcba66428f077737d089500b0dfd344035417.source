"""test_camwar — vendor_from_str + RTSP response-head parsing."""
import quantum_cli as q


def test_vendor_from_str_hikvision():
    assert q.vendor_from_str("Hikvision DS-2CD2135") == "hikvision"
    assert q.vendor_from_str("Server:embedded_net_dvr") == "hikvision"
    assert q.vendor_from_str("hik-webComponents") == "hikvision"


def test_vendor_from_str_dahua():
    assert q.vendor_from_str("Dahua DVR login_module.js") == "dahua"


def test_vendor_from_str_axis():
    assert q.vendor_from_str("AXIS P3245 axis-cgi") == "axis"


def test_vendor_from_str_foscam():
    assert q.vendor_from_str("Foscam ipcam cgi-bin/hi3510") == "foscam"


def test_vendor_from_str_tplink():
    assert q.vendor_from_str("Tapo C200 tplink") == "tplink"


def test_vendor_from_str_unknown():
    assert q.vendor_from_str("some random webserver") == "unknown"
    assert q.vendor_from_str("") == "unknown"
    assert q.vendor_from_str(None) == "unknown"


def test_parse_rtsp_header_status_line():
    raw = ("RTSP/1.0 401 Unauthorized\r\n"
           "CSeq: 1\r\n"
           "WWW-Authenticate: Digest realm=\"IP Camera(12345)\"\r\n\r\n")
    head = q.parse_rtsp_header(raw)
    assert head["status"] == 401
    assert head["headers"]["cseq"] == "1"
    assert "ip camera" in head["headers"]["www-authenticate"].lower()


def test_parse_rtsp_header_ok():
    raw = "RTSP/1.0 200 OK\r\nCSeq: 2\r\nPublic: OPTIONS, DESCRIBE\r\n\r\n"
    head = q.parse_rtsp_header(raw)
    assert head["status"] == 200
    assert "DESCRIBE" in head["headers"]["public"]


def test_parse_rtsp_header_bytes_and_garbage():
    head = q.parse_rtsp_header(b"RTSP/1.0 200 OK\r\nServer: vivotek\r\n\r\n")
    assert head["status"] == 200
    assert head["headers"]["server"] == "vivotek"
    empty = q.parse_rtsp_header("")
    assert empty["status"] is None
    assert empty["headers"] == {}


def test_camwar_engine_class_attrs():
    assert 554 in q.CamWarEngine.CAM_PORTS
    assert "hikvision" in q.CamWarEngine.CREDS
    assert callable(q.CamWarEngine._vendor_from_str)
