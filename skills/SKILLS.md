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
python scripts/sso_login.py --username your_username --password your_password
```