import subprocess
import platform
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, scrolledtext

param = "-n" if platform.system().lower() == "windows" else "-c"

hosts = []
host_stats = {}
monitoring = False
monitor_thread = None
stop_event = threading.Event()
log_file = "uptime_log.txt"

theme = {
    "bg": "#282c34",
    "text_bg": "#3c3f58",
    "text_fg": "#FFFFFF",
    "btn_bg": "#61afef",
    "btn_fg": "#282c34",
    "btn_hover_bg": "#5299e6",
    "entry_bg": "#3c3f58",
    "entry_fg": "#e8e8e8",
    "label_fg": "#abb2bf"
}

def ping_host(host):
    try:
        output = subprocess.check_output(["ping", param, "1", host], universal_newlines=True)
        latency = None
        if platform.system().lower() == "windows":
            import re
            match = re.search(r"Average = (\d+)ms", output)
            if match:
                latency = int(match.group(1))
        else:
            for line in output.split("\n"):
                if "time=" in line:
                    latency = float(line.split("time=")[-1].split(" ")[0].replace("ms", "").strip())
                    break
        return True, latency
    except subprocess.CalledProcessError:
        return False, None

def log_status(host, status, latency, output_area, summary_text):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status_text = "UP" if status else "DOWN"
    latency_text = f"{latency:.2f} ms" if latency is not None else "N/A"

    stat = host_stats[host]
    stat['total'] += 1

    if status:
        stat['up'] += 1
        stat['current_down'] = False
        if latency is not None:
            stat['latency_sum'] += latency
            stat['latency_count'] += 1
            if stat['min_latency'] is None or latency < stat['min_latency']:
                stat['min_latency'] = latency
            if stat['max_latency'] is None or latency > stat['max_latency']:
                stat['max_latency'] = latency
        if stat.get('down_start_time'):
            downtime_duration = (datetime.now() - stat['down_start_time']).total_seconds()
            if downtime_duration > stat['longest_downtime']:
                stat['longest_downtime'] = downtime_duration
            stat['down_start_time'] = None
    else:
        stat['down'] += 1
        if not stat['current_down']:
            stat['downtime_count'] += 1
            stat['down_start_time'] = datetime.now()
            stat['current_down'] = True

    uptime_percent = (stat['up'] / stat['total']) * 100
    avg_latency = (stat['latency_sum'] / stat['latency_count']) if stat['latency_count'] else 0

    message = (f"[{timestamp}] {host} is {status_text} | "
               f"Latency: {latency_text} | Uptime: {uptime_percent:.1f}% | "
               f"Avg Latency: {avg_latency:.2f} ms")

    output_area.insert(tk.END, message + "\n")
    output_area.see(tk.END)

    with open(log_file, "a") as f:
        f.write(message + "\n")

    update_summary_panel(summary_text)

def update_summary_panel(summary_text):
    summary_text.config(state=tk.NORMAL)
    summary_text.delete(1.0, tk.END)
    summary_text.insert(tk.END, "Host Summary:\n")
    summary_text.insert(tk.END, "-" * 40 + "\n")
    for host, stat in host_stats.items():
        if stat["total"] == 0:
            continue
        uptime_percent = (stat['up'] / stat['total']) * 100
        avg_latency = (stat['latency_sum'] / stat['latency_count']) if stat['latency_count'] else 0
        min_latency = stat['min_latency'] if stat['min_latency'] is not None else 0
        max_latency = stat['max_latency'] if stat['max_latency'] is not None else 0
        downtime_count = stat['downtime_count']
        longest_down = stat['longest_downtime']
        current_status = "UP" if not stat.get('current_down', False) else "DOWN"
        summary = (f"{host}\n"
                   f"  Checks: {stat['total']}\n"
                   f"  Uptime: {uptime_percent:.1f}%\n"
                   f"  Current Status: {current_status}\n"
                   f"  Downtime Count: {downtime_count}\n"
                   f"  Longest Downtime: {longest_down:.1f} sec\n"
                   f"  Avg Latency: {avg_latency:.2f} ms\n"
                   f"  Min Latency: {min_latency:.2f} ms\n"
                   f"  Max Latency: {max_latency:.2f} ms\n\n")
        summary_text.insert(tk.END, summary)
    summary_text.config(state=tk.DISABLED)

def monitor_hosts(output_area, summary_text, interval):
    global monitoring
    while not stop_event.is_set():
        for host in hosts:
            if stop_event.is_set():
                break
            status, latency = ping_host(host)
            log_status(host, status, latency, output_area, summary_text)
        if stop_event.wait(interval):
            break
    monitoring = False

def start_monitoring(output_area, summary_text, interval_var, start_btn, stop_btn, interval_entry):
    global monitoring, monitor_thread, stop_event
    if not hosts:
        messagebox.showwarning("No Hosts", "Please add at least one host to monitor.")
        return

    if monitoring:
        messagebox.showinfo("Monitoring", "Monitoring is already running.")
        return

    try:
        interval = float(interval_var.get())
        if interval < 0.1:
            messagebox.showwarning("Invalid Interval", "Interval must be at least 0.1 seconds.")
            return
    except ValueError:
        messagebox.showwarning("Invalid Interval", "Please enter a valid number for the interval.")
        return

    stop_event.clear()
    monitoring = True
    start_btn.config(state=tk.DISABLED)
    interval_entry.config(state=tk.DISABLED)
    stop_btn.config(state=tk.NORMAL)

    monitor_thread = threading.Thread(target=monitor_hosts, args=(output_area, summary_text, interval))
    monitor_thread.daemon = True
    monitor_thread.start()

def stop_monitoring(start_btn=None, stop_btn=None, interval_entry=None):
    global monitoring, stop_event
    if not monitoring:
        return
    stop_event.set()
    monitoring = False
    if start_btn:
        start_btn.config(state=tk.NORMAL)
    if stop_btn:
        stop_btn.config(state=tk.DISABLED)
    if interval_entry:
        interval_entry.config(state=tk.NORMAL)

def add_host(entry, listbox, summary_text):
    host = entry.get().strip()
    if host and host not in hosts:
        hosts.append(host)
        host_stats[host] = {
            "total": 0,
            "up": 0,
            "down": 0,
            "latency_sum": 0.0,
            "latency_count": 0,
            "min_latency": None,
            "max_latency": None,
            "downtime_count": 0,
            "longest_downtime": 0,
            "down_start_time": None,
            "current_down": False
        }
        listbox.insert(tk.END, host)
        update_summary_panel(summary_text)
    entry.delete(0, tk.END)

def remove_selected_host(listbox, summary_text):
    selected = listbox.curselection()
    if selected:
        index = selected[0]
        host = listbox.get(index)
        hosts.remove(host)
        del host_stats[host]
        listbox.delete(index)
        update_summary_panel(summary_text)

def style_button(btn):
    btn.config(
        bg=theme["btn_bg"],
        fg=theme["btn_fg"],
        relief=tk.FLAT,
        bd=0,
        highlightthickness=0,
        padx=15,
        pady=10,
        font=("Segoe UI", 12, "bold"),
        cursor="hand2",
        activebackground=theme["btn_hover_bg"],
        activeforeground=theme["btn_fg"]
    )
    def on_enter(e):
        btn['background'] = theme["btn_hover_bg"]
    def on_leave(e):
        btn['background'] = theme["btn_bg"]
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

def build_gui():
    root = tk.Tk()
    root.title("Network Uptime Checker By Sayan")
    root.configure(bg=theme["bg"])
    root.geometry("980x640")

    left_frame = tk.Frame(root, bg=theme["bg"])
    left_frame.pack(side=tk.LEFT, padx=15, pady=15, fill=tk.BOTH, expand=True)

    right_frame = tk.Frame(root, bg=theme["bg"])
    right_frame.pack(side=tk.RIGHT, padx=15, pady=15, fill=tk.Y)

    tk.Label(left_frame, text="Host:", bg=theme["bg"], fg=theme["label_fg"],
             font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="e", pady=6)

    host_entry = tk.Entry(left_frame, bg=theme["entry_bg"], fg=theme["entry_fg"],
                          font=("Segoe UI", 12), relief=tk.FLAT,
                          highlightthickness=0, borderwidth=0)
    host_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=6)
    left_frame.grid_columnconfigure(1, weight=1)

    add_btn = tk.Button(left_frame, text="Add", command=lambda: add_host(host_entry, host_listbox, summary_text))
    add_btn.grid(row=0, column=2, padx=6, pady=6)
    style_button(add_btn)

    host_listbox = tk.Listbox(left_frame, height=7, width=45, bg=theme["text_bg"], fg=theme["text_fg"],
                              font=("Segoe UI", 12), highlightthickness=0, borderwidth=0, relief=tk.FLAT)
    host_listbox.grid(row=1, column=0, columnspan=3, pady=8, sticky="ew")

    remove_btn = tk.Button(left_frame, text="Remove Selected", command=lambda: remove_selected_host(host_listbox, summary_text))
    remove_btn.grid(row=2, column=0, columnspan=3, pady=6)
    style_button(remove_btn)

    output_area = scrolledtext.ScrolledText(
        left_frame,
        width=75,
        height=24,
        bg=theme["text_bg"],
        fg=theme["text_fg"],
        font=("Courier New", 11),
        relief=tk.FLAT,
        highlightthickness=0,
        borderwidth=0
    )
    output_area.grid(row=3, column=0, columnspan=3, pady=10, sticky="nsew")
    left_frame.grid_rowconfigure(3, weight=1)

    interval_label = tk.Label(left_frame, text="Ping Interval (sec):", bg=theme["bg"], fg=theme["label_fg"],
                              font=("Segoe UI", 12))
    interval_label.grid(row=4, column=0, sticky="e", pady=10)

    interval_var = tk.StringVar(value="1.0")
    interval_entry = tk.Entry(left_frame, bg=theme["entry_bg"], fg=theme["entry_fg"],
                              font=("Segoe UI", 12), relief=tk.FLAT, width=8,
                              textvariable=interval_var, borderwidth=0, highlightthickness=0)
    interval_entry.grid(row=4, column=1, sticky="w", pady=10, padx=6)

    start_btn = tk.Button(left_frame, text="Start Monitoring",
                          command=lambda: start_monitoring(output_area, summary_text, interval_var, start_btn, stop_btn, interval_entry))
    start_btn.grid(row=5, column=0, pady=8, sticky="ew")
    style_button(start_btn)

    stop_btn = tk.Button(left_frame, text="Stop Monitoring",
                         command=lambda: stop_monitoring(start_btn, stop_btn, interval_entry))
    stop_btn.grid(row=5, column=2, pady=8, sticky="ew")
    style_button(stop_btn)
    stop_btn.config(state=tk.DISABLED)

    summary_label = tk.Label(right_frame, text="Host Summary", bg=theme["bg"], fg=theme["label_fg"],
                             font=("Segoe UI", 14, "bold"))
    summary_label.pack(anchor="nw", pady=6)

    summary_text = scrolledtext.ScrolledText(right_frame, width=38, height=38, state=tk.DISABLED,
                                             bg=theme["text_bg"], fg=theme["text_fg"], font=("Courier New", 11),
                                             relief=tk.FLAT, highlightthickness=0, borderwidth=0)
    summary_text.pack(fill=tk.BOTH, expand=True)

    def on_close():
        stop_monitoring()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    build_gui()
