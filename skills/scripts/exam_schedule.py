from requests import Session, cookies
import time
from datetime import datetime, date
import argparse
from tokenizer import deserialize_token
import json
def parse_exams_list(exams_list) -> list:
    """
    将 EMS 返回的考试安排列表解析为结构化的考试信息字典列表。

    :param exams_list: 原始考试记录列表，来源于 EMS 接口的 items 字段。
    :type exams_list: list | None
    :return: 每场考试的结构化信息，包括名称、时间、地点和类型。
    :rtype: list
    """
    exams = []
    for exam in exams_list:
        exam_name = exam.get("kcmc", "").strip()
        exam_time = exam.get("kssj", "").strip()  # "2026-01-10(10:30-12:30)"
        if "(" in exam_time and ")" in exam_time:
            start_str = exam_time.split("(")[0]
            time_range = exam_time.split("(")[1].split(")")[0]
            start_time_str, end_time_str = time_range.split("-")
            start_time = f"{start_str} {start_time_str}"
            end_time = f"{start_str} {end_time_str}"
        else:
            start_time = exam_time
            end_time = exam_time

        location = exam.get("cdmc", "").strip()
        exam_type = exam.get("khfs", "考试").strip()
        exams.append({
            "name": exam_name,
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
            "type": exam_type
        })
    return exams

def get_term_year(d: date) -> int:
    """
    根据日期推断所属学年，8 月之前归属于上一学年，8 月及以后归属当年。

    :param d: 需要判断学年的日期对象。
    :type d: date
    :return: 学年起始年份整数，例 2023 表示 2023-2024 学年。
    :rtype: int
    """
    year = d.year
    month = d.month
    if month < 8:
        return year - 1
    else:
        return year


def get_term_id(d: date) -> int:
    """
    根据日期判断当前学期编号，2-7 月视为第二学期，其余月份视为第一学期。

    :param d: 需要判断学期的日期对象。
    :type d: date
    :return: 学期编号，1 表示第一学期，2 表示第二学期。
    :rtype: int
    """
    month = d.month
    return 2 if 2 <= month <= 7 else 1

def ems_get_exam_schedule(cookie_jar: cookies.RequestsCookieJar, year=None, term=None) -> list:
    """
    使用 EMS 系统的用户凭证查询指定学年学期的考试安排信息。

    :param cookie_jar: 已登录 EMS 系统的会话 Cookie 集合，用于接口认证。
    :type cookie_jar: cookies.RequestsCookieJar
    :param year: 学年起始年份，为 None 时自动根据当前日期推断。
    :type year: int | None
    :param term: 学期编号，1 表示第一学期，2 表示第二学期，为 None 时自动推断。
    :type term: int | None
    :return: 结构化的考试安排信息列表。
    :rtype: list
    """
    exams_url = "https://jw.xtu.edu.cn/jwglxt/kwgl/kscx_cxXsksxxIndex.html?doType=query&gnmkdm=N358105"
    date = datetime.now().date()
    if year is None or term is None:
        year = get_term_year(date)
        term = get_term_id(date)
    current_date = datetime.now().date()
    if year is None or term is None:
        year = get_term_year(current_date)
        term = get_term_id(current_date)
    payload = (
        f"xnm={year}"
        f"&xqm={term}"
        f"&ksmcdmb_id="
        f"&kch="
        f"&kc="
        f"&ksrq="
        f"&kkbm_id="
        f"&_search=false"
        f"&nd={int(time.time() * 1000)}"
        f"&queryModel.showCount=9999"
        f"&queryModel.currentPage=1"
        f"&queryModel.sortName=+"
        f"&queryModel.sortOrder=asc"
        f"&time=1"
    )

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    with Session() as session:
        session.cookies = cookie_jar
        response = session.post(exams_url, data=payload, headers=headers)
        response.raise_for_status()
        resp_json = response.json()
        exams_list = resp_json.get("items", [])
        return parse_exams_list(exams_list)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="EMS Exam Schedule Script")
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
        help="Academic year, e.g., 2025 for the 2025-2026 academic year, defaults to current academic year",
    )
    parser.add_argument(
        "--term",
        type=int,
        required=False,
        help="Term number, e.g., 1 for the first term, 2 for the second term, defaults to current term",
    )
    args = parser.parse_args()
    input_token = args.token
    compressed = args.compressed

    input_cookies = deserialize_token(input_token, compressed=compressed)
    exams = ems_get_exam_schedule(input_cookies, year=args.year, term=args.term)
    print(json.dumps(exams, ensure_ascii=False, indent=4))