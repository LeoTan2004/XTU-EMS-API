"""XTU EMS API toolkit.

This package bundles helpers and command line entry points for interacting
with the XTU EMS (教学管理系统) portal.
"""

from __future__ import annotations

from importlib.metadata import version, PackageNotFoundError

from .classroom_availability import ClassroomQueryData, ems_get_classroom_availability
from .course_schedule import ems_get_course_schedule
from .ems_auth import ems_auth_with_sso
from .exam_schedule import ems_get_exam_schedule
from .sso_login import get_config, rsa_encrypt, sso_auth
from .student_info import ems_get_info
from .teaching_calendar import ems_get_calendar
from .tokenizer import deserialize_token, serialize_token
from .transcript import ems_download_transcript

try:  # pragma: no cover - defensive guard for metadata lookup
    __version__ = version("xtu-ems-api")
except PackageNotFoundError:  # pragma: no cover - runtime fallback for local usage
    __version__ = "0.0.0"

__all__ = [
    "ClassroomQueryData",
    "deserialize_token",
    "ems_download_transcript",
    "ems_get_calendar",
    "ems_get_classroom_availability",
    "ems_get_course_schedule",
    "ems_get_exam_schedule",
    "ems_get_info",
    "ems_auth_with_sso",
    "get_config",
    "rsa_encrypt",
    "serialize_token",
    "sso_auth",
    "__version__",
]
