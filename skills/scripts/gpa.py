from __future__ import annotations

import argparse
import json
from typing import Iterable, Literal

from requests import Session, cookies

try:
    from .tokenizer import deserialize_token
except ImportError:  # pragma: no cover
    from tokenizer import deserialize_token


class GPAQueryData(dict):
    """
    表示 EMS GPA 查询的参数集合，用于封装请求所需的字段。

    :param start_year: GPA 计算的起始年份，示例 2025 表示 2025-2026 学年。
    :type start_year: int
    :param end_year: GPA 计算的结束年份，示例 2025 表示 2025-2026 学年。
    :type end_year: int
    :param start_term: GPA 计算的起始学期，1 表示第一学期，2 表示第二学期。
    :type start_term: int
    :param end_term: GPA 计算的结束学期，1 表示第一学期，2 表示第二学期。
    :type end_term: int
    :param time: 额外的时间戳参数，默认 0。
    :type time: int
    :param filter_option: GPA 计算的课程过滤选项，'Mandatory' 表示必修课程，'Elective' 表示选修课程，'All' 表示所有课程（默认）。
    :type filter_option: Literal['Mandatory', 'Elective', 'All']
    """

    def __init__(
        self,
        start_year: int,
        end_year: int,
        start_term: int,
        end_term: int,
        filter_option: Literal["Mandatory", "Elective", "All"] = "All",
        time: int = 0,
    ) -> None:
        super().__init__()
        self.start_year = start_year
        self.end_year = end_year
        self.start_term = start_term
        self.end_term = end_term
        self.time = time
        self.filter_option = filter_option

    def __repr__(self):
        import time

        xbx_mapping = {
            "Mandatory": "bx",
            "Elective": "xx",
            "All": "",
        }
        return (
            f"qsXnxq={self.start_year}{3 if self.start_term == 1 else 12:02d}"
            f"&zzXnxq={self.end_year}{3 if self.end_term == 1 else 12:02d}"
            f"&xbx={xbx_mapping[self.filter_option]}"
            "&_search=false"
            f"&nd={int(time.time() * 1000)}"
            "&queryModel.showCount=50"
            "&queryModel.currentPage=1"
            "&queryModel.sortName=xh+"
            "&queryModel.sortOrder=asc"
            f"&time={self.time}"
        )


def ems_get_gpa(
    input_cookies: cookies.RequestsCookieJar,
    gpa_query_data: GPAQueryData,
) -> dict:
    """
    使用提供的 EMS 认证 cookies 获取学生的 GPA 信息。

    :param input_cookies: 包含 EMS 认证信息的 cookies。
    :type input_cookies: requests.cookies.RequestsCookieJar
    :param gpa_query_data: 包含 GPA 查询参数的对象。
    :type gpa_query_data: GPAQueryData
    :return: 包含学生 GPA 信息的字典。
    :rtype: dict
    """
    gpa_url = "https://jw.xtu.edu.cn/jwglxt/cjpmtj/cjpmtj_cxPjxfjdpmtjIndex.html?doType=query&gnmkdm=N309104"
    gpa_info = {}
    headers = {
        "Host": "jw.xtu.edu.cn",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    with Session() as session:
        session.cookies = input_cookies
        # 这里假设有一个 API 端点可以接受这些参数并返回 GPA 信息, 这个接口需要设置最大响应时间以防止长时间等待、
        # 设置最大响应时间为20秒
        response = session.post(
            gpa_url,
            headers=headers,
            data=gpa_query_data.__repr__(),
            allow_redirects=False,
            timeout=20,
        )
        # 首先检查是否出现重定向（例如认证过期被重定向到登录页）
        if response.is_redirect or 300 <= response.status_code < 400:
            raise RuntimeError(
                f"Unexpected redirect when requesting GPA data; "
                f"status_code={response.status_code}, "
                f"location={response.headers.get('Location')!r}"
            )
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            raise RuntimeError(
                f"Expected JSON response for GPA data, got Content-Type {content_type!r}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError("Failed to parse GPA response as JSON") from exc
        data = response.json()
    if data is None or "items" not in data or len(data["items"]) == 0:
        return gpa_info  # 返回空字典表示没有数据
    gpa_panel = data["items"][0]
    gpa_info["average_score"] = gpa_panel.get("pjcj", "")  # 平均学分绩点
    gpa_info["average_gpa"] = gpa_panel.get("pjxfjd", "")  # 平均绩点
    gpa_info["class_rank"] = gpa_panel.get("jdbjpm", "")  # 班级排名
    gpa_info["grade_rank"] = gpa_panel.get("jdnjzypm", "")  # 年级排名"
    terms = (
        f"{gpa_query_data.start_year}-{gpa_query_data.start_year + 1}-{gpa_query_data.start_term} ~ "
        f"{gpa_query_data.end_year}-{gpa_query_data.end_year + 1}-{gpa_query_data.end_term}"
    )
    gpa_info["terms"] = gpa_panel.get("terms", terms)  # 学期范围
    return gpa_info


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
    parser.add_argument(
        "--start-year",
        type=int,
        default=2001,
        required=False,
        help="Starting year for GPA calculation (inclusive), default is 2001",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2030,
        required=False,
        help="Ending year for GPA calculation (inclusive), default is current year",
    )
    parser.add_argument(
        "--start-term",
        type=int,
        choices=[1, 2],
        required=False,
        default=1,
        help="Starting term for GPA calculation (1 for Spring, 2 for Fall), default is 1",
    )
    parser.add_argument(
        "--end-term",
        type=int,
        choices=[1, 2],
        default=2,
        required=False,
        help="Ending term for GPA calculation (1 for Spring, 2 for Fall), default is 2",
    )
    parser.add_argument(
        "--filter",
        choices=["Mandatory", "Elective", "All"],
        default="All",
        help="Filter for courses to include in GPA calculation: 'Mandatory' for mandatory courses, 'Elective' for elective courses, 'All' for all courses (default)",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    input_token = args.token
    compressed = args.compressed
    start_year = args.start_year
    end_year = args.end_year
    start_term = args.start_term
    end_term = args.end_term
    filter_option = args.filter
    input_cookies = deserialize_token(input_token, compressed=compressed)
    gpa_query_data = GPAQueryData(
        start_year=start_year,
        end_year=end_year,
        start_term=start_term,
        end_term=end_term,
        filter_option=filter_option,
    )
    student_info = ems_get_gpa(
        input_cookies,
        gpa_query_data=gpa_query_data,
    )
    print(json.dumps(student_info, ensure_ascii=False, indent=4))


if __name__ == "__main__":  # pragma: no cover - CLI passthrough
    main()
