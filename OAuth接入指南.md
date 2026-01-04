# OAuth接入指南

使用OAuth接入应用，由如下三步完成接入：

1. **第一步**：通过身份认证，获取code
2. **第二步**：根据code获取access_token
3. **第三步**：根据access_token获取用户信息

------

## 第一步：通过身份认证，获取code

通过构造授权认证url并请求将跳转至用户身份授权地址，进行身份认证。参考链接如下：

HTTP

```
https://account.zime.edu.cn/cas/oauth2.0/authorize?response_type=code&client_id=APPKEY&redirect_uri=REDIRECT_URI
```

> **注意**：链接回调 `redirect_uri`，应当使用 https 链接来确保授权 code 的安全性

- **接口地址**：`https://account.zime.edu.cn/cas/oauth2.0/authorize`
- **请求方式**：GET

### 参数说明

| **参数**        | **是否必须** | **说明**                                                     |
| --------------- | ------------ | ------------------------------------------------------------ |
| `client_id`     | 是           | 应用审核通过后返回的 `app_key`                               |
| `redirect_uri`  | 是           | 回调地址，应用接入第二步中填写的请求地址                     |
| `response_type` | 是           | 返回类型，填写为 `code`                                      |
| `state`         | 否           | 重定向后会带上 state 参数，开发者可以填写 a-zA-Z0-9 的参数值，最多128字节 |

### 下图为用户授权界面

*(此处为统一身份认证登录界面截图，显示用户名/密码登录框及二维码)*

当输入正确的口令认证通过后，页面将跳转至：

redirect_uri?code=CODE&state=STATE

> **注意**：为授权安全，code只能使用一次，并且有效期为10秒，未被使用将自动过期

------

## 第二步：根据code获取access_token

这里注意，用 code 获取的 access_token 与 RestFul API 中使用的 token 不同。构造获取 access_token 链接参考如下：

HTTP

```
https://account.zime.edu.cn/cas/oauth2.0/accessToken?client_id=APPID&client_secret=SECRET&code=CODE&redirect_uri=REDIRECT_URI
```

- **接口地址**：`https://account.zime.edu.cn/cas/oauth2.0/accessToken`
- **请求方式**：GET

### 参数说明

| **参数**        | **是否必须** | **说明**                                 |
| --------------- | ------------ | ---------------------------------------- |
| `client_id`     | 是           | 应用审核通过后返回的 `app_key`           |
| `client_secret` | 是           | 应用审核通过后返回的 `app_secret`        |
| `redirect_uri`  | 是           | 回调地址，应用接入第二步中填写的请求地址 |
| `code`          | 是           | 填写第一步获取的 `code`                  |

### 返回说明

**正确时返回的 JSON 数据包如下：**

JSON

```
{
  "access_token": "ACCESS_TOKEN",
  "expires_in": 7200
}
```

| **参数**       | **说明**                                      |
| -------------- | --------------------------------------------- |
| `access_token` | 用户鉴权接口凭证，用以获取身份信息            |
| `expires_in`   | `access_token` 接口调用凭证，时间（单位：秒） |

**错误时返回的 JSON 数据包如下：**

JSON

```
{
  "errorcode": "ERRORCODE",
  "errormsg": "ERRORMSG"
}
```

------

## 第三步：根据access_token获取用户信息

第三步：通过 access_token，构造获取身份信息链接请求。参考链接如下：

HTTP

```
https://account.zime.edu.cn/cas/oauth2.0/profile?access_token=ACCESS_TOKEN
```

- **接口地址**：`https://account.zime.edu.cn/cas/oauth2.0/profile`
- **请求方式**：GET

### 参数说明

| **参数**       | **是否必须** | **说明**         |
| -------------- | ------------ | ---------------- |
| `access_token` | 是           | 用户鉴权接口凭证 |

### 返回说明

**正确时返回的 JSON 数据包如下：**

JSON

```
{
  "id": "testuser",
  "attributes": {
    "CODE": "testuser",
    "DWPF": "XX",
    "XM": "testuser",
    "ZJHM": "XX"
  }
}
```

**错误时返回的 JSON 数据包如下：**

JSON

```
{
  "errorcode": "ERRORCODE",
  "errormsg": "ERRORMSG"
}
```