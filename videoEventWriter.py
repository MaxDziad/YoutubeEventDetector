import string
import videoExtensions
from dataclasses import dataclass


class VideoEventWriter:
    VIDEO_FRAME_SIZE = 30

    video_name = ""
    video_resolution = ()

    current_frames = []
    requested_events = []

    def __init__(self, name, resolution):
        self.video_name = name
        self.video_resolution = resolution

    def request_event_write(self, event_id):
        event_data = EventData(int(self.VIDEO_FRAME_SIZE / 2), event_id)
        self.requested_events.append(event_data)

    def receive_frame(self, frame):
        if len(self.current_frames) == self.VIDEO_FRAME_SIZE:
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
        full_video_name = "out/" + self.video_name + "/" + event_id + ".avi"
        videoExtensions.save_video_event(self.current_frames, full_video_name, self.video_resolution)


@dataclass
class EventData:
    frames_left: int
    event_id: string
