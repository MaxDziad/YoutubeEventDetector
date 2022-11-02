import os
import string
import videoExtensions
from dataclasses import dataclass


class VideoEventWriter:
    BUF_SIZE = 80
    event_video_frames_size = 30

    video_name = ""
    video_resolution = ()

    current_frames = []
    requested_events = []

    def __init__(self, name, resolution):
        self.video_name = name
        self.video_resolution = resolution
        new_directory_name = "out\\" + name

        if not os.path.isdir(new_directory_name):
            os.mkdir("out\\" + name)

    def request_event_write(self, event_id):
        event_data = EventData(int(self.event_video_frames_size / 2), event_id)
        self.requested_events.append(event_data)

    def request_instant_event_write(self, event_id):
        self.instant_save_video(event_id)

    def receive_frame(self, frame):
        if len(self.current_frames) == self.BUF_SIZE:
            self.current_frames.pop(0)

        self.current_frames.append(frame)
        self.decrease_event_counters()

    def decrease_event_counters(self):
        for event_data in self.requested_events:
            event_data.frames_left -= 1

            if event_data.frames_left == 0:
                self.save_video(event_data.event_id)
                self.requested_events.remove(event_data)

    def save_video(self, event_id):
        full_video_name = "out\\" + self.video_name + "\\" + event_id + ".mp4"
        video_frames = self.current_frames[self.BUF_SIZE - 1 - self.event_video_frames_size:self.BUF_SIZE - 1]
        videoExtensions.save_video_event(video_frames, full_video_name, self.video_resolution)

    def instant_save_video(self, event_id):
        full_video_name = "out\\" + self.video_name + "\\" + event_id + ".mp4"
        video_frames = self.current_frames[5:self.event_video_frames_size + 5]
        videoExtensions.save_video_event(video_frames, full_video_name, self.video_resolution)


@dataclass
class EventData:
    frames_left: int
    event_id: string
