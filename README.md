# 湘潭大学网站接入指南

本项目旨在帮助开发者将湘潭大学的各类网站。

本项目采用开源协议，欢迎大家参与贡献。允许商用和二次开发，但请保留原作者信息。本项目对于因使用本项目而产生的任何法律责任不承担任何责任。使用者需自行承担使用风险。本项目仅作为技术分享学习之用。

项目创建于2026年1月，所用 API 和指南不保证全部可用，如有问题请提交issue

## PyPI 打包使用说明

### 安装

```bash
pip install xtu-ems-api
```

### 命令行工具

安装后可直接使用下列命令获取湘潭大学 EMS 信息：

```bash
xtu-sso-login --username <学号> --password <密码>
xtu-ems-auth --token <token>
xtu-course-schedule --token <token>
xtu-classroom-availability --token <token> --year 2025 --term 1 --weeks 1 2 3 --day-of-week 1 --sections 1 2
xtu-exam-schedule --token <token>
xtu-student-info --token <token>
xtu-teaching-calendar --token <token>
xtu-transcript --token <token>
```

命令支持 `--compressed` 参数以兼容压缩后的 Cookie token。

### 作为库调用

```python
from xtu_ems_api import sso_auth, ems_get_course_schedule

# 登录获取 token
cookies = sso_auth("202200000000", "your-password")

# 查询课表
courses = ems_get_course_schedule(cookies, year=2025, term=1)
```
