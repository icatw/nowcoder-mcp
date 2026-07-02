from nowcoder_mcp.client import NowcoderClient


def test_parse_current_user_from_logged_in_profile():
    html = '{"rawNickname":"鹿满川","nickname":"鹿满川"}'

    user = NowcoderClient._parse_current_user("https://www.nowcoder.com/users/376305945", html)

    assert user.authenticated is True
    assert user.user_id == "376305945"
    assert user.nickname == "鹿满川"
    assert user.profile_url == "https://www.nowcoder.com/users/376305945"
    assert "cookie" not in user.model_dump_json().lower()


def test_parse_current_user_login_page_is_unauthenticated():
    user = NowcoderClient._parse_current_user("https://www.nowcoder.com/login?callBack=%2Fprofile", "")

    assert user.authenticated is False
    assert user.user_id is None
    assert user.nickname is None
