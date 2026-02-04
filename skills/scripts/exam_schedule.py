from requests import Session, cookies
import time
from datetime import datetime, date
import argparse
from tokenizer import deserialize_token
import json
def parse_exams_list(exams_list) -> list:
    """
    解析考试信息列表

    :param exams_list: 原始考试列表
    :return: 解析后的考试信息字典列表
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
    获取当前学年

    学年从每年的8月开始，到次年的7月结束
    例如：
    - 2023年8月到2024年7月是2023-2024学年
    - 2024年8月到2025年7月是2024-2025学年

    :param d: 日期时间对象
    :return: 学年开始的年份
    例如，2023-2024学年返回2023
    """
    year = d.year
    month = d.month
    if month < 8:
        return year - 1
    else:
        return year


def get_term_id(d: date) -> int:
    """
    获取当前学期

    学期分为两个：
    - 第1学期：8月到次年1月
    - 第2学期：2月到7月

    :param d: 日期时间对象
    :return: 学期编号，1或2

    """
    month = d.month
    return 2 if 2 <= month <= 7 else 1

def ems_get_exam_schedule(cookie_jar: cookies.RequestsCookieJar, year=None, term=None) -> list:
    """
    使用EMS系统的用户凭证获取考试安排信息。

    :param cookie_jar: 包含EMS系统登录后cookies的CookieJar对象
    :param year: 学年
    :param term: 学期
    :return: 考试安排信息字典列表
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