import os
import subprocess
import sys
import json

shell = os.environ["SHELL"]
terminal = "kitty"

print(f"[DEBUG] PATH: {os.environ.get('PATH')}")
print(f"[DEBUG] SHELL: {shell}")

def get_hyprland_windows():
    try:
        result = subprocess.check_output(["hyprctl", "clients", "-j"]).decode()
        return json.loads(result)
    except:
        return []
        
def main():
    argv = sys.argv
    if len(argv) == 1:
        call_fzf()
    else:
        if argv[1] == "picker":
            run_plugins_picker(" ".join(argv[2:]))
        elif argv[1] == "run":
            run_plugins(" ".join(argv[2:]))

def call_fzf():
    path = os.path.realpath(__file__)
    cmd = [
        terminal,
        "--class",
        "fzfmenu",
        "-e",
        "fzf",
        "--color=bg+:#363A4F,spinner:#F4DBD6,hl:#ED8796",
        "--color=fg:#CAD3F5,header:#ED8796,info:#C6A0F6,pointer:#F4DBD6",
        "--color=marker:#B7BDF8,fg+:#CAD3F5,prompt:#C6A0F6,hl+:#ED8796",
        "--color=selected-bg:#494D64,border:#363A4F,label:#CAD3F5",

        f"--bind 'start,change:reload:python {path} picker {{q}}'",
        #f"--bind 'enter:execute(touch /tmp/fzf.lock && python {path} run {{}} && rm /tmp/fzf.lock && sleep 2)+abort'"
        f"--bind 'enter:execute(touch /tmp/fzf.lock && setsid nohup python {path} run {{}} >/dev/null 2>&1 & rm /tmp/fzf.lock && sleep 1)+abort'"
    ]

    subprocess.call(
        " ".join(cmd),
        shell=True,
        stderr=subprocess.STDOUT  # 显示错误输出
    )

def run_plugins(output: str):
    if output.startswith("kl "):
        killer_runner(output)
    elif output.startswith("wd "):
        window_jump_runner(output)
    elif output.startswith("hs "):
        history_runner(output)
    else:
        open_application_runner(output)

def open_application_runner(output: str):
    desktop = output.split(" ")[-1]
    print(f"[DEBUG] 尝试打开: {desktop}")  # 调试信息

    if not os.path.exists(desktop):
        subprocess.call(f"dex {desktop}", shell=True)
        print(f"[ERROR] 文件不存在: {desktop}")
        return
        
    try:
        # 尝试直接调用 gtk-launch（更可靠）
        subprocess.call(["gtk-launch", desktop.split("/")[-1].replace(".desktop", "")])
        # 或保留原 dex 调用
        # subprocess.call(["dex", desktop])
    except Exception as e:
        print(f"[ERROR] 启动失败: {e}")

   # if os.path.exists(desktop):
    #    subprocess.call(f"dex {desktop}", shell=True)

def window_jump_runner(output: str):
    addr = output.split(" ")[-1]
    subprocess.call(["hyprctl", "dispatch", "focuswindow", f"address:{addr}"])

def run_plugins_picker(input: str):
    if input.startswith("wd "):
        window_jump_picker(input)
    elif input.startswith("kl "):
        killer_picker(input)
    elif input.startswith("hs "):
        history_picker(input)
    else:
        open_application_picker(input)

def window_jump_picker(_):
    windows = get_hyprland_windows()
    for win in windows:
        print(f"wd {win['title']} {win['address']}")

def open_application_picker_by_path(path: str):
    output = (
        subprocess.check_output(f"fd -a .desktop {path}", shell=True).strip().decode()
    )
    for path in output.splitlines():
        if no_display_is_true(path):
            continue
        name = get_name_by_path(path)
        if name is not None:
            print(name + " " + path)

def open_application_picker(_):
    open_application_picker_by_path("/usr/share/applications/")
    open_application_picker_by_path(os.path.expanduser("~/Desktop/"))

def no_display_is_true(path: str):
    with open(path, "r") as f:
        for line in f.readlines():
            if line.startswith("NoDisplay=true"):
                return True
    return False

def get_name_by_path(path: str):
    with open(path, "r") as f:
        for line in f.readlines():
            if line.startswith("Name="):
                return line.removeprefix("Name=").strip()

def killer_picker(input: str):
    input = input.removeprefix("kl ")
    if len(input) == 0:
        return
    output = subprocess.check_output(f"pgrep -fa {input}", shell=True).strip().decode()
    path = os.path.realpath(__file__)
    for line in output.splitlines():
        if path in line:
            continue
        print("kl " + line)

def killer_runner(output: str):
    pid = output.removeprefix("kl ").split(" ")[0]
    subprocess.call([shell, "-c", f"kill -9 {pid}"])

def history_picker(_):
    output = subprocess.check_output([shell, "-c", "history"]).strip().decode()
    for line in set(output.splitlines()):
        print("hs " + line)

def history_runner(output: str):
    cmd = output.removeprefix("hs ")
    subprocess.call(f"nohup {cmd} > /dev/null 2>&1 &", shell=True)

if __name__ == "__main__":
    main()
