from requests import Session, cookies


def parse_student_info(html: str) -> dict:
    """
    解析学生信息页面的HTML内容，提取学生信息。

    :param html: 学生信息页面的HTML内容
    :return: 包含学生信息的字典

    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    info = {}

    def _safe_get_text(panel, element_id: str) -> str:
        """
        Safely get stripped text from a child element by id.
        Returns an empty string if the panel or element is missing.
        """
        if panel is None:
            return ""
        element = panel.find(id=element_id)
        if element is None:
            return ""
        return element.get_text(strip=True)

    basic_info_panel = soup.find(id="content_xsxxgl_xsjbxx")
    if basic_info_panel is None:
        return info
    # 基本信息面板
    info["student_id"] = _safe_get_text(basic_info_panel, "col_xh")
    info["name"] = _safe_get_text(basic_info_panel, "col_xm")
    info["gender"] = _safe_get_text(basic_info_panel, "col_xbm")
    info["birthday"] = _safe_get_text(basic_info_panel, "col_csrq")
    info["entrance_day"] = _safe_get_text(basic_info_panel, "col_rxrq")
    # 学籍信息面板
    student_info_panel = soup.find(id="content_xsxxgl_xsxjxx")
    if student_info_panel is None:
        return info
    info["major"] = _safe_get_text(student_info_panel, "col_zyh_id")
    info["class"] = _safe_get_text(student_info_panel, "col_bh_id")
    info["college"] = _safe_get_text(student_info_panel, "col_jg_id")
    return info


def ems_get_info(cookie_jar: cookies.RequestsCookieJar) -> dict:
    """
    使用EMS系统的用户凭证获取学生信息。

    :param cookie_jar: 包含EMS系统登录后cookies的CookieJar对象
    :return: 包含学生信息的字典

    """
    info_url = "https://jw.xtu.edu.cn/jwglxt/xsxxxggl/xsgrxxwh_cxXsgrxx.html?gnmkdm=N100801&layout=default"

    with Session() as session:
        session.cookies = cookie_jar
        response = session.get(info_url, allow_redirects=False)
        # When allow_redirects=False, a 3xx status usually indicates an authentication
        # problem (e.g., redirect to login page) or an unexpected redirect target.
        response.raise_for_status()
    html = response.text
    info = parse_student_info(html)
    return info


if __name__ == "__main__":
    import argparse
    from tokenizer import deserialize_token

    parser = argparse.ArgumentParser(description="EMS SSO Authentication Script")
    parser.add_argument(
        "--token",
        type=str,
        required=True,
        help="Serialized token which must contain EMS authentication cookies",
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
    student_info = ems_get_info(input_cookies)
    print(student_info)
