from nowcoder_mcp.client import NowcoderClient


def test_parse_visible_discuss_comments_from_html():
    html = """
    <html><body>
      <div class="comment-item" data-comment-id="42">
        <span class="name">Alice</span><p>感谢分享</p>
      </div>
    </body></html>
    """

    comments = NowcoderClient._parse_comments_from_html(html)

    assert len(comments) == 1
    assert comments[0].comment_id == "42"
    assert "感谢分享" in comments[0].content


def test_parse_user_public_profile_from_html():
    html = """
    <html><head>
      <title>牛客用户 - 牛客网</title>
      <meta name="description" content="公开资料">
    </head><body><div class="profile-user-name">求职同学</div></body></html>
    """

    profile = NowcoderClient._parse_user_public_profile("123", "https://www.nowcoder.com/users/123", html)

    assert profile.user_id == "123"
    assert profile.nickname == "求职同学"
    assert profile.raw["description"] == "公开资料"
