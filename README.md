# 🚀 XTU-EMS-API | 湘潭大学教务聚合接口

一个开发者友好的 EMS（Educational Management System）接入工具包，让你用最少的代码触达湘潭大学的统一身份认证、课表、考试、成绩等关键信息流。🙂

## ✨ 你将收获什么
- 🎯 **多端统一**：CLI + Python SDK + Agent Skills 三通道可选。
- 🔐 **安全认证链路**：覆盖 SSO 登录、EMS Cookie 获取与压缩 Token 传递。
- 📅 **完整教务视图**：课表、考试、空教室、教学日历、成绩一网打尽。
- 🧩 **可扩展脚本**：`skills/scripts` 下的技能脚本随拿随用，可快速改造成自动化任务。

## 🤖 Agent Skills 兼容声明
本项目已完成 Agent Skills 规范对接（见 `skills/SKILLS.md`），可被具备技能编排能力的智能体直接调用：
1. 在 Agent 中注册 `XTU-API-SKILLS` 规范。
2. 为技能配置必要的凭证（如用户名、密码或 Token）。
3. 直接透传脚本参数，即可让 Agent 按需触发登录、教务查询和报表整理。🤝

## 📦 安装与环境
- 需要 Python ≥ 3.10。
- 从 PyPI 安装：

```bash
pip install xtu-ems-api
```

> 若需本地调试技能脚本，可直接运行 `python skills/scripts/<script>.py ...`。

## 🛠️ CLI 使用速览
安装后即刻拥有下列命令，全部支持 `--compressed` 以接收压缩后的 Cookie Token。

| 命令 | 作用 | 常用参数 |
| --- | --- | --- |
| `xtu-sso-login` | 统一身份认证获取原始 Token | `--username` `--password`
| `xtu-ems-auth` | 用 SSO Token 换取 EMS Cookies | `--token` `--compressed`
| `xtu-course-schedule` | 查询课表 | `--token` `--year` `--term`
| `xtu-classroom-availability` | 批量查询空教室 | `--weeks` `--day-of-week` `--sections`
| `xtu-exam-schedule` | 获取考试安排 | `--year` `--term`
| `xtu-student-info` | 查看个人信息档案 | `--token`
| `xtu-teaching-calendar` | 拉取教学日历 | `--token`
| `xtu-transcript` | 解析成绩（依赖 `pdfplumber`） | `--token`

示例：

```bash
xtu-classroom-availability \
	--token <cookie_token> \
	--year 2025 --term 1 \
	--weeks 1 2 3 --day-of-week 1 --sections 1 2 3 --compressed
```

## 🐍 作为 Python 库调用

```python
from xtu_ems_api import sso_auth, ems_get_course_schedule

# 1. 登录并获取 EMS Cookies（可选 compressed 写盘后复用）
cookies = sso_auth("202200000000", "your-password")

# 2. 查询 2025-1 学期课表
courses = ems_get_course_schedule(cookies, year=2025, term=1)
for course in courses:
		print(course["name"], course["weeks"])
```

如果你在 Agent 或自动化脚本中使用，也可以直接 import `skills/scripts` 里的函数，以获得与 CLI 一致的体验。

## 📘 进阶小贴士
- 🌀 **Token 压缩**：`--compressed` 会对 Cookie 进行 gzip+Base64 的体积压缩，适合跨系统传输或 Agent 上下文内使用。
- 🧱 **配额与风控**：统一身份认证存在防刷限制，请合理设置调用频率；若被锁定通常 24h 自动恢复。
- 📤 **PDF 成绩解析**：`xtu-transcript` 会调用 `pdfplumber`，需确保系统支持 PDF 渲染依赖。

## 🤲 贡献与支持
欢迎通过 Issue / PR 提交 BUG、功能或高校生态相关的技能脚本：
1. Fork & 修改。
2. 本地运行 `python -m build` 验证打包是否通过。
3. 发起 PR 并描述变更与测试情况。

## ⚠️ 使用须知与免责
- 本项目仅供学习与科研交流，不保证对所有院系/时间段持续可用。
- 使用者需自行确保调用行为符合校方与国家相关法规及隐私政策。
- 对因使用本项目导致的账号封禁、数据泄露或任意直接/间接损失，维护者不承担任何责任。
- 继续使用即视为同意上述条款与 MIT License。

## 📄 开源协议
本项目遵循 MIT License（详见 LICENSE）。你可以自由复制、分发、商用及二次开发，但需保留版权声明并在衍生作品中附带同样的许可文本。🙏

## 💬 联系我们
- Maintainer: LeoTan2004
- Issue Tracker: https://github.com/LeoTan2004/XTU-EMS-API/issues

如果本文档未覆盖你的使用场景，欢迎提 Issue 交流，我们很乐意继续完善！🎉
