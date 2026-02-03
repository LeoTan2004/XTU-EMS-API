from requests.cookies import RequestsCookieJar
import json

def serialize_token(cookies: RequestsCookieJar, compressed: bool = False) -> str:
    """Serialize a token by replacing spaces with underscores."""
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
        # 字符串压缩
        import bz2
        import base64
        serialized_token = bz2.compress(serialized_token.encode("utf-8"))
        serialized_token = base64.urlsafe_b64encode(serialized_token).decode("utf-8")
    return serialized_token


def deserialize_token(token: str, compressed: bool = False) -> RequestsCookieJar:
    """Deserialize a token by replacing underscores with spaces."""
    if compressed:
        # 字符串解压
        import bz2
        import base64
        token = bz2.decompress(token.encode("utf-8")).decode("utf-8")
        token = bz2.decompress(base64.urlsafe_b64decode(token.encode("utf-8"))).decode("utf-8")
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
    
