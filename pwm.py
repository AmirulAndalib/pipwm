from gpiozero import PWMOutputDevice, Device
import tkinter as tk
from tkinter import ttk
import subprocess
import time
import configparser
import atexit
import logging

class PWMFanControl:
    def __init__(self, master):
        self.master = master
        master.title("PWM Fan Control")

        # Force gpiozero to use the default pin factory
        Device.pin_factory = None

        self.config = configparser.ConfigParser()
        self.load_settings()  # Load settings from pwm.config

        self.fan_pin_var = tk.StringVar(value=str(self.config.getint('Settings', 'FanPin')))
        self.fan_pin_label = tk.Label(self.master, text="Fan GPIO Pin:")
        self.fan_pin_label.grid(row=0, column=0, padx=10, pady=10)
        self.fan_pin_entry = tk.Entry(self.master, textvariable=self.fan_pin_var)
        self.fan_pin_entry.grid(row=0, column=1, padx=10, pady=10)

        self.fan = PWMOutputDevice(self.config.getint('Settings', 'FanPin'))
        self.fan_status = tk.StringVar(value="OFF")

        self.theme_var = tk.StringVar(value="Light")
        self.auto_start_var = tk.BooleanVar(value=True)

        self.create_gui()

        # Register the shutdown function
        atexit.register(self.shutdown)

        # Initialize logging
        logging.basicConfig(filename='fan_control.log', level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

    def create_gui(self):
        self.pwm_label = tk.Label(self.master, text="Fan Speed:")
        self.pwm_label.grid(row=1, column=0, padx=10, pady=10)

        self.pwm_scale = tk.Scale(self.master, from_=0, to=100, orient=tk.HORIZONTAL, length=200, label="",
                                  command=self.update_pwm)
        self.pwm_scale.set(self.config.getfloat('Settings', 'FanSpeed'))
        self.pwm_scale.grid(row=1, column=1, padx=10, pady=10)

        self.temp_label = tk.Label(self.master, text="CPU Temp:")
        self.temp_label.grid(row=2, column=0, padx=10, pady=10)

        self.freq_label = tk.Label(self.master, text="CPU Frequency:")
        self.freq_label.grid(row=3, column=0, padx=10, pady=10)

        self.time_label = tk.Label(self.master, text="Elapsed Time:")
        self.time_label.grid(row=4, column=0, padx=10, pady=10)

        self.fan_status_label = tk.Label(self.master, text="Fan Status:")
        self.fan_status_label.grid(row=5, column=0, padx=10, pady=10)
        self.fan_status_display = tk.Label(self.master, textvariable=self.fan_status)
        self.fan_status_display.grid(row=5, column=1, padx=10, pady=10)

        self.theme_label = tk.Label(self.master, text="GUI Theme:")
        self.theme_label.grid(row=6, column=0, padx=10, pady=10)
        self.theme_menu = ttk.Combobox(self.master, textvariable=self.theme_var, values=["Light", "Dark"])
        self.theme_menu.grid(row=6, column=1, padx=10, pady=10)
        self.theme_menu.bind("<<ComboboxSelected>>", self.toggle_theme)

        self.auto_start_check = tk.Checkbutton(self.master, text="Auto Start on Boot", variable=self.auto_start_var)
        self.auto_start_check.grid(row=7, column=0, columnspan=2, padx=10, pady=10)

        self.quit_button = tk.Button(self.master, text="Quit", command=self.cleanup)
        self.quit_button.grid(row=9, column=0, columnspan=2, pady=10)

        self.start_time = time.time()

        self.update_gui()

    def update_pwm(self, duty_cycle):
        duty_cycle = float(duty_cycle)
        self.fan.value = duty_cycle / 100.0
        self.config.set('Settings', 'FanSpeed', str(duty_cycle))
        self.save_settings()  # Save settings to pwm.config
        logging.info(f"Fan speed set to {duty_cycle}%")

    def update_gui(self):
        temp = subprocess.getoutput("vcgencmd measure_temp | sed 's/[^0-9.]//g'")
        freq = subprocess.getoutput("vcgencmd measure_clock arm | awk -F '=' '{print $2}'")

        elapsed_time = time.time() - self.start_time
        hours, rem = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(rem, 60)
        elapsed_time_str = "{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds)

        self.temp_label.config(text=f"CPU Temp: {temp}°C")
        self.freq_label.config(text=f"CPU Frequency: {int(freq) / 1000000} MHz")
        self.time_label.config(text=f"Elapsed Time: {elapsed_time_str}")

        self.update_fan_status()

        self.master.after(1000, self.update_gui)

    def toggle_theme(self, event=None):
        if self.theme_var.get() == "Dark":
            self.master.configure(bg="#2E2E2E")
        else:
            self.master.configure(bg="white")
        for widget in self.master.winfo_children():
            try:
                widget.configure(bg=self.master.cget('bg'))
            except tk.TclError:
                pass  # Some widgets may not support background color

    def load_settings(self):
        try:
            self.config.read('pwm.config')
        except FileNotFoundError:
            # If pwm.config doesn't exist, create it with default settings
            self.config['Settings'] = {'FanSpeed': '0', 'FanPin': '14', 'ThresholdTemp': '40', 'ThresholdSpeed': '50'}
            self.save_settings()

    def save_settings(self):
        self.config.set('Settings', 'FanPin', str(self.fan_pin_var.get()))
        with open('pwm.config', 'w') as configfile:
            self.config.write(configfile)

    def cleanup(self):
        self.fan.value = 0
        self.master.destroy()

    def shutdown(self):
        # This function will be called during system shutdown
        self.fan.value = 0
        logging.info("Fan turned off during system shutdown")

def update_fan_status(self):
    current_temp_str = self.temp_label.cget("text").split(":")[1].strip()  # Remove leading/trailing spaces
    current_temp = float(current_temp_str[:-1])  # Remove '°C' and convert to float
    threshold_temp = self.config.getint('Settings', 'ThresholdTemp')
    threshold_speed = self.config.getint('Settings', 'ThresholdSpeed')

    if self.pwm_scale.get() > 0:
        # If the fan speed slider is manually set, use the manual setting
        self.fan.value = self.pwm_scale.get() / 100.0
    elif current_temp >= threshold_temp:
        # If the temperature crosses the threshold, set the fan to the threshold speed
        self.fan.value = threshold_speed / 100.0
    else:
        # If the temperature is below the threshold, turn off the fan
        self.fan.value = 0.0

    if self.fan.value > 0:
        self.fan_status.set("ON")
    else:
        self.fan_status.set("OFF")

def main():
    root = tk.Tk()
    app = PWMFanControl(root)
    root.mainloop()

if __name__ == "__main__":
    main()
