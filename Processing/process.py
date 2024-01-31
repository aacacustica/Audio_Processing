import os
import subprocess
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
import queue
import logging

class TextHandler(logging.Handler):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        self.text.configure(state='normal')
        self.text.insert(tk.END, msg + '\n')
        self.text.configure(state='disabled')
        self.text.yview(tk.END)

urban_model_program = 'urban_model.py'
leq_level_program = 'leq_level_class.py'
plotting_program = 'main.py'

def run_subprocess(command, queue):
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in iter(process.stdout.readline, ''):
            queue.put(line)
        process.stdout.close()
        process.wait()
        queue.put("Command finished successfully.")
    except subprocess.CalledProcessError as e:
        queue.put(f"An error occurred: {e}")

def get_last_subfolder(directory):
    subfolders = [os.path.join(directory, o) for o in os.listdir(directory) 
                  if os.path.isdir(os.path.join(directory, o))]
    if not subfolders:
        return None
    subfolders.sort()
    return subfolders[-1]

def process_urban_model(base_directory, queue):
    os.chdir(r'C:\Users\GIS2\Documents\santi\GitHub\AAC\AI_Model\Urban_Model')
    queue.put("Changed directory to Urban Model")
    for folder in os.listdir(base_directory):
        full_path = os.path.join(base_directory, folder)
        if os.path.isdir(full_path):
            last_subfolder = get_last_subfolder(full_path)
            if last_subfolder:
                queue.put(f"Processing folder: {folder}")
                run_subprocess(['python', urban_model_program, '-p', last_subfolder], queue)

def process_leq_level(base_directory, queue):
    os.chdir(r'C:\Users\GIS2\Documents\santi\GitHub\AAC\SPL\Leq_Levels\Leq_level')
    queue.put("Changed directory to Leq Level")
    for folder in os.listdir(base_directory):
        full_path = os.path.join(base_directory, folder)
        if os.path.isdir(full_path):
            last_subfolder = get_last_subfolder(full_path)
            if last_subfolder:
                queue.put(f"Processing: {last_subfolder} in Leq Level")
                run_subprocess(['python', leq_level_program, '-p', last_subfolder], queue)

def process_plotting(base_directory, queue):
    os.chdir(r'C:\Users\GIS2\Documents\santi\GitHub\AAC\SPL\Visualization\Sonometer-AudioMoth')
    queue.put("Changed directory to Plotting")
    base_directory_plot = base_directory.replace('3-Medidas', '5-Resultados')
    queue.put(f"Processing plotting for: {base_directory_plot}")
    run_subprocess(['python', plotting_program, '-f', base_directory_plot, '-a', '900', '-p', '90', '10'], queue)

def process_in_thread(base_directory, queue):
    try:
        process_urban_model(base_directory, queue)
        process_leq_level(base_directory, queue)
        process_plotting(base_directory, queue)
        queue.put("All tasks have been completed.")
    except Exception as e:
        queue.put(str(e))

def start_processing():
    base_directory = path_entry.get()
    if not os.path.exists(base_directory):
        messagebox.showerror("Error", "The provided path does not exist.")
        return

    process_thread = threading.Thread(target=process_in_thread, args=(base_directory, output_queue))
    process_thread.start()
    root.after(100, check_queue)

def check_queue():
    while True:
        try:
            message = output_queue.get_nowait()
        except queue.Empty:
            break
        else:
            log_text.configure(state='normal')
            log_text.insert(tk.END, message + '\n')
            log_text.configure(state='disabled')
            log_text.yview(tk.END)
            if message == "All tasks have been completed.":
                messagebox.showinfo("Processing Complete", message)

    root.after(100, check_queue)

# def browse_folder():
#     dirname = filedialog.askdirectory()
#     if dirname:
#         path_entry.delete(0, tk.END)
#         path_entry.insert(0, dirname)

def browse_folder():
    dirname = filedialog.askdirectory()
    if dirname:
        normalized_path = os.path.normpath(dirname)  # normalize the path
        path_entry.delete(0, tk.END)
        path_entry.insert(0, normalized_path)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Audio Processing")

    tk.Label(root, text="Enter the 3-Medidas folder path:").pack(padx=10, pady=5)
    path_entry = tk.Entry(root, width=50)
    path_entry.pack(padx=10, pady=5)

    browse_button = tk.Button(root, text="Browse", command=browse_folder)
    browse_button.pack(padx=10, pady=5)

    start_button = tk.Button(root, text="Start Processing", command=start_processing)
    start_button.pack(padx=10, pady=5)

    log_text = scrolledtext.ScrolledText(root, state='disabled', height=10)
    log_text.pack(padx=10, pady=5)

    output_queue = queue.Queue()

    root.mainloop()
