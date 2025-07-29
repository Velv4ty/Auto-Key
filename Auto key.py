import tkinter as tk
from tkinter import ttk
from pynput.keyboard import Key, Controller, Listener
import threading
import time
import json
import os

keyboard = Controller()
running = False
exit_program = False

listener_lock = threading.Lock()
listener = None
click_thread = None

CONFIG_FILE = "autokey_config.json"

def limit_entry_length(P):
    if len(P) > 5:
        return False
    return P.isdigit() or P == ""

def on_hotkey_keypress(event):
    if event.char.isalpha():
        hotkey_var.set(event.char.upper())
        return "break"

def toggle_repeat_mode():
    if repeat_mode_var.get() == "until":
        entry_repeat.configure(state="disabled")
    else:
        entry_repeat.configure(state="normal")

def change_toggle_key_from_string(key_str):
    key_str = key_str.strip().lower()
    special_keys = {
        "f1": Key.f1, "f2": Key.f2, "f3": Key.f3, "f4": Key.f4, "f5": Key.f5,
        "f6": Key.f6, "f7": Key.f7, "f8": Key.f8, "f9": Key.f9, "f10": Key.f10,
        "f11": Key.f11, "f12": Key.f12,
        "esc": Key.esc, "enter": Key.enter, "space": Key.space, "tab": Key.tab,
        "shift": Key.shift, "ctrl": Key.ctrl, "alt": Key.alt
    }
    if key_str in special_keys:
        return special_keys[key_str]
    elif len(key_str) == 1:
        return key_str
    else:
        return None

def get_interval_seconds():
    try:
        hrs = int(entry_hours.get() or 0)
        mins = int(entry_minutes.get() or 0)
        secs = int(entry_seconds.get() or 0)
        millis = int(entry_milliseconds.get() or 0)
    except ValueError:
        return 0.1
    total_ms = ((hrs * 3600 + mins * 60 + secs) * 1000) + millis
    interval_sec = max(total_ms / 1000, 0.001)
    return interval_sec

def get_target_key():
    key_str = hotkey_var.get().lower()
    if len(key_str) == 1:
        return key_str
    return 'e'

def auto_key_presser():
    global running
    interval = get_interval_seconds()
    key_to_press = get_target_key()

    if repeat_mode_var.get() == "count":
        try:
            count = int(entry_repeat.get())
        except ValueError:
            count = 1
        for _ in range(count):
            if not running:
                break
            keyboard.press(key_to_press)
            keyboard.release(key_to_press)
            time.sleep(interval)
        running = False
        update_button_states()
    else:
        while running:
            keyboard.press(key_to_press)
            keyboard.release(key_to_press)
            time.sleep(interval)

def on_press(key):
    global running, TOGGLE_KEY, click_thread
    if key == TOGGLE_KEY:
        running = not running
        print(f"{'Started' if running else 'Stopped'} auto key press.")
        update_button_states()
        if running:
            click_thread = threading.Thread(target=auto_key_presser, daemon=True)
            click_thread.start()

def start_listener(new_key):
    global listener, TOGGLE_KEY

    with listener_lock:
        TOGGLE_KEY = new_key
        if listener is not None:
            listener.stop()
            listener.join()
        listener = Listener(on_press=on_press)
        listener.start()

def start_clicking():
    global running, click_thread
    if running:
        return
    running = True
    update_button_states()
    print(f"Started clicking with key '{get_target_key().upper()}', interval {get_interval_seconds()*1000:.0f} ms.")
    click_thread = threading.Thread(target=auto_key_presser, daemon=True)
    click_thread.start()

def stop_clicking():
    global running
    running = False
    update_button_states()
    print("Stopped clicking.")

def update_button_states():
    if running:
        btn_start.config(state="disabled")
        btn_stop.config(state="normal")
    else:
        btn_start.config(state="normal")
        btn_stop.config(state="disabled")

def update_toggle_key():
    key_str = toggle_hotkey_var.get()
    new_key = change_toggle_key_from_string(key_str)
    if new_key:
        start_listener(new_key)
        print(f"Toggle key set to: {key_str.upper()}")
    else:
        print(f"Invalid toggle key '{key_str}', toggle key not changed.")

def on_toggle_hotkey_keypress(event):
    key_name = event.keysym.lower()

    pynput_key = None
    special_keys_map = {
        "f1": Key.f1, "f2": Key.f2, "f3": Key.f3, "f4": Key.f4, "f5": Key.f5,
        "f6": Key.f6, "f7": Key.f7, "f8": Key.f8, "f9": Key.f9, "f10": Key.f10,
        "f11": Key.f11, "f12": Key.f12,
        "escape": Key.esc, "return": Key.enter, "space": Key.space, "tab": Key.tab,
        "shift_l": Key.shift, "shift_r": Key.shift, "control_l": Key.ctrl, "control_r": Key.ctrl,
        "alt_l": Key.alt, "alt_r": Key.alt
    }

    if key_name in special_keys_map:
        pynput_key = special_keys_map[key_name]
        display_name = key_name.upper()
    elif len(key_name) == 1:
        pynput_key = key_name
        display_name = key_name.upper()
    else:
        return "break"

    toggle_hotkey_var.set(display_name)
    start_listener(pynput_key)
    print(f"Toggle key set to: {display_name}")
    return "break"

def save_settings():
    settings = {
        "interval": {
            "hours": entry_hours.get(),
            "minutes": entry_minutes.get(),
            "seconds": entry_seconds.get(),
            "milliseconds": entry_milliseconds.get()
        },
        "hotkey": hotkey_var.get(),
        "repeat_mode": repeat_mode_var.get(),
        "repeat_count": entry_repeat.get(),
        "toggle_key": toggle_hotkey_var.get()
    }
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(settings, f)
    except Exception as e:
        print(f"Failed to save settings: {e}")

def load_settings():
    if not os.path.isfile(CONFIG_FILE):
        return
    try:
        with open(CONFIG_FILE, "r") as f:
            settings = json.load(f)

        entry_hours.delete(0, "end")
        entry_hours.insert(0, settings["interval"]["hours"])

        entry_minutes.delete(0, "end")
        entry_minutes.insert(0, settings["interval"]["minutes"])

        entry_seconds.delete(0, "end")
        entry_seconds.insert(0, settings["interval"]["seconds"])

        entry_milliseconds.delete(0, "end")
        entry_milliseconds.insert(0, settings["interval"]["milliseconds"])

        hotkey_var.set(settings["hotkey"])
        repeat_mode_var.set(settings["repeat_mode"])
        toggle_repeat_mode()

        entry_repeat.delete(0, "end")
        entry_repeat.insert(0, settings["repeat_count"])

        toggle_hotkey_var.set(settings["toggle_key"])
        update_toggle_key()
    except Exception as e:
        print(f"Failed to load config: {e}")

def on_closing():
    save_settings()
    global exit_program
    exit_program = True
    with listener_lock:
        if listener is not None:
            listener.stop()
            listener.join()
    root.destroy()

root = tk.Tk()
root.title("Auto Key Clicker 1.0")
root.geometry("440x400")
root.resizable(False, False)
root.attributes('-topmost', True)

small_font = ("Arial", 8)

vcmd_interval = (root.register(limit_entry_length), "%P")
vcmd_repeat = (root.register(limit_entry_length), "%P")

frame_interval = ttk.LabelFrame(root, text="Key Interval", padding=(10, 5))
frame_interval.pack(fill="x", padx=10, pady=(10, 5))

def create_entry(parent, row, col, label_text, default=""):
    entry = ttk.Entry(parent, width=7, validate="key", validatecommand=vcmd_interval, font=small_font)
    entry.insert(0, default)
    entry.grid(row=row, column=col, padx=(5, 2))
    ttk.Label(parent, text=label_text, font=small_font).grid(row=row, column=col + 1, padx=(0, 10))
    return entry

entry_hours = create_entry(frame_interval, 0, 0, "hours", "0")
entry_minutes = create_entry(frame_interval, 0, 2, "mins", "0")
entry_seconds = create_entry(frame_interval, 0, 4, "secs", "1")
entry_milliseconds = create_entry(frame_interval, 0, 6, "Milliseconds", "0")

frame_middle = ttk.Frame(root)
frame_middle.pack(fill="x", padx=10)

frame_hotkey = ttk.LabelFrame(frame_middle, text="Key options", padding=(10, 5))
frame_hotkey.pack(side="left", fill="both", expand=True)

ttk.Label(frame_hotkey, text="Key to Press:", font=small_font).grid(row=0, column=0, sticky="w", padx=5)
hotkey_var = tk.StringVar(value="E")
entry_hotkey = ttk.Entry(frame_hotkey, textvariable=hotkey_var, width=5, font=small_font)
entry_hotkey.grid(row=0, column=1, padx=5)
entry_hotkey.bind("<KeyPress>", on_hotkey_keypress)

frame_repeat = ttk.LabelFrame(frame_middle, text="Repeat options", padding=(10, 5))
frame_repeat.pack(side="left", fill="both", expand=True, padx=(10, 0))

repeat_mode_var = tk.StringVar(value="until")

radio_count = ttk.Radiobutton(frame_repeat, text="Repeat", variable=repeat_mode_var, value="count", command=toggle_repeat_mode)
radio_count.grid(row=0, column=0, sticky="w", padx=5)

entry_repeat = tk.Spinbox(frame_repeat, from_=1, to=99999, width=7, font=small_font, validate="key", validatecommand=vcmd_repeat)
entry_repeat.grid(row=0, column=1, padx=5)
entry_repeat.delete(0, "end")
entry_repeat.insert(0, "1")

ttk.Label(frame_repeat, text="times", font=small_font).grid(row=0, column=2, sticky="w")

radio_until = ttk.Radiobutton(frame_repeat, text="Repeat until stopped", variable=repeat_mode_var, value="until", command=toggle_repeat_mode)
radio_until.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=(5, 0))

toggle_repeat_mode()

frame_buttons = ttk.Frame(root)
frame_buttons.pack(fill="x", pady=10, padx=10)

btn_start = ttk.Button(frame_buttons, text="Start", command=start_clicking)
btn_start.pack(side="left", expand=True, fill="x", padx=(0,5), ipadx=15, ipady=10)

btn_stop = ttk.Button(frame_buttons, text="Stop", command=stop_clicking, state="disabled")
btn_stop.pack(side="right", expand=True, fill="x", padx=(5,0), ipadx=15, ipady=10)

frame_toggle = ttk.LabelFrame(root, text="Toggle Hotkey (Click and Press a Key)", padding=(10, 5))
frame_toggle.pack(fill="x", padx=10, pady=(5,10))

toggle_hotkey_var = tk.StringVar(value="F5")
entry_toggle_hotkey = ttk.Entry(frame_toggle, textvariable=toggle_hotkey_var, width=10, font=small_font)
entry_toggle_hotkey.pack(side="left", padx=(5,10))
entry_toggle_hotkey.bind("<KeyPress>", on_toggle_hotkey_keypress)

btn_set_toggle = ttk.Button(frame_toggle, text="Set Toggle Key", command=update_toggle_key)
btn_set_toggle.pack(side="left")

start_listener(Key.f5)
load_settings()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
