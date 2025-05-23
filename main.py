import tkinter as tk
from tkinter import messagebox, ttk
import os
from datetime import datetime
import time
import obsws_python as obs
from dotenv import load_dotenv
load_dotenv(override=True)

# connection
cl = obs.ReqClient(host=os.getenv("HOST"), port=os.getenv("PORT"), password=os.getenv("PASSWORD"), timeout=3) #print info about connection

#variables
licznik = 0
videos = [] #to do: save queue in file and restore it after restarting program
video_types = ('.mp4', '.avi', '.mov', '.mkv')
current_directory = os.path.dirname(os.path.abspath(__file__))
delete_source = ""
try:
    cl.create_scene(name="videos") #to do
except Exception as e:
    print("Scene videos already exists, it's ok :)")

def update_video(time, new_time):
    global videos
    l = 0
    while l < len(videos):
        if videos[l]["time"] == time:
            videos[l]["time"] = new_time
        l+=1

def get_video_files(): #to do: photos?
    video_files = []
    for filename in os.listdir(current_directory):
        if filename.endswith(video_types):
            video_files.append(filename)
    return video_files

def play_video(video_file_path):
    global licznik
    global delete_source

    licznik += 1
    scene_name = "videos"
    source_name = scene_name + "_source_" + str(licznik)
    video_file_path = current_directory + "/" + video_file_path
    
    #time.sleep(0.1)
    cl.set_current_program_scene(name=scene_name)

    cl.create_input(
        sceneName=scene_name,
        inputName=source_name,
        inputKind="ffmpeg_source",
        inputSettings={"local_file": video_file_path, "is_local_file": True, "clear_on_media_end": False},
        sceneItemEnabled=True,
    )
    
    if delete_source != "":
        cl.remove_input(name=delete_source)
        delete_source = ""

    time.sleep(0.1)
    response = cl.get_media_input_status(name=source_name)
    while response.media_state == "OBS_MEDIA_STATE_PLAYING":
        response = cl.get_media_input_status(name=source_name)
    delete_source = source_name

def validate_time_format(time_str):
    try:
        time.strptime(time_str, "%H:%M:%S")
        return True
    except ValueError:
        return False

def add_to_queue():
    selected_video = video_listbox.get(tk.ACTIVE)
    time_to_play = time_entry.get()

    if selected_video and time_to_play:
        if validate_time_format(time_to_play):
            videos.append({"file": selected_video, "time": time_to_play})
            
            update_queue_display()
            time_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Error", "Please enter the time in format HH:MM:SS.")
    else:
        messagebox.showwarning("Error", "Please select a video from the list and enter the time.")

def edit_time():
    selected_item = treeview.selection()
    if selected_item:
        #selected_video = treeview.item(selected_item, "values")[0]
        new_time = edit_time_entry.get()
        if new_time and validate_time_format(new_time):
            update_video(treeview.item(selected_item, "values")[1], new_time)
            update_queue_display()
            edit_time_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Error", "Please enter the time in format HH:MM:SS.")
    else:
        messagebox.showwarning("Error", "Please select a video from the list and enter the time.")

def update_queue_display():
    global videos
    for row in treeview.get_children():
        treeview.delete(row)
    
    videos = sorted(videos, key=lambda x: x["time"])
    for video in videos:
        treeview.insert('', 'end', values=(video["file"], video["time"]))

def check_and_play_scheduled_videos():
    global videos
    current_time = datetime.now().strftime("%H:%M:%S")
    for video in videos:
        if current_time >= video["time"]:
            print(current_time + " PLAYING: " + video["file"])
            play_video(video["file"])
            for video2 in videos[:]:
                if video2["time"] == video["time"]:
                    videos.remove(video2)
            update_queue_display()
            break

def on_closing():
    cl.remove_scene(name="videos")
    root.destroy()

def load_video_list(): #to do: add refreshing button
    video_listbox.delete(0, tk.END)
    video_files = get_video_files()
    for video in video_files:
        video_listbox.insert(tk.END, video)

def run_scheduled_tasks():
    while True:
        check_and_play_scheduled_videos()
        time.sleep(0.01)

# GUI
root = tk.Tk()
root.title("OBS video queue manager")
root.protocol("WM_DELETE_WINDOW", on_closing)

# Video list
video_listbox = tk.Listbox(root, height=5, width=40)
video_listbox.pack(pady=5)

# Button for adding videos to queue
add_button = tk.Button(root, text="Add to queue", command=add_to_queue)
add_button.pack(pady=5)

# Time input
time_entry = tk.Entry(root, width=10)
time_entry.pack(pady=5)

# Queue table
treeview = ttk.Treeview(root, columns=("Video", "Time"), show="headings")
treeview.heading("Video", text="Video")
treeview.heading("Time", text="Time")
treeview.pack(pady=10)

# Edit time input
edit_time_label = tk.Label(root, text="New time:")
edit_time_label.pack(pady=5)

edit_time_entry = tk.Entry(root, width=10)
edit_time_entry.pack(pady=5)

edit_time_button = tk.Button(root, text="Edit time", command=edit_time)
edit_time_button.pack(pady=5)

# Load videos
load_video_list()
update_queue_display()

# Running tasks in the background
import threading
threading.Thread(target=run_scheduled_tasks, daemon=True).start()

root.mainloop()
