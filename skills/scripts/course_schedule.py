from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from typing import Iterable

from requests import Session, cookies

try:
    from .tokenizer import deserialize_token
except ImportError:  # pragma: no cover
    from tokenizer import deserialize_token

def parse_weeks(weeks_str: str) -> list[int]:
    """
    将 EMS 返回的周次字符串解析为按升序排列的周次整数列表。

    :param weeks_str: 教务系统中的周次描述，例如 "1-16周"、"3-15(单)"。
    :type weeks_str: str
    :return: 去重后的周次整数集合，使用升序列表表示。
    :rtype: list
    """
    if not weeks_str:
        return []
    normalized = weeks_str.replace("周", "").replace("，", ",")
    parts = [part.strip() for part in normalized.split(",") if part.strip()]
    weeks: list[int] = []
    for part in parts:
        range_part = part
        filter_type = None
        if "(" in part and ")" in part:
            range_part = part.split("(")[0]
            filter_type = part.split("(")[1].split(")")[0]
        range_part = range_part.strip()
        if not range_part:
            continue
        if "-" in range_part:
            start_str, end_str = range_part.split("-", 1)
            try:
                start = int(start_str)
                end = int(end_str)
            except ValueError:
                continue
            candidate_weeks = list(range(start, end + 1))
        else:
            try:
                week = int(range_part)
            except ValueError:
                continue
            candidate_weeks = [week]
        if filter_type == "单":
            candidate_weeks = [week for week in candidate_weeks if week % 2 == 1]
        elif filter_type == "双":
            candidate_weeks = [week for week in candidate_weeks if week % 2 == 0]
        weeks.extend(candidate_weeks)
    return sorted(set(weeks))


def parse_sections(section_str: str) -> list[int]:
    """
    将课节描述字符串转换为节次整数列表，支持单节或区间格式。

    :param section_str: 原始节次描述，例如 "第1-2节"、"第5节"。
    :type section_str: str
    :return: 对应的节次整数列表，按升序排列。
    :rtype: list
    """
    if not section_str:
        return []
    cleaned = section_str.replace("节", "").replace("第", "")
    cleaned = cleaned.strip()
    if not cleaned:
        return []
    if "-" in cleaned:
        start_str, end_str = cleaned.split("-", 1)
        try:
            start = int(start_str)
            end = int(end_str)
        except ValueError:
            return []
    else:
        try:
            start = end = int(cleaned)
        except ValueError:
            return []
    if end < start:
        start, end = end, start
    return list(range(start, end + 1))


def parse_courses_list(courses_list: list[dict] | None) -> list[dict]:
    """
    将 EMS 接口返回的课程列表转为结构化且字段规范的课程字典列表。

    :param courses_list: EMS 接口返回的原始课程数据列表。
    :type courses_list: list | None
    :return: 每门课程的结构化信息列表，包含课程名称、教师、场地等字段。
    :rtype: list
    """
    courses: list[dict] = []
    for course in courses_list or []:
        name = course.get("kcmc", "").strip()
        teacher = course.get("xm", "").strip()
        location = course.get("cdmc", "").strip()
        weeks = parse_weeks(course.get("zcd", ""))
        sections = parse_sections(course.get("jc", ""))
        day_raw = str(course.get("xqj", "1")).strip()
        try:
            day_of_week = int(day_raw)
        except ValueError:
            day_of_week = 1
        courses.append(
            {
                "name": name,
                "teacher": teacher,
                "location": location,
                "weeks": weeks,
                "day_of_week": day_of_week,
                "sections": sections,
            }
        )
    return courses


def get_term_year(d: date) -> int:
    """
    根据指定日期推算所属学年的起始年份，8 月前视为上一学年。

    :param d: 用于推算的日期对象。
    :type d: date
    :return: 学年起始年份整数值。
    :rtype: int
    """
    return d.year - 1 if d.month < 8 else d.year


def get_term_id(d: date) -> int:
    """
    根据指定日期推断当前学期，返回 EMS 使用的学期编码。

    :param d: 用于推算的日期对象。
    :type d: date
    :return: 学期编码，第一学期返回 3，第二学期返回 12。
    :rtype: int
    """
    return 12 if 2 <= d.month <= 7 else 3


def normalize_term(term: int) -> int:
    """
    将用户输入的学期编号转换为 EMS 接口使用的学期编码。

    :param term: 学期编号，可为逻辑编号 1/2 或 EMS 编码 3/12。
    :type term: int
    :return: 与 EMS 接口兼容的学期编码。
    :rtype: int
    """
    if term == 1:
        return 3
    if term == 2:
        return 12
    return term


def ems_get_course_schedule(
    cookie_jar: cookies.RequestsCookieJar,
    year: int | None = None,
    term: int | None = None,
) -> list[dict]:
    """
    使用 EMS 系统的用户凭证获取课表信息。

    :param cookie_jar: 已登录 EMS 教务系统的会话 Cookie 集合，用于进行认证请求。
    :type cookie_jar: cookies.RequestsCookieJar
    :param year: 学年起始年份。例如 2025 表示 2025-2026 学年。
    :type year: int | None
    :param term: 学期编号，可以是“逻辑学期号”或“EMS 编码”。
    :type term: int | None
    :return: 解析后的课程记录列表。
    :rtype: list
    """
    courses_url = (
        "https://jw.xtu.edu.cn/jwglxt/kbcx/xskbcx_cxXsgrkb.html?gnmkdm=N2151"
    )
    current_date = datetime.now().date()
    if year is None:
        year = get_term_year(current_date)
    if term is None:
        term = get_term_id(current_date)
    term_for_payload = normalize_term(term)
    payload = {
        "xnm": str(year),
        "xqm": str(term_for_payload),
        "kzlx": "ck",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    with Session() as session:
        session.cookies = cookie_jar
        response = session.post(courses_url, data=payload, headers=headers)
        response.raise_for_status()
        resp_json = response.json()
        courses_list = resp_json.get("kbList", [])
        return parse_courses_list(courses_list)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EMS Course Schedule Script")
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
    parser.add_argument(
        "--year",
        type=int,
        required=False,
        help=(
            "Academic year, e.g., 2025 for the 2025-2026 academic year, "
            "defaults to current academic year"
        ),
    )
    parser.add_argument(
        "--term",
        type=int,
        required=False,
        help=(
            "Term number, accepts either 1/2 or ERP codes 3/12; defaults to current term"
        ),
    )
    return parser


def main(argv: Iterable[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    input_token = args.token
    compressed = args.compressed
    input_cookies = deserialize_token(input_token, compressed=compressed)
    courses = ems_get_course_schedule(input_cookies, year=args.year, term=args.term)
    print(json.dumps(courses, ensure_ascii=False, indent=4))


if __name__ == "__main__":  # pragma: no cover - CLI passthrough
    main()
