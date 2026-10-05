#!/usr/bin/env python3
"""basex — 终端编解码小工具：多种编码互转 + 智能猜测。

纯标准库，纯本地运行。
"""

import argparse
import base64
import binascii
import codecs
import html
import json
import sys
import urllib.parse

VERSION = "0.1.0"

CODECS = ["base64", "base64url", "hex", "url", "html", "unicode-escape", "rot13"]


def _b(s: str) -> bytes:
    return s.encode("utf-8")


def _s(b: bytes) -> str:
    return b.decode("utf-8")


def enc_base64(s: str) -> str:
    return _s(base64.b64encode(_b(s)))


def dec_base64(s: str) -> str:
    return _s(base64.b64decode(s.strip(), validate=True))


def enc_base64url(s: str) -> str:
    return _s(base64.urlsafe_b64encode(_b(s)))


def dec_base64url(s: str) -> str:
    s = s.strip()
    # 补齐 padding（urlsafe 常省略末尾的 =）
    s += "=" * (-len(s) % 4)
    return _s(base64.urlsafe_b64decode(s))


def enc_hex(s: str) -> str:
    return _b(s).hex()


def dec_hex(s: str) -> str:
    return _s(bytes.fromhex(s.strip().replace(" ", "")))


def enc_url(s: str) -> str:
    return urllib.parse.quote(s, safe="")


def dec_url(s: str) -> str:
    return urllib.parse.unquote(s.strip())


def enc_html(s: str) -> str:
    return html.escape(s)


def dec_html(s: str) -> str:
    return html.unescape(s.strip())


def enc_unicode_escape(s: str) -> str:
    return s.encode("unicode_escape").decode("ascii")


def dec_unicode_escape(s: str) -> str:
    return codecs.decode(s.strip(), "unicode_escape")


def enc_rot13(s: str) -> str:
    return codecs.encode(s, "rot13")


def dec_rot13(s: str) -> str:
    return codecs.decode(s, "rot13")


ENCODERS = {
    "base64": enc_base64,
    "base64url": enc_base64url,
    "hex": enc_hex,
    "url": enc_url,
    "html": enc_html,
    "unicode-escape": enc_unicode_escape,
    "rot13": enc_rot13,
}

DECODERS = {
    "base64": dec_base64,
    "base64url": dec_base64url,
    "hex": dec_hex,
    "url": dec_url,
    "html": dec_html,
    "unicode-escape": dec_unicode_escape,
    "rot13": dec_rot13,
}


def is_printable(s: str) -> bool:
    """宽松的可打印判断：允许常见空白，拒绝控制字符和替换字符。"""
    if not s:
        return False
    if "\ufffd" in s:
        return False
    for ch in s:
        if ch in "\t\n\r":
            continue
        if ord(ch) < 0x20 or ord(ch) == 0x7F:
            return False
    return True


def guess(s: str) -> list[tuple[str, str]]:
    """对输入尝试所有解码器，返回产生可打印输出的 (codec, result)。"""
    hits = []
    for name in CODECS:
        try:
            out = DECODERS[name](s)
        except Exception:
            continue
        if is_printable(out) and out != s:
            hits.append((name, out))
    return hits


def read_input(args) -> str:
    if args.stdin:
        data = sys.stdin.read()
        return data.rstrip("\n")
    if args.text is not None:
        return args.text
    return ""


def cmd_encode(args) -> int:
    text = read_input(args)
    try:
        print(ENCODERS[args.codec](text))
    except Exception as e:
        print(f"error: 编码失败（{args.codec}）：{e}", file=sys.stderr)
        return 1
    return 0


def cmd_decode(args) -> int:
    text = read_input(args)
    try:
        print(DECODERS[args.codec](text))
    except (binascii.Error, ValueError, UnicodeDecodeError) as e:
        print(f"error: 无法用 {args.codec} 解码输入：{e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"error: 解码失败（{args.codec}）：{e}", file=sys.stderr)
        return 1
    return 0


def cmd_guess(args) -> int:
    text = read_input(args)
    if not text:
        print("error: 没有输入", file=sys.stderr)
        return 1
    hits = guess(text)
    if not hits:
        print("没有解码器能产生可打印结果。")
        return 1
    if args.json:
        print(json.dumps(
            [{"codec": c, "result": r} for c, r in hits],
            ensure_ascii=False, indent=2,
        ))
        return 0
    print(f"输入：{text}")
    print(f"命中 {len(hits)} 个可能的解码：\n")
    for codec, result in hits:
        shown = result if len(result) <= 200 else result[:200] + "…"
        print(f"  [{codec}]")
        print(f"    {shown}\n")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="basex",
        description="终端编解码小工具：encode/decode/guess，纯本地。",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    sub = p.add_subparsers(dest="cmd", required=True)

    for name in ("encode", "decode"):
        sp = sub.add_parser(name, help="编码" if name == "encode" else "解码")
        sp.add_argument("codec", choices=CODECS, help="编码方式")
        sp.add_argument("text", nargs="?", help="要处理的文本（省略则读 --stdin）")
        sp.add_argument("--stdin", action="store_true", help="从标准输入读取")

    gp = sub.add_parser("guess", help="猜测输入可能是哪种编码")
    gp.add_argument("text", nargs="?", help="要猜测的文本（省略则读 --stdin）")
    gp.add_argument("--stdin", action="store_true", help="从标准输入读取")
    gp.add_argument("--json", action="store_true", help="JSON 输出")

    args = p.parse_args(argv)
    if args.cmd == "encode":
        return cmd_encode(args)
    if args.cmd == "decode":
        return cmd_decode(args)
    return cmd_guess(args)


if __name__ == "__main__":
    sys.exit(main())
