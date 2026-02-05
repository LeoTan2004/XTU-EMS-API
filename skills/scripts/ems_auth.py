from __future__ import annotations

import argparse
from typing import Iterable

from requests import Session, cookies

try:
    from .tokenizer import deserialize_token, serialize_token
except ImportError:  # pragma: no cover
    from tokenizer import deserialize_token, serialize_token

def ems_auth_with_sso(cookie_jar: cookies.RequestsCookieJar) -> cookies.RequestsCookieJar:
    """
    使用现有 SSO 登录态换取 EMS 系统的会话 Cookie 集合。

    :param cookie_jar: 已完成 SSO 认证的 Cookie 集合，用于继续访问 EMS。
    :type cookie_jar: cookies.RequestsCookieJar
    :return: EMS 系统登录后的 Cookie 集合，可用于后续接口请求。
    :rtype: cookies.RequestsCookieJar
    :raises Exception: 当最终跳转地址未进入 EMS 首页时抛出，用于提示认证失败。
    """
    homepage_url_prefix = "https://jw.xtu.edu.cn:443/jwglxt/xtgl/index_initMenu.html"

    with Session() as session:
        session.cookies = cookie_jar
        auth_url = "https://jw.xtu.edu.cn/sso/zfiotlogin"
        response = session.get(auth_url)
        final_url = response.url
        if not final_url.startswith(homepage_url_prefix):
            raise Exception(f"EMS Authentication Failed via SSO {final_url}")
        return session.cookies


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EMS SSO Authentication Script")
    parser.add_argument(
        "--token",
        type=str,
        required=True,
        help="Serialized token which must contain SSO authentication cookies",
    )
    parser.add_argument(
        "--compressed",
        action="store_true",
        help="Whether the input token is compressed",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    input_token = args.token
    compressed = args.compressed

    input_cookies = deserialize_token(input_token, compressed=compressed)
    ems_cookies = ems_auth_with_sso(input_cookies)
    output_token = serialize_token(ems_cookies, compressed=compressed)
    print(output_token)


if __name__ == "__main__":  # pragma: no cover - CLI passthrough
    main()
