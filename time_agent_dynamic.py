import tkinter as tk
from time import time, strftime, localtime, gmtime
import json
import os
import pygame
from enum import Enum
import random

class Audio(Enum):
    FRUEH = "frueh"
    ABENDS = "abends"
    ZWISCHENDURCH = "zwischendurch"


class Timer():
    def __init__(self):
        self.just_started = True
        self.running = False
        self.root = tk.Tk()
        self.root.title("Working time")

        # Initialize pygame for audio playback
        pygame.mixer.init()

        projects = self.load_projects()
        self.selected_project = projects[0]
        self.selected_project_index = 0
        col_num = len(projects)

        self.toggle_button = tk.Label(self.root, text="00:00:00", font=("Helvetica", 48), cursor='hand2')
        self.toggle_button.grid(row=0, column=0, columnspan=col_num, sticky=tk.E)
        self.toggle_button.bind("<Button-1>", self.toggle_clock)

        # Load project buttons from JSON file
        self.project_buttons = []
        self.create_project_buttons(projects, self.project_buttons)

        # Display current time
        self.clock_label = tk.Label(self.root, text="", font=("Helvetica", 12))
        self.clock_label.grid(row=2, column=0, columnspan=col_num, sticky=tk.E)
        self.update_clock()

        self.root.mainloop()

    def update_clock(self):
        current_time = strftime('%H:%M:%S', localtime())
        self.clock_label.config(text=current_time)
        self.root.after(1000, self.update_clock)

    def toggle_clock(self, event=None):
        if not self.running:
            current_hour = int(strftime('%H', localtime()))
            # Play the audio when starting the clock
            if self.just_started and current_hour < 9:
                self.just_started = False
                audio_file = self.get_audio_file(Audio.FRUEH)
            elif current_hour > 18:
                audio_file = self.get_audio_file(Audio.ABENDS)
            else:
                audio_file = self.get_audio_file(Audio.ZWISCHENDURCH)
            print(f'say {audio_file} {current_hour}')
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()

        if self.running:
            self.running = False
            self.stop_clock()
        else:
            self.running = True
            self.start_clock()

    def start_clock(self):
        self.running = True
        start_time = time()
        while self.running:
            elapsed_time = time() - start_time
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.toggle_button.config(text=f'{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}')
            self.root.update()

    def stop_clock(self):
        self.running = False

    def load_projects(self):
        with open('projects.json', 'r') as file:
            projects = json.load(file)
            return projects

    def create_project_buttons(self, projects, project_buttons):
        for i, project in enumerate(projects):
            project_button = tk.Button(self.root, text=project, font=("Helvetica", 14))
            project_button.grid(row=1, column=i, sticky=tk.E)
            project_buttons.append(project_button)
            project_button.bind("<Button-1>", lambda event, button=project_button, project=project: self.toggle_project(button, project))        
        for buttonx in self.project_buttons:
            buttonx.config(relief=tk.SUNKEN)
        project_buttons[0].config(relief=tk.RAISED)

    def toggle_project(self, button, project):  
        print()      
        
        if button.cget("relief") == tk.RAISED:
            # if an already active project was selected do nothing
            return        
        
        # Unselect the previously selected project and save the time
        if self.selected_project and self.selected_project != project:
            print(f'old project {self.selected_project} selected: is raised -> set sunken')   
            self.project_buttons[self.selected_project_index].config(relief=tk.SUNKEN)
            if self.running:
                self.running = False
                self.stop_clock()
                self.save_project()
        else:
            self.toggle_button.config(text="00:00:00")
            self.root.update()
      

        self.selected_project = project
        self.selected_project_index = self.project_buttons.index(button)
        print(f'new project {project} selected: is sunken -> set raised')  
        self.root.update()  
        self.project_buttons[self.selected_project_index].config(relief=tk.RAISED)
        print(f'-> {project} {self.selected_project_index}')
        self.root.update()


    def get_audio_file(self, audio_type: Audio):
        # Define the base folder for audio files
        base_folder = "data"        

        # Construct the full path to the subfolder
        subfolder_path = os.path.join(base_folder, audio_type.value)

        # Check if the subfolder exists
        if not os.path.exists(subfolder_path):
            raise FileNotFoundError(f"Subfolder '{audio_type.value}' not found in '{base_folder}'")

        # List all files in the subfolder
        audio_files = [f for f in os.listdir(subfolder_path) if f.lower().endswith(".mp3")]

        # Check if there are any MP3 files
        if not audio_files:
            raise FileNotFoundError(f"No MP3 files found in '{audio_type.value}'")

        # Select a random MP3 file
        selected_file = random.choice(audio_files)

        # Return the full path to the selected MP3 file
        return os.path.join(subfolder_path, selected_file)


    def save_project(self):
        if self.selected_project:
            # Read out the time displayed on the timer button
            time_displayed = self.toggle_button.cget("text")
            current_day = strftime('%Y-%m-%d', gmtime())  # Get the current day in YYYY-MM-DD format
            current_time = strftime('%H:%M:%S', localtime())
            data = {current_day: {current_time: {self.selected_project: time_displayed}}}
            # Save the time to a file or perform the desired action
            print(f"Saving project: {self.selected_project}, Time: {time_displayed}")
            file_path = "times.json"
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    saved_data = json.load(file)
                    if current_day in saved_data:
                        day_data = saved_data[current_day]
                        if time_displayed in day_data:
                            # Append the project and its displayed time to the current saving time
                            day_data[current_time][self.selected_project] = time_displayed
                        else:
                            # Create a new saving time with the project and its displayed time
                            day_data[current_time] = {self.selected_project: time_displayed}
                    else:
                        # Create a new day entry with the saving time, project, and displayed time
                        saved_data[current_day] = {current_time: {self.selected_project: time_displayed}}
            else:
                saved_data = data
            with open(file_path, 'w') as file:
                json.dump(saved_data, file)

if __name__ == "__main__":
    timer = Timer()
