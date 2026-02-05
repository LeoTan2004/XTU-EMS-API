from __future__ import annotations

import argparse
import json
from typing import Iterable

from requests import Session, cookies

try:
    from .tokenizer import deserialize_token
except ImportError:  # pragma: no cover
    from tokenizer import deserialize_token

def parse_student_info(html: str) -> dict[str, str]:
    """
    解析 EMS 学生信息页面的 HTML 内容并提取结构化的学生信息字段。

    :param html: 从学生信息页面获取的完整 HTML 文本。
    :type html: str
    :return: 学生基本信息与学籍信息的字典表示。
    :rtype: dict
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    info: dict[str, str] = {}

    def _safe_get_text(panel, element_id: str) -> str:
        """
        安全地从指定元素中提取文本内容，缺失时返回空字符串。

        :param panel: 当前查找范围内的父级节点。
        :type panel: bs4.element.Tag | None
        :param element_id: 需要查找的元素 id。
        :type element_id: str
        :return: 对应元素的去除空白后的文本内容。
        :rtype: str
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
    info["student_id"] = _safe_get_text(basic_info_panel, "col_xh")
    info["name"] = _safe_get_text(basic_info_panel, "col_xm")
    info["gender"] = _safe_get_text(basic_info_panel, "col_xbm")
    info["birthday"] = _safe_get_text(basic_info_panel, "col_csrq")
    info["entrance_day"] = _safe_get_text(basic_info_panel, "col_rxrq")
    student_info_panel = soup.find(id="content_xsxxgl_xsxjxx")
    if student_info_panel is None:
        return info
    info["major"] = _safe_get_text(student_info_panel, "col_zyh_id")
    info["class"] = _safe_get_text(student_info_panel, "col_bh_id")
    info["college"] = _safe_get_text(student_info_panel, "col_jg_id")
    return info


def ems_get_info(cookie_jar: cookies.RequestsCookieJar) -> dict[str, str]:
    """
    使用 EMS 系统的用户凭证检索学生个人信息页面并解析核心字段。

    :param cookie_jar: 已登录 EMS 系统的会话 Cookie 集合，用于认证请求。
    :type cookie_jar: cookies.RequestsCookieJar
    :return: 包含学生基本信息与学籍信息的字典。
    :rtype: dict
    :raises Exception: 当请求过程中遇到非 2xx 状态码时抛出。
    """
    info_url = "https://jw.xtu.edu.cn/jwglxt/xsxxxggl/xsgrxxwh_cxXsgrxx.html?gnmkdm=N100801&layout=default"

    with Session() as session:
        session.cookies = cookie_jar
        response = session.get(info_url, allow_redirects=False)
        response.raise_for_status()
    html = response.text
    return parse_student_info(html)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EMS Student Info Script")
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
    student_info = ems_get_info(input_cookies)
    print(json.dumps(student_info, ensure_ascii=False, indent=4))


if __name__ == "__main__":  # pragma: no cover - CLI passthrough
    main()
