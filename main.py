import tkinter as tk
from tkinter import messagebox, ttk
import os
from datetime import datetime, timedelta
import time
import obsws_python as obs
from dotenv import load_dotenv
from moviepy import VideoFileClip
load_dotenv(override=True)

# connection
cl = obs.ReqClient(host=os.getenv("HOST"), port=os.getenv("PORT"), password=os.getenv("PASSWORD"), timeout=3) #print info about connection
# print(dir(cl))
#variables
licznik = 0
videos = [] #to do: save queue in file and restore it after restarting program
now_playing = ""
paused = False
queue_paused = False

video_duration = {}


video_types = ('.mp4', '.avi', '.mov', '.mkv')
current_directory = os.path.dirname(os.path.abspath(__file__))
delete_source = ""
try:
    cl.create_scene(name="videos") #to do
except Exception as e:
    print("Scene videos already exists, it's ok :)")

def update_video(time, new_time):
    global videos
    videos = sorted(videos, key=lambda x: x["time"])
    l = len(videos) - 1
    while l >= 0:
        if videos[l]["time"] == time:
            # print("a", videos[l])
            videos[l]["time"] = new_time
        elif videos[l]["time"] >= new_time:
            # print("b", videos[l])
            videos[l]["time"] += 1
            
        l-=1
    # print(video_duration)
    videos = sorted(videos, key=lambda x: x["time"])


def get_video_files(): #to do: photos?
    global video_duration
    video_files = []
    for filename in os.listdir(current_directory):
        if filename.endswith(video_types):
            video_files.append(filename)
            video_duration[filename] = VideoFileClip(current_directory + "/" + filename).duration
    return video_files

def play_video(video_file_path):
    global licznik
    global delete_source
    global now_playing
    global paused

    licznik += 1
    scene_name = "videos"
    source_name = scene_name + "_source_" + str(licznik)
    now_playing = source_name
    now_playing_label.config(text="Now playing: " + video_file_path)
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

    # time.sleep(3)
    # cl.pause_media_input(input_name=source_name)
    # cl.send(obs.requests.PauseMediaInput(inputName=source_name))
    
    # print(cl.send("GetVersion", raw=True))
    
    if delete_source != "":
        cl.remove_input(name=delete_source)
        delete_source = ""

    # time.sleep(0.1)
    # response = cl.get_media_input_status(name=source_name)
    # while response.media_state == "OBS_MEDIA_STATE_PLAYING" or paused:
    #     response = cl.get_media_input_status(name=source_name)
    delete_source = source_name

def validate_time_format(time_str):
    try:
        int(time_str)
        return True
    except ValueError:
        return False

def add_to_queue():
    selected_video = video_listbox.get(tk.ACTIVE)
    time_to_play = time_entry.get()

    if selected_video and time_to_play:
        if validate_time_format(time_to_play):
            time_to_play = int(time_to_play)
            videos.append({"file": selected_video, "time": time_to_play})
            
            update_queue_display()
            time_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Error", "Please enter number.")
    else:
        messagebox.showwarning("Error", "Please select a video from the list and enter the time.")

def edit_time():
    
    selected_item = treeview.selection()
    if selected_item:
        #selected_video = treeview.item(selected_item, "values")[0]
        new_time = edit_time_entry.get()
        
        if new_time and validate_time_format(new_time):
            new_time = int(new_time)
            update_video(int(treeview.item(selected_item, "values")[1]), new_time)
            update_queue_display()
            edit_time_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Error", "Please enter number.")
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
    global delete_source
    global now_playing
    global video_duration

    ok = False
    

    if now_playing != "":
        # print(duration)
        response = cl.get_media_input_status(name=now_playing)
        # print(dir(response))
        if response.media_state == "OBS_MEDIA_STATE_ENDED": #to do
            now_playing = ""
            now_playing_label.config(text="Now playing: ")
            # print(response.media_state)
    

    # time.sleep(0.1)
    if delete_source != "" and paused == False:
        response = cl.get_media_input_status(name=delete_source)
        if response.media_state != "OBS_MEDIA_STATE_PLAYING":
            ok = True
    
    if (ok or (delete_source == "" and paused == False)) and queue_paused == False:
        videos = sorted(videos, key=lambda x: x["time"])
        current_time = datetime.now().strftime("%H:%M:%S")
        for video in videos:
            # if current_time >= video["time"]:
            print(current_time + " PLAYING: " + video["file"] + " duration " + str(video_duration[video["file"]]) + "s")
            play_video(video["file"])
            for video2 in videos[:]:
                if video2["time"] == video["time"]:
                    videos.remove(video2)
            update_queue_display()
            break

def on_closing():
    cl.remove_scene(name="videos")
    root.destroy()

def load_video_list():
    video_listbox.delete(0, tk.END)
    video_files = get_video_files()
    for video in video_files:
        video_listbox.insert(tk.END, video)

def update_queue_time():
    global videos
    global now_playing
    time_sum = 0.0
    if now_playing != "":
        duration = cl.get_media_input_status(name=now_playing).media_duration
        if duration is None:
            duration = 0.0
        time = cl.get_media_input_status(name=now_playing).media_cursor
        if time is None:
            time = 0.0
        time_sum = (duration - time) / 1000
    # print((duration - time) / 1000)


    
    videos = sorted(videos, key=lambda x: x["time"])
    
    for video in videos:
        time_sum += video_duration[video["file"]]
    now = datetime.now()
    queue_end_time = now + timedelta(seconds=time_sum)
    queue_ends_in_label.config(text="Queue ends in: " + str(round(time_sum / 60.0, 2)) + " minutes (" + queue_end_time.strftime("%H:%M:%S") + ")")
    

def run_scheduled_tasks():
    while True:
        check_and_play_scheduled_videos()
        update_queue_time()
        time.sleep(0.1)

def pause():
    global paused
    global now_playing
    
    if paused == False:
        paused = True
        if now_playing != "":
            cl.send("TriggerMediaInputAction", {
                "inputName": now_playing,
                "mediaAction": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PAUSE"
            })
        pause_button.config(text="Resume")
    else:
        paused = False
        if now_playing != "":
            cl.send("TriggerMediaInputAction", {
                "inputName": now_playing,
                "mediaAction": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY"
            })
        pause_button.config(text="Pause")

def queue_pause():
    global queue_paused
    
    if queue_paused == False:
        queue_paused = True
        queue_pause_button.config(text="Queue Resume")
    else:
        queue_paused = False
        queue_pause_button.config(text="Queue Pause")

# GUI
root = tk.Tk()
root.title("OBS video queue manager")
root.protocol("WM_DELETE_WINDOW", on_closing)

top = tk.Frame(root)
top.pack(pady=10)

#now playing
now_playing_label = tk.Label(top, text="Now playing: ")
now_playing_label.pack(side="left", padx=10)

#pause
pause_button = tk.Button(top, text="Pause", command=pause)
pause_button.pack(side="left", padx=5)

#queue pause
queue_pause_button = tk.Button(top, text="Queue Pause", command=queue_pause)
queue_pause_button.pack(side="left", padx=5)

refresh_button = tk.Button(root, text="Refresh video files", command=load_video_list)
refresh_button.pack(pady=5)

#queue ends in
queue_ends_in_label = tk.Label(root, text="Queue ends in: ")
queue_ends_in_label.pack(pady=5)

# Video list
video_listbox = tk.Listbox(root, height=5, width=40)
video_listbox.pack(pady=5)

# Time input
time_entry = tk.Entry(root, width=10)
time_entry.pack(pady=5)

# Button for adding videos to queue
add_button = tk.Button(root, text="Add to queue", command=add_to_queue)
add_button.pack(pady=5)

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
