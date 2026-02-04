---
name: XTU-API-SKILLS
description: XiangTan University API, You can use these skills to access various services of XiangTan University.
---

# 湘潭大学信息接入

## 身份认证

湘潭大学的信息系统包好多个子系统，每个子系统有独立的身份认证方式。同时我们也可以使用统一身份认证系统进行登录。

### 统一身份认证

需要提供账号密码进行登录，登录成功后会返回一个 token, 该 token 可用于后续的接口调用。

统一身份认证接口有防刷机制，请勿频繁调用，同时注意如果账号密码错误过多会被锁定，常规账号锁定时间为24小时，可以主动联系管理员。

可以执行下面的命令进行登录，登录成功后会在控制台中打印 token 信息：

```bash
python scripts/sso_login.py --username your_username --password your_password --compressed
```

参数说明：
| 参数名 | 说明 | 类型 | 必填 | 示例值 |
| ------------ | ------------ | ------ | ---- | -------------- |
| --username | 统一身份认证账号 | 字符串 | 是 | your_username |
| --password | 统一身份认证密码 | 字符串 | 是 | your_password |
| --compressed | 是否启用压缩 | 布尔 | 否 | |

### 通过SSO Token 获取教务系统授权

可以使用统一身份认证系统获取的 token 来访问教务系统。需要将 token 放入请求头中进行身份验证。

可以执行下面的命令进行登录，登录成功后会在控制台中打印教务系统的 cookies 信息：

```bash
python scripts/ems_auth.py --token your_token --compressed
```

参数说明：
| 参数名 | 说明 | 类型 | 必填 | 示例值 |
| ------------ | ------------ | ------ | ---- | ------------- |
| --token | 统一身份认证 token | 字符串 | 是 | your_token |
| --compressed | 是否启用压缩 | 布尔 | | 否 | |

## 获取个人信息

可以使用教务系统的 cookies 来获取个人信息。

可以执行下面的命令获取个人信息：

```bash
python scripts/student_info.py --token your_token --compressed
```

获取的信息会以 JSON 格式打印在控制台中。

```json
{
  "student_id": "202205561111",
  "name": "张三",
  "gender": "男",
  "birthday": "2004-01-01",
  "entrance_day": "2022-09-01",
  "major": "通信工程(00837)",
  "class": "2022通信工程3班",
  "college": "计算机学院●网络空间安全学院"
}
```

参数说明：
| 参数名 | 说明 | 类型 | 必填 | 示例值 |
| ------------ | ------------ | ------ | ---- | ------------- |
| --token | 教务系统 cookies | 字符串 | 是 | your_token |
| --compressed | 是否启用压缩 | 布尔 | 否 | |

## 获取教学日历

可以使用教务系统的 cookies 来获取教学日历信息。

主要包括学期开始时间、结束时间。
可以执行下面的命令获取教学日历信息：

```bash
python scripts/teaching_calendar.py --token your_token --compressed
```

获取的信息会以 JSON 格式打印在控制台中。

```json
{
  "term_id": "2025-2026-1",
  "start_date": "2025-09-01",
  "end_date": "2026-01-18"
}
```

参数说明：
| 参数名 | 说明 | 类型 | 必填 | 示例值 |
| ------------ | ------------ | ------ | ---- | ------------- |
| --token | 教务系统 cookies | 字符串 | 是 | your_token |
| --compressed | 是否启用压缩 | 布尔 | 否 | |

## 获取教室空满情况

可以使用教务系统的 cookies 来获取教室空满情况。

可以执行下面的命令获取教室空满情况：

```bash
python scripts/classroom_availability.py --token your_token --compressed --year 2025 --term 1 --weeks 1 2 3 --day-of-week 1 --sections 1 2 3
```

获取的信息会以 JSON 格式打印在控制台中。

```json
["化工原理楼-北106", "一教楼-102", "一教楼-114"]
```

参数说明：
| 参数名 | 说明 | 类型 | 必填 | 示例值 |
| ------------ | -------- | -------- | ---- | ------ |
| --year | 学年 | 整数 | 是 | 2025 |
| --term | 学期 | 整数 | 是 | 1 |
| --weeks | 周次列表 | 整数列表 | 是 | 1 2 3 |
| --day-of-week | 星期几 | 整数 | 是 | 1 |
| --sections | 节次列表 | 整数列表 | 是 | 1 2 3 |
