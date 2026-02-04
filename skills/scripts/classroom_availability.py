from requests import Session, cookies


class ClassroomQueryData(dict):
    def __init__(
        self,
        year,
        term,
        weeks: list[int],
        day_of_week: int,
        sections: list[int],
        time=0,
    ):
        super().__init__()
        self.year = year
        self.term = term
        self.weeks = weeks
        self.day_of_week = day_of_week
        self.sections = sections
        self.time = time

    @staticmethod
    def _bits_of_list(ls: list[int]) -> int:
        result = 0
        for i in ls:
            result |= 1 << (i - 1)
        return result

    def __repr__(self):
        import time

        return (
            f"xqh_id=02"
            f"&xnm={self.year}"
            f"&xqm={3 if self.term == 1 else 12}"
            f"&cdlb_id=01"
            f"&jyfs=0"
            f"&zcd={self._bits_of_list(self.weeks)}"
            f"&xqj={self.day_of_week}"
            f"&jcd={self._bits_of_list(self.sections)}"
            f"&_search=false"
            f"&nd={int(time.time() * 1000)}"  # 当前时间戳，防止缓存
            f"&queryModel.showCount=99999"
            f"&queryModel.currentPage=1"
            f"&queryModel.sortName=cdbh+"
            f"&queryModel.sortOrder=asc"
            f"&time={self.time}"
        )

def ems_get_classsroom_avaliability(
    cookie_jar: cookies.RequestsCookieJar, query_data: ClassroomQueryData
) -> list[str]:
    """
    获取教室状态

    :param session: 已登录的 HttpSessionHolder 对象
    :param query: 查询参数
    :return: 空闲的教室名称，列表
    """
    headers = {
        "Host": "jw.xtu.edu.cn",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    # print(query.__dict__)
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
                f"Failed to retrieve classroom availability information, status code: {response.status_code}"
            )
        # 从返回的 JSON 中提取教室使用情况数据
        data = response.json()
        return [item['cdmc'] for item in data['items']]


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
    args = parser.parse_args()
    input_token = args.token
    compressed = args.compressed
    year = args.year
    term = args.term
    weeks = args.weeks
    day_of_week = args.day_of_week
    sections = args.sections
    input_cookies = deserialize_token(input_token, compressed=compressed)
    query_data = ClassroomQueryData(
        year=year,
        term=term,
        weeks=weeks,
        day_of_week=day_of_week,
        sections=sections,
    )
    available_classrooms = ems_get_classsroom_avaliability(input_cookies, query_data)
    import json
    print(json.dumps(available_classrooms, ensure_ascii=False, indent=4))