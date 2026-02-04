import argparse
import json
from io import BytesIO
from typing import Any, Dict, List, Optional

from requests import Session, cookies

from tokenizer import deserialize_token


def with_default(value: Any, default: str) -> str:
    """Return the stripped string value or a fallback when empty."""
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _safe_cell(row: List[Any], index: int, default: str = "") -> str:
    """Safely read a cell from a table row.
    :param row: A list representing a table row.
    :type row: List[Any]
    :param index: The index of the cell to read.
    :type index: int
    :param default: The default value to return if the cell is not found or empty.
    :type default: str
    :return: The cell value as a string, or the default if not found or empty.
    :rtype: str
    """
    if row is None or index >= len(row):
        return default
    return with_default(row[index], default)


def extract_segment(source: str, start: str, end: Optional[str] = None) -> str:
    """
    Extract a substring from source between start and end markers.
    :param source: The original string to extract from.
    :type source: str
    :param start: The starting marker string.
    :type start: str
    :param end: The ending marker string (optional).
    :type end: Optional[str]
    :return: The extracted substring, or empty string if not found.
    :rtype: str
    """
    if not source or not start:
        return ""
    else:
        if start not in source:
            return ""
        segment = source.split(start, 1)[1]
        if end and end in segment:
            segment = segment.split(end, 1)[0]
        return segment.strip()


def parse_transcript_scores(table: List[List[Any]]) -> List[Dict[str, Any]]:
    """
    解析成绩单表格中的课程成绩信息。
    :param table: 成绩单表格数据，包含表头和多行课程记录。
    :type table: List[List[Any]]
    :return: 课程成绩信息列表，每个元素为包含课程名称、类型、
                学分、成绩和学期的字典。
    :rtype: List[Dict[str, Any]]
    """

    header = table[0]
    group_size = 7 if header else 0
    term = 0
    score_list = []
    for col in range(len(header) // group_size if group_size else 0):
        name_idx = type_idx = credit_idx = score_idx = None
        for idx in range(col * group_size, (col + 1) * group_size):
            cell_content = header[idx]
            if not cell_content:
                continue
            content = "".join(str(cell_content).split())
            if content == "课程名称":
                name_idx = idx
            elif content == "课程性质":
                type_idx = idx
            elif content == "学分":
                credit_idx = idx
            elif content == "成绩":
                score_idx = idx
        if None in (name_idx, type_idx, credit_idx, score_idx):
            continue

        for row in table[1:-3]:
            if any(
                index >= len(row)
                for index in (name_idx, type_idx, credit_idx, score_idx)
            ):
                continue
            name_cell = row[name_idx]
            if not name_cell or "以 下 空 白" in str(name_cell):
                break
            name_text = str(name_cell).strip()
            if "学期" in name_text:
                term += 1
                continue

            course_type_raw = with_default(row[type_idx], "跨学科选修")
            course_type = (
                course_type_raw
                if course_type_raw in {"必修", "选修", "跨学科选修"}
                else "跨学科选修"
            )
            score_list.append(
                {
                    "name": name_text,
                    "type": course_type,
                    "credit": with_default(row[credit_idx], "0"),
                    "score": with_default(row[score_idx], ""),
                    "term": term,
                }
            )
    return score_list


def parse_transcript_pdf(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    解析成绩单 PDF 二进制内容并提取院系信息、课程成绩等结构化数据。

    :param pdf_bytes: 成绩单 PDF 文件的二进制数据。
    :type pdf_bytes: bytes
    :return: 包含院系、专业、学号、姓名及课程成绩列表等信息的字典。
    :rtype: Dict[str, Any]
    """

    import pdfplumber

    with pdfplumber.open(BytesIO(pdf_bytes)) as transcript_pdf:
        page = transcript_pdf.pages[0]
        text_lines = page.extract_text_lines()
        metadata_line = text_lines[1]["text"] if len(text_lines) > 1 else ""

        result: Dict[str, Any] = {
            "college": extract_segment(metadata_line, "学院:", "专业:"),
            "major": extract_segment(metadata_line, "专业:", "学号:"),
            "student_id": extract_segment(metadata_line, "学号:", "姓名:"),
            "name": extract_segment(metadata_line, "姓名:"),
            "scores": [],
        }

        table = page.extract_table()
        if not table:
            return result

        result["scores"] = parse_transcript_scores(table)

        average_row = table[-3] if len(table) >= 3 else []
        summary_row = table[-1] if len(table) >= 1 else []

        result.update(
            {
                "average_score": with_default(_safe_cell(average_row, 2, "100"), "100"),
                "gpa": with_default(_safe_cell(average_row, 16, "4.0"), "4.0"),
                "total_credit": [
                    with_default(_safe_cell(summary_row, 0, "0"), "0"),
                    with_default(_safe_cell(summary_row, 1, "0"), "0"),
                ],
                "compulsory_credit": [
                    with_default(_safe_cell(summary_row, 4, "0"), "0"),
                    with_default(_safe_cell(summary_row, 8, "0"), "0"),
                ],
                "elective_credit": [
                    with_default(_safe_cell(summary_row, 9, "0"), "0"),
                    with_default(_safe_cell(summary_row, 12, "0"), "0"),
                ],
                "cross_course_credit": [
                    with_default(_safe_cell(summary_row, 15, "0"), "0"),
                    with_default(_safe_cell(summary_row, 17, "0"), "0"),
                ],
            }
        )

    return result


def ems_download_transcript(cookie_jar: cookies.RequestsCookieJar) -> Dict[str, Any]:
    """
    使用 EMS 系统的用户凭证下载并解析成绩单 PDF，返回结构化的成绩单数据。
    :param cookie_jar: 已登录 EMS 教务系统的会话 Cookie 集合，用于进行认证请求。
    :type cookie_jar: cookies.RequestsCookieJar
    :return: 解析后的成绩单数据字典。
    :rtype: Dict[str, Any]
    """
    list_payload = (
        "gsdygx=10530-zw-qcmrgs"
        "&ids="
        "&bdykcxzDms="
        "&cytjkcxzDms="
        "&cytjkclbDms="
        "&cytjkcgsDms="
        "&bjgbdykcxzDms="
        "&bjgbdyxxkcxzDms="
        "&djksxmDms="
        "&cjbzmcDms="
        "&zdyfsxmDms="
        "&bdymaxcjbzmcDms="
        "&cjdySzxs="
    )

    with Session() as session:
        session.cookies = cookie_jar
        index_url = "https://jw.xtu.edu.cn/jwglxt/bysxxcx/xscjzbdy_cxXsCount.html?gnmkdm=N558020"
        response = session.post(index_url, allow_redirects=False)
        response.raise_for_status()

        list_url = (
            "https://jw.xtu.edu.cn/jwglxt/bysxxcx/xscjzbdy_dyList.html?gnmkdm=N558020"
        )
        response = session.post(
            list_url,
            data=list_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            allow_redirects=False,
        )
        response.raise_for_status()
        resource_url = response.text.strip().replace("\\", "")
        resource_url = resource_url.strip('"')
        pdf_url = f"https://jw.xtu.edu.cn{resource_url}"

        pdf_response = session.get(pdf_url, allow_redirects=False)
        pdf_response.raise_for_status()

    return parse_transcript_pdf(pdf_response.content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EMS Transcript Script")
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

    ems_cookies = deserialize_token(args.token, compressed=args.compressed)
    transcript = ems_download_transcript(ems_cookies)
    print(json.dumps(transcript, ensure_ascii=False, indent=4))
