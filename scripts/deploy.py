# =============================================================================
# scripts/deploy.py —— 一键把本地改动发到云服务器
# =============================================================================
# 用法：
#   python scripts/deploy.py               # 前端 + 后端全量更新
#   python scripts/deploy.py --frontend    # 只更新前端
#   python scripts/deploy.py --backend     # 只更新后端
#
# 它做的事（按顺序）：
#   1. 本地构建前端（npm run build）→ 打包 dist
#   2. SSH 到服务器：git pull 拉最新代码
#   3. 上传 dist（dist 不进 git，所以单独传）
#   4. docker compose up -d --build（按需重启 api / web）
#   5. 健康检查，打印结果
#
# 前置：deploy/.deploy.env 里配好 SSH 连接信息（已被 gitignore）
# =============================================================================
import argparse
import os
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

import httpx
import paramiko

# Windows 控制台默认 GBK，先切成 UTF-8，否则中文/符号会 UnicodeEncodeError
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / "deploy" / ".deploy.env"
REMOTE_DIR = "/opt/straycat-platform"


def load_env() -> dict:
    if not ENV_FILE.exists():
        sys.exit(f"缺配置文件：{ENV_FILE}\n请复制 deploy/.deploy.env.example 后填写。")
    conf = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            conf[k.strip()] = v.strip()
    return conf


def step(msg: str) -> None:
    print(f"\n>> {msg}")


def ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def fail(msg: str) -> None:
    print(f"  [X]  {msg}")


def build_frontend() -> Path:
    """本地构建前端，返回 dist 目录"""
    step("构建前端（npm run build）")
    r = subprocess.run(
        ["npm", "run", "build"], cwd=ROOT / "web",
        capture_output=True, text=True, encoding="utf-8", errors="replace", shell=True,
    )
    if r.returncode != 0:
        fail("前端构建失败")
        print((r.stdout or "")[-1500:] + (r.stderr or "")[-1500:])
        sys.exit(1)
    dist = ROOT / "web" / "dist"
    ok(f"构建完成（{sum(1 for _ in dist.rglob('*') if _.is_file())} 个文件）")
    return dist


def pack_dir(src: Path) -> Path:
    """把目录打成一个 tar.gz"""
    tmp = Path(tempfile.gettempdir()) / f"_deploy_{int(time.time())}.tar.gz"
    with tarfile.open(tmp, "w:gz") as tar:
        tar.add(src, arcname="web/dist")
    return tmp


def ssh_connect(conf: dict) -> paramiko.SSHClient:
    step(f"连接服务器 {conf['SSH_HOST']}")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        conf["SSH_HOST"], username=conf.get("SSH_USER", "root"),
        password=conf["SSH_PASSWORD"], timeout=20,
    )
    ok("已连接")
    return client


def run_remote(client: paramiko.SSHClient, cmd: str, timeout: int = 1800) -> tuple[int, str]:
    _, out, err = client.exec_command(cmd, timeout=timeout)
    text = out.read().decode("utf-8", "ignore") + err.read().decode("utf-8", "ignore")
    return out.channel.recv_exit_status(), text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontend", action="store_true", help="只更新前端")
    parser.add_argument("--backend", action="store_true", help="只更新后端")
    args = parser.parse_args()
    do_front = args.frontend or not args.backend
    do_back = args.backend or not args.frontend

    conf = load_env()
    started = time.time()

    dist = build_frontend() if do_front else None
    client = ssh_connect(conf)

    # 1) 拉代码
    if do_back:
        step("服务器拉取最新代码（git pull）")
        code, text = run_remote(client, f"cd {REMOTE_DIR} && git pull 2>&1 | tail -5")
        print("  " + text.replace("\n", "\n  ").strip())
        if code != 0:
            fail("git pull 失败（可能有本地改动冲突）")
        else:
            ok("代码已更新")

    # 2) 上传前端
    if do_front:
        step("上传前端 dist")
        archive = pack_dir(dist)
        sftp = client.open_sftp()
        sftp.put(str(archive), "/tmp/_dist.tar.gz")
        sftp.close()
        archive.unlink(missing_ok=True)
        code, text = run_remote(client, f"cd {REMOTE_DIR} && rm -rf web/dist && tar -xzf /tmp/_dist.tar.gz && ls web/dist | head -3")
        ok("前端已更新") if code == 0 else fail(text[-300:])

    # 3) 重启/重建容器
    step("应用改动（docker compose up -d --build）")
    services = []
    if do_back:
        services.append("api")
    if do_front:
        services.append("web")
    cmd = f"cd {REMOTE_DIR}/deploy && docker compose up -d --build {' '.join(services)} 2>&1 | tail -8"
    code, text = run_remote(client, cmd, timeout=2400)
    print("  " + text.replace("\n", "\n  ").strip())
    ok("容器已更新") if code == 0 else fail("compose 失败，看上面输出")

    # 4) 健康检查
    step("健康检查")
    base = f"http://{conf['SSH_HOST']}:{conf.get('HOST_PORT', '8080')}"
    for path in ("/health", "/api/v1/contents?page_size=1"):
        last = ""
        for attempt in range(20):           # 最多等 60 秒
            try:
                r = httpx.get(base + path, timeout=10)
                if r.status_code == 200:
                    ok(f"{path} -> 200")
                    last = "ok"
                    break
                last = str(r.status_code)
            except Exception as exc:  # noqa: BLE001
                last = type(exc).__name__
            time.sleep(3)
        if last != "ok":
            fail(f"{path} -> {last}（60 秒内未就绪，看 docker compose logs api）")

    client.close()
    print(f"\n完成，用时 {time.time() - started:.0f} 秒 -> {base}")


if __name__ == "__main__":
    main()
