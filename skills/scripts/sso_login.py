from requests import Session, cookies


def rsa_encrypt(encrypt_exponent: int, modulus: int, plaintext: str) -> str:
    """
    使用 RSA 公钥加密算法对明文进行加密并返回十六进制密文。

    :param encrypt_exponent: RSA 公钥指数 e。
    :type encrypt_exponent: int
    :param modulus: RSA 模数 n，来自服务端发布的公钥。
    :type modulus: int
    :param plaintext: 待加密的明文字符串。
    :type plaintext: str
    :return: 加密后的密文，使用十六进制字符串表示。
    :rtype: str
    """
    # 将明文字符串转换为整数
    message_int = int.from_bytes(plaintext.encode("utf-8"), "big")

    # 计算密文 c = m^e mod n
    ciphertext_int = pow(message_int, encrypt_exponent, modulus)

    # 将密文整数转换为十六进制字符串
    ciphertext_hex = hex(ciphertext_int)[2:]  # 去掉前缀'0x'

    return ciphertext_hex


def get_config():
    """
    提供门户 SSO 登录流程所需的固定配置项。

    :return: 包含登录入口、RSA 公钥接口及后续跳转地址前缀的配置字典。
    :rtype: dict
    """

    return {
        "login_url": "https://portal2020.xtu.edu.cn/cas/login?service=https%3A%2F%2Fportal2020.xtu.edu.cn%2Fapplication-center",
        "key_url": "https://portal2020.xtu.edu.cn/cas/v2/getPubKey",
        "login_success_url_prefix": "https://portal2020.xtu.edu.cn/application-center",
        "modify_password_url_prefix": "https://portal2020.xtu.edu.cn/im/securitycenter/modifyPwd/index.zf",
    }


def sso_auth(username: str, password: str) -> cookies.RequestsCookieJar:
    """
    执行门户 SSO 登录流程并返回登录成功后的 Cookie 集合。

    :param username: 学号或工号形式的 SSO 用户名。
    :type username: str
    :param password: 用户密码，在提交前会通过 RSA 加密。
    :type password: str
    :return: 登录成功后从会话中提取的 Cookie 集合。
    :rtype: cookies.RequestsCookieJar
    :raises Exception: 当 RSA 公钥、登录页面或重定向地址异常时抛出具体异常信息。
    """
    config = get_config()
    login_url = config["login_url"]
    key_url = config["key_url"]
    login_success_url_prefix = config["login_success_url_prefix"]
    modify_password_url_prefix = config["modify_password_url_prefix"]
    redirect_url = ""

    with Session() as session:
        with session.get(key_url) as response:
            if response.status_code != 200:
                raise Exception("CAS Key Service was unavailable")
            key_pair = response.json()
            key_pair = {
                "modulus": int(key_pair["modulus"], 16),
                "public_exponent": int(key_pair["exponent"], 16),
            }
        with session.get(login_url) as response:
            if response.status_code != 200:
                raise Exception("CAS Login Page was unavailable")
            # 从html中提取execution值，一个input标签，name="execution"，value="xxxx"
            html = response.text
            start_index = html.index('name="execution" value="') + len(
                'name="execution" value="'
            )
            end_index = html.index('"', start_index)
            if not (0 < start_index < end_index):
                raise Exception("CAS Login Page was unavailable")
            execution = html[start_index:end_index]
        encrypted_password = rsa_encrypt(
            key_pair["public_exponent"], key_pair["modulus"], password
        )
        payload = {
            "username": username,
            "password": encrypted_password,
            "execution": execution,
            "_eventId": "submit",
            "authcode": "",
            "mobileCode": "",
        }
        # 执行登录请求
        with session.post(
            login_url,
            data=payload,
            allow_redirects=False,
        ) as response:
            if response.status_code == 302 and "Location" in response.headers:
                redirect_url = response.headers["Location"] or ""
            elif response.status_code == 200:
                raise Exception("Invalid username or password")
            elif response.status_code == 403:
                raise Exception("Account disabled")
            else:

                raise Exception("login failed")
        # 判断重定向URL
        if redirect_url.startswith(modify_password_url_prefix):
            raise Exception(username, "Please change password first.")
        elif not redirect_url.startswith(login_success_url_prefix):
            raise Exception("ticket URL not found")
        # 访问ticket_url，完成登录
        with session.get(
            redirect_url,
        ) as response:
            if response.status_code == 200:
                return session.cookies
            else:
                raise Exception("login failed")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SSO Login Script")
    parser.add_argument(
        "--username", type=str, required=True, help="Username for SSO login"
    )
    parser.add_argument(
        "--password", type=str, required=True, help="Password for SSO login"
    )
    parser.add_argument(
        "--compressed", action="store_true", help="Whether to use compressed token"
    )
    args = parser.parse_args()
    username = args.username
    password = args.password
    compressed = args.compressed
    token = sso_auth(username, password)
    import tokenizer
    token = tokenizer.serialize_token(token, compressed=compressed)
    print(token)
