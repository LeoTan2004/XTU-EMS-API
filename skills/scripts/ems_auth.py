from requests import Session, cookies

def ems_auth_with_sso(cookie_jar: cookies.RequestsCookieJar) -> cookies.RequestsCookieJar:
    """
    使用SSO登录获取EMS系统的用户凭证。

    :param cookie_jar: 包含用户凭证的CookieJar对象
    :return: 包含EMS系统登录后cookies的CookieJar对象

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


if __name__ == "__main__":
    import argparse
    from tokenizer import deserialize_token, serialize_token

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
    args = parser.parse_args()
    input_token = args.token
    compressed = args.compressed

    input_cookies = deserialize_token(input_token, compressed=compressed)
    ems_cookies = ems_auth_with_sso(input_cookies)
    output_token = serialize_token(ems_cookies, compressed=compressed)
    print(output_token)
