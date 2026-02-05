from __future__ import annotations

import argparse
import json
from typing import Iterable

from requests import Session, cookies

try:
    from .tokenizer import deserialize_token
except ImportError:  # pragma: no cover
    from tokenizer import deserialize_token

def parse_calendar_info(response_text: str) -> dict[str, str]:
    """
    解析 EMS 教务系统返回的日历 HTML 内容并提取学期起止日期等信息。

    :param response_text: 日历页面的 HTML 文本内容。
    :type response_text: str
    :return: 包含学期标识、开始日期与结束日期的字典。
    :rtype: dict
    :raises ValueError: 当页面结构不符合预期时抛出，用于提示解析失败。
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response_text, "html.parser")
    info: dict[str, str] = {}

    th_elements = soup.find_all("th")
    if len(th_elements) < 2 or not th_elements[1].text:
        raise ValueError(
            "Unexpected calendar HTML format: could not find term header in <th> elements."
        )
    panel = th_elements[1].text
    if "学年" not in panel or "学期" not in panel or "至" not in panel:
        raise ValueError(
            "Unexpected calendar HTML format: term header does not contain expected substrings."
        )
    term_id = panel.replace("学年", "-").split("学期")[0]
    start_date = panel.split("(")[1].split("至")[0]
    end_date = panel.split("至")[1].split(")")[0]

    info["term_id"] = term_id
    info["start_date"] = start_date
    info["end_date"] = end_date
    return info


def ems_get_calendar(cookie_jar: cookies.RequestsCookieJar) -> dict[str, str]:
    """
    使用 EMS 系统的用户凭证获取学期教学日历并返回关键日期信息。

    :param cookie_jar: 已登录 EMS 系统的会话 Cookie 集合，用于访问日历页面。
    :type cookie_jar: cookies.RequestsCookieJar
    :return: 学期日历信息字典，包括学期标识、开始日期和结束日期。
    :rtype: dict
    :raises Exception: 当接口请求失败且返回非 200 状态码时抛出。
    """
    calendar_url = "https://jw.xtu.edu.cn/jwglxt/xtgl/index_cxAreaFive.html?localeKey=zh_CN&gnmkdm=index"
    with Session() as session:
        session.cookies = cookie_jar
        response = session.get(calendar_url)
        if response.status_code != 200:
            raise Exception(
                "Failed to retrieve calendar information, status code: "
                f"{response.status_code}"
            )
        text = response.text
        return parse_calendar_info(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EMS Teaching Calendar Script")
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
    return parser


def main(argv: Iterable[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    input_token = args.token
    compressed = args.compressed

    input_cookies = deserialize_token(input_token, compressed=compressed)
    calendar = ems_get_calendar(input_cookies)
    print(json.dumps(calendar, ensure_ascii=False, indent=4))


if __name__ == "__main__":  # pragma: no cover - CLI passthrough
    main()
