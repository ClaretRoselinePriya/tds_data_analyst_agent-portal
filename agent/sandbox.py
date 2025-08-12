import os, sys, subprocess, venv
from typing import Tuple

class PyExecError(Exception):
    pass

def python_exec(code: str, workdir: str, timeout_sec: int = 40) -> Tuple[int,str,str]:
    code_path = os.path.join(workdir, "job.py")
    with open(code_path, "w", encoding="utf-8") as f:
        f.write(code)
    env = {"PYTHONHASHSEED":"0"}
    proc = subprocess.run([sys.executable, code_path], cwd=workdir, env=env,
                          capture_output=True, text=True, timeout=timeout_sec)
    return proc.returncode, proc.stdout, proc.stderr

ALLOW_PIP = {"pandas","numpy","matplotlib","duckdb","pdfplumber"}

def python_exec_with_venv(code: str, workdir: str, pkgs: list[str]|None=None, timeout_sec: int = 40):
    vdir = os.path.join(workdir, ".venv")
    venv.EnvBuilder(with_pip=True).create(vdir)
    pip = os.path.join(vdir, 'bin', 'pip') if os.name != 'nt' else os.path.join(vdir, 'Scripts', 'pip.exe')
    py  = os.path.join(vdir, 'bin', 'python') if os.name != 'nt' else os.path.join(vdir, 'Scripts', 'python.exe')
    if pkgs:
        safe = [p for p in pkgs if p.split('==')[0] in ALLOW_PIP]
        if safe:
            subprocess.run([pip, 'install', '--no-cache-dir', *safe], cwd=workdir, check=True, timeout=timeout_sec)
    code_path = os.path.join(workdir, 'job.py')
    open(code_path,'w',encoding='utf-8').write(code)
    proc = subprocess.run([py, code_path], cwd=workdir, capture_output=True, text=True, timeout=timeout_sec)
    return proc.returncode, proc.stdout, proc.stderr
