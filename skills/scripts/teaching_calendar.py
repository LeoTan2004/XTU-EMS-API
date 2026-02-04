from requests import Session, cookies

def parse_calendar_info(response_text: str) -> dict:
    """
    解析教务系统返回的日历信息。

    :param response_text: 教务系统返回的日历信息文本
    :return: 学期日历信息的字典对象，包括学期开始和结束日期等
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response_text, "html.parser")
    info = {}

    th_elements = soup.find_all("th")
    if len(th_elements) < 2 or not th_elements[1].text:
        raise ValueError("Unexpected calendar HTML format: could not find term header in <th> elements.")
    panel = th_elements[1].text
    if "学年" not in panel or "学期" not in panel or "至" not in panel:
        raise ValueError("Unexpected calendar HTML format: term header does not contain expected substrings.")
    # panel: 2025-2026学年1学期(2025-09-01至2026-01-18)
    term_id = panel.replace("学年", "-").split("学期")[0]  # 2025-2026-1
    start_date = panel.split("(")[1].split("至")[0]  # 2025-09-01
    end_date = panel.split("至")[1].split(")")[0]  # 2026-01-18
    
    info["term_id"] = term_id
    info["start_date"] = start_date
    info["end_date"] = end_date
    return info

def ems_get_calendar(cookie_jar: cookies.RequestsCookieJar) -> dict:
    """
    从教务系统获取学期的日历信息。
    :param cookie_jar: 包含EMS系统登录后cookies的CookieJar对象
    :return: 学期日历信息的字典对象，包括学期开始和结束日期等
    """
    calendar_url = "https://jw.xtu.edu.cn/jwglxt/xtgl/index_cxAreaFive.html?localeKey=zh_CN&gnmkdm=index"
    with Session() as session:
        session.cookies = cookie_jar
        response = session.get(calendar_url)
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve calendar information, status code: {response.status_code}")
        # 从返回的 HTML 中提取教学周历数据
        text = response.text
        calendar_info = parse_calendar_info(text)
        return calendar_info


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
    calendar = ems_get_calendar(input_cookies)
    import json
    print(json.dumps(calendar, ensure_ascii=False, indent=4))