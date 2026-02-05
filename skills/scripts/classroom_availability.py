from __future__ import annotations

import argparse
from typing import Iterable

from requests import Session, cookies

try:
    from .tokenizer import deserialize_token
except ImportError:  # pragma: no cover
    from tokenizer import deserialize_token

class ClassroomQueryData(dict):
    """
    表示 EMS 教室空闲查询的参数集合，用于封装请求所需的字段。

    :param year: 学年起始年份，示例 2025 表示 2025-2026 学年。
    :type year: int
    :param term: 学期编号，1 表示第一学期，2 表示第二学期。
    :type term: int
    :param weeks: 需要查询的教学周列表，采用整数周次。
    :type weeks: list[int]
    :param day_of_week: 星期几的节次安排，1 表示周一，7 表示周日。
    :type day_of_week: int
    :param sections: 需要查询的节次列表，整数表示第几节。
    :type sections: list[int]
    :param time: 额外的时间戳参数，默认 0。
    :type time: int
    """

    def __init__(
        self,
        year: int,
        term: int,
        weeks: list[int],
        day_of_week: int,
        sections: list[int],
        time: int = 0,
    ) -> None:
        super().__init__()
        self.year = year
        self.term = term
        self.weeks = weeks
        self.day_of_week = day_of_week
        self.sections = sections
        self.time = time

    @staticmethod
    def _bits_of_list(ls: list[int]) -> int:
        """
        将周次或节次列表转换为位掩码整数表示，兼容教务系统的查询格式。

        :param ls: 由周次或节次整数构成的列表。
        :type ls: list[int]
        :return: 对应的位掩码整数值。
        :rtype: int
        """

        result = 0
        for i in ls:
            result |= 1 << (i - 1)
        return result

    def __repr__(self) -> str:  # pragma: no cover - string formatting helper
        import time

        return (
            "xqh_id=02"
            f"&xnm={self.year}"
            f"&xqm={3 if self.term == 1 else 12}"
            "&cdlb_id=01"
            "&jyfs=0"
            f"&zcd={self._bits_of_list(self.weeks)}"
            f"&xqj={self.day_of_week}"
            f"&jcd={self._bits_of_list(self.sections)}"
            "&_search=false"
            f"&nd={int(time.time() * 1000)}"
            "&queryModel.showCount=99999"
            "&queryModel.currentPage=1"
            "&queryModel.sortName=cdbh+"
            "&queryModel.sortOrder=asc"
            f"&time={self.time}"
        )


def ems_get_classroom_availability(
    cookie_jar: cookies.RequestsCookieJar, query_data: ClassroomQueryData
) -> list[str]:
    """
    使用 EMS 系统的用户凭证查询指定条件下的空闲教室列表。

    :param cookie_jar: 已登录 EMS 系统的会话 Cookie 集合，用于身份校验。
    :type cookie_jar: cookies.RequestsCookieJar
    :param query_data: 封装了学年、学期、周次、节次等查询条件的对象。
    :type query_data: ClassroomQueryData
    :return: 满足条件的空闲教室名称列表。
    :rtype: list[str]
    :raises Exception: 当接口返回异常状态码时抛出，用于提示查询失败。
    """

    headers = {
        "Host": "jw.xtu.edu.cn",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    classroom_status_url = (
        "https://jw.xtu.edu.cn/jwglxt/cdjy/cdjy_cxKxcdlb.html?doType=query&gnmkdm=N2155"
    )
    payload = query_data.__repr__()
    with Session() as session:
        session.cookies = cookie_jar
        response = session.post(
            classroom_status_url, headers=headers, data=payload, allow_redirects=False
        )
        if response.status_code != 200:
            raise Exception(
                "Failed to retrieve classroom availability information, "
                f"status code: {response.status_code}"
            )
        data = response.json()
        return [item["cdmc"] for item in data["items"]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EMS Classroom Availability Script")
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
        required=True,
        help="Academic year, e.g., 2025 for the 2025-2026 academic year",
    )
    parser.add_argument(
        "--term",
        type=int,
        required=True,
        help="Term number, e.g., 1 for the first term",
    )
    parser.add_argument(
        "--weeks",
        type=int,
        nargs="+",
        required=True,
        help="List of week numbers to query, e.g., 1 2 3",
    )
    parser.add_argument(
        "--day-of-week",
        type=int,
        required=True,
        help="Day of the week (1=Monday, 7=Sunday)",
    )
    parser.add_argument(
        "--sections",
        type=int,
        nargs="+",
        required=True,
        help="List of class sections to query, e.g., 1 2 3",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    input_token = args.token
    compressed = args.compressed
    input_cookies = deserialize_token(input_token, compressed=compressed)
    query_data = ClassroomQueryData(
        year=args.year,
        term=args.term,
        weeks=args.weeks,
        day_of_week=args.day_of_week,
        sections=args.sections,
    )
    available_classrooms = ems_get_classroom_availability(input_cookies, query_data)
    import json

    print(json.dumps(available_classrooms, ensure_ascii=False, indent=4))


ems_get_classsroom_avaliability = ems_get_classroom_availability  # backward compat


if __name__ == "__main__":  # pragma: no cover - CLI passthrough
    main()
