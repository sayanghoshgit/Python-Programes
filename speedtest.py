import threading
import tkinter as tk
from tkinter import ttk
import subprocess
import time

speedtest_threads = []
speedtest_running = False

def run_speedtest(thread_num):
    while True:
        if not speedtest_running:
            break
        result = subprocess.run(['speedtest-cli', '--simple'], capture_output=True, text=True)
        log_text = f"Thread-{thread_num} | {result.stdout}\n"
        log_display.insert(tk.END, log_text)
        log_display.see(tk.END)
        time.sleep(5)

def start_speedtests():
    global speedtest_threads, speedtest_running
    speedtest_running = True
    num_threads = int(thread_entry.get())

    for i in range(num_threads):
        thread = threading.Thread(target=run_speedtest, args=(i + 1,))
        speedtest_threads.append(thread)
        thread.start()

    log_display.insert(tk.END, "Speed Tests Started\n")

def stop_speedtests():
    global speedtest_running
    speedtest_running = False
    for thread in speedtest_threads:
        thread.join()

    log_display.insert(tk.END, "Speed Tests Stopped\n")

root = tk.Tk()
root.title("Stresser Utility By Sayan")

frame = ttk.Frame(root, padding="20")
frame.grid(row=0, column=0)

label_thread = ttk.Label(frame, text="Number of SpeedTest Threads:")
label_thread.grid(row=0, column=0)

thread_entry = ttk.Entry(frame, width=10)
thread_entry.grid(row=0, column=1)

start_speed_button = ttk.Button(frame, text="Start Speed Tests", command=start_speedtests)
start_speed_button.grid(row=1, column=0, pady=5)

stop_speed_button = ttk.Button(frame, text="Stop Speed Tests", command=stop_speedtests)
stop_speed_button.grid(row=1, column=1, pady=5)

log_display = tk.Text(root, height=10, width=50)
log_display.grid(row=1, column=0, padx=10, pady=10, columnspan=2)

root.mainloop()
