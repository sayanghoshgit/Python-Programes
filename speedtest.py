import threading
import tkinter as tk
from tkinter import ttk
import subprocess
import time

speedtest_threads = []
speedtest_running = False

# Function to run a download, upload, or both tests
def run_speedtest(thread_num, mode):
    while True:
        if not speedtest_running:
            break

        # Run the speedtest-cli command for download, upload, or both
        if mode == "download":
            result = subprocess.run(['speedtest-cli', '--no-upload', '--simple'], capture_output=True, text=True)
        elif mode == "upload":
            result = subprocess.run(['speedtest-cli', '--no-download', '--simple'], capture_output=True, text=True)
        else:
            result = subprocess.run(['speedtest-cli', '--simple'], capture_output=True, text=True)

        log_text = f"Thread-{thread_num} | {mode.capitalize()} Test | {result.stdout}\n"
        log_display.insert(tk.END, log_text)
        log_display.see(tk.END)
        time.sleep(5)

def start_speedtests():
    global speedtest_threads, speedtest_running
    speedtest_running = True
    num_threads = int(thread_entry.get())
    mode = mode_var.get()

    for i in range(num_threads):
        thread = threading.Thread(target=run_speedtest, args=(i + 1, mode))
        speedtest_threads.append(thread)
        thread.start()

    log_display.insert(tk.END, f"{mode.capitalize()} Speed Tests Started\n")

def stop_speedtests():
    global speedtest_running
    speedtest_running = False
    for thread in speedtest_threads:
        thread.join()

    log_display.insert(tk.END, "Speed Tests Stopped\n")

# Create the GUI
root = tk.Tk()
root.title("Stresser Utility By Python")

frame = ttk.Frame(root, padding="20")
frame.grid(row=0, column=0)

label_thread = ttk.Label(frame, text="Number of SpeedTest Threads:")
label_thread.grid(row=0, column=0)

thread_entry = ttk.Entry(frame, width=10)
thread_entry.grid(row=0, column=1)

label_mode = ttk.Label(frame, text="Select Test Mode:")
label_mode.grid(row=1, column=0)

mode_var = tk.StringVar(value="download")
mode_dropdown = ttk.Combobox(frame, textvariable=mode_var, values=["download", "upload", "both"], state="readonly")
mode_dropdown.grid(row=1, column=1)

start_button = ttk.Button(frame, text="Start Speed Tests", command=start_speedtests)
start_button.grid(row=2, column=0, columnspan=2, pady=5)

stop_speed_button = ttk.Button(frame, text="Stop Speed Tests", command=stop_speedtests)
stop_speed_button.grid(row=3, column=0, columnspan=2, pady=5)

log_display = tk.Text(root, height=15, width=60)
log_display.grid(row=4, column=0, padx=10, pady=10, columnspan=2)

root.mainloop()

