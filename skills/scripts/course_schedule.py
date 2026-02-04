from requests import Session, cookies
from datetime import datetime, date
import argparse
import json
from tokenizer import deserialize_token


def parse_weeks(weeks_str: str) -> list:
    """将教务系统的周次描述解析为周次整数列表。"""
    if not weeks_str:
        return []
    normalized = weeks_str.replace("周", "").replace("，", ",")
    parts = [part.strip() for part in normalized.split(",") if part.strip()]
    weeks = []
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


def parse_sections(section_str: str) -> list:
    """将节次描述转换为节次整数列表。"""
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


def parse_courses_list(courses_list) -> list:
    """解析课程列表为结构化的课程字典列表。"""
    courses = []
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
    """根据日期推断学年起始年份。"""
    return d.year - 1 if d.month < 8 else d.year


def get_term_id(d: date) -> int:
    """根据日期推断学期，第一学期返回3，第二学期返回12。"""
    return 12 if 2 <= d.month <= 7 else 3


def normalize_term(term: int) -> int:
    """接受用户输入的学期编号，必要时转换为教务系统使用的编码。"""
    if term == 1:
        return 3
    if term == 2:
        return 12
    return term


def ems_get_course_schedule(
    cookie_jar: cookies.RequestsCookieJar,
    year: int | None = None,
    term: int | None = None,
) -> list:
    
    """
    使用 EMS 系统的用户凭证获取课表信息。

    :param cookie_jar: 已登录 EMS 教务系统的会话 Cookie 集合，用于进行认证请求。
    :type cookie_jar: cookies.RequestsCookieJar
    :param year: 学年起始年份。例如 2025 表示 2025-2026 学年。
        - 为 None 时，将根据当前日期自动推断所属学年的起始年份（见 get_term_year）。
        - 非 None 时，将直接作为请求参数 xnm 发送给教务系统。
    :type year: int | None
    :param term: 学期编号，可以是“逻辑学期号”或“EMS 编码”：
        - 1 表示第一学期（自动转换为 EMS 编码 3）
        - 2 表示第二学期（自动转换为 EMS 编码 12）
        - 3 或 12 可直接传递 EMS 编码
        - None 时自动推断当前学期（见 get_term_id）
    :type term: int | None
    :return: 由 parse_courses_list 解析后的课程记录列表。通常为若干字典组成的列表，
        每个元素对应一门课程或一条课表记录，包含课程名称、时间、周次、节次等
        从 EMS 接口返回的 kbList 字段中提取并规范化后的信息。
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


if __name__ == "__main__":
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
    args = parser.parse_args()
    input_token = args.token
    compressed = args.compressed

    input_cookies = deserialize_token(input_token, compressed=compressed)
    courses = ems_get_course_schedule(input_cookies, year=args.year, term=args.term)
    print(json.dumps(courses, ensure_ascii=False, indent=4))
