# basex

终端编解码小工具：一种编码进，多种编码出，还能**猜**一段乱码原本是什么编码。

纯 Python 标准库，纯本地运行，不联网。

## 安装

```bash
git clone https://github.com/ljiang9/basex.git
cd basex
# 直接用，无需安装
python3 -m basex encode base64 "hello"
```

## 用法

```bash
# 编码
basex encode base64 "hello"        # aGVsbG8=
basex encode hex "中文"            # e4b8ade69687
basex encode url "a b&c"           # a%20b%26c
basex encode html "<b>hi</b>"      # &lt;b&gt;hi&lt;/b&gt;
basex encode unicode-escape "中文" # \u4e2d\u6587
basex encode rot13 "hello"         # uryyb

# 解码
basex decode base64 aGVsbG8=       # hello
basex decode base64url aGVsbG8     # hello（可省略 padding）

# 从管道读
echo "hello" | basex encode base64 --stdin

# 猜编码：把输入喂给所有解码器，列出能产生可打印文本的
basex guess "aGVsbG8="
#   [base64]
#     hello
basex guess "48656c6c6f" --json
```

支持的编码：`base64` / `base64url` / `hex` / `url` / `html` / `unicode-escape` / `rot13`。

解码失败时输出中文错误并 exit 1，不抛 traceback：

```bash
$ basex decode base64 "!!!"
error: 无法用 base64 解码输入：Non-base64 digit found
$ echo $?
1
```

## 关于 rot13

rot13 只是字母替换的**混淆**手段，不是加密，没有任何安全性。
别拿它藏密码。

## 关于 guess

`guess` 是启发式的：它把输入丢给每个解码器，
只保留"解出来是可打印文本且与输入不同"的结果。
短字符串可能同时命中多个编码（比如纯数字串既是合法 hex
又是合法 base64url），长一点的输入通常只剩一个合理解。
它帮你缩小范围，不替你做决定。

## 已知局限

- `unicode-escape` 解码用的是 Python 的 codec 语义，
  `\x41` 这类转义也会被展开（和 JSON 的 `\uXXXX` 不完全等价）。
- `guess` 对二进制/非文本输入无意义；只处理文本。
- HTML 编码是转义（escape）不是 URL 编码，别和 `url` 搞混。
