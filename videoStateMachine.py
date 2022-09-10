from enum import Enum
import videoExtensions


class State(Enum):
    LOOKING_FOR_VIDEO = 0
    LOADING_VIDEO = 1
    PLAYING_VIDEO = 2
    PAUSED_VIDEO = 3


class VideoStateMachine:
    # static parameters
    FRAME_WIDTH = 0
    FRAME_HEIGHT = 0

    # dynamic parameters
    current_state = None

    previous_frame = None
    next_frame = None

    current_contour = None
    height_bar_y = -1

    # references
    has_height_bar = height_bar_y != -1

    def __init__(self):
        self.current_state = State.LOOKING_FOR_VIDEO

    def initialize(self, width, height):
        self.FRAME_WIDTH = width
        self.FRAME_HEIGHT = height

    def run_current_state(self, previous_frame, next_frame):
        self.previous_frame = previous_frame
        self.next_frame = next_frame

        match self.current_state:
            case State.LOOKING_FOR_VIDEO:
                self.look_for_video()
            case State.LOADING_VIDEO:
                self.wait_for_video_to_load()
            case State.PLAYING_VIDEO():
                self.look_for_interruptions()
            case State.PAUSED_VIDEO():
                self.look_for_continuation()

    def change_state(self, state):
        self.current_state = state

    def look_for_video(self):
        biggest_contour = videoExtensions.find_biggest_contour(self.previous_frame)
        self.current_contour = videoExtensions.simplify_contour(biggest_contour)

        if videoExtensions.is_video_initializing(self.previous_frame, self.current_contour):
            self.change_state(State.LOADING_VIDEO)

    def wait_for_video_to_load(self):
        height_bar_y = videoExtensions.try_get_bar_height(self.previous_frame, self.current_contour)
        scroll_bar_down_edge = videoExtensions.find_bottom_scroll_bar_point(self.previous_frame, self.FRAME_HEIGHT, self.FRAME_WIDTH)

    def look_for_interruptions(self):
        return 0

    def look_for_continuation(self):
        return 0
