from __future__ import annotations

from requests.cookies import RequestsCookieJar
import json


def serialize_token(cookies: RequestsCookieJar, compressed: bool = False) -> str:
    """
    将 Cookie 集合序列化为 JSON 字符串，可选地进行压缩编码。

    :param cookies: 需要序列化的 Cookie 集合。
    :type cookies: RequestsCookieJar
    :param compressed: 指示是否对序列化结果执行压缩编码。
    :type compressed: bool
    :return: 序列化后的令牌字符串，若压缩则为 Base64 编码。
    :rtype: str
    """
    cookies_list = [
        {
            "key": cookie.name,
            "value": cookie.value,
            "host": cookie.domain,
            "path": cookie.path,
        }
        for cookie in cookies
    ]
    serialized_token = json.dumps(cookies_list)
    if compressed:
        import base64
        import bz2

        serialized_token = bz2.compress(serialized_token.encode("utf-8"))
        serialized_token = base64.urlsafe_b64encode(serialized_token).decode("utf-8")
    return serialized_token


def deserialize_token(token: str, compressed: bool = False) -> RequestsCookieJar:
    """
    将序列化令牌解析回 Cookie 集合，支持自动解压缩。

    :param token: 通过 serialize_token 生成的令牌字符串。
    :type token: str
    :param compressed: 指示令牌是否经过压缩编码。
    :type compressed: bool
    :return: 还原后的 Cookie 集合，可直接用于请求会话。
    :rtype: RequestsCookieJar
    """
    if compressed:
        import base64
        import bz2

        token = base64.urlsafe_b64decode(token.encode("utf-8"))
        token = bz2.decompress(token).decode("utf-8")
    cookies_list = json.loads(token)
    cookies = RequestsCookieJar()
    for cookie_dict in cookies_list:
        cookies.set(
            name=cookie_dict["key"],
            value=cookie_dict["value"],
            domain=cookie_dict["host"],
            path=cookie_dict["path"],
        )
    return cookies
