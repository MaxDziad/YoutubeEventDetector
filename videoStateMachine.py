from enum import Enum
import videoExtensions
import cv2


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

    is_full_screen = False
    has_unpaused_symbol_in_bar = False

    current_contour = None
    yt_bar_y = float('-inf')
    scroll_bar_bottom_edge = float('inf')

    watch_for_loading_circle = False

    # references
    has_height_bar = yt_bar_y != float('-inf')
    has_scroll_bar = scroll_bar_bottom_edge != float('inf')

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
        videoExtensions.get_diff_between_frames(self.previous_frame, self.next_frame, self.current_contour)
        self.try_look_for_bar()
        self.make_scroll_bar_check()

    def look_for_interruptions(self):
        return 0

    def look_for_continuation(self):
        return 0

    def try_look_for_bar(self):
        yt_bar_pause_image = None

        if not self.has_height_bar:
            self.yt_bar_y = videoExtensions.try_get_yt_bar_height(self.previous_frame, self.current_contour)

        if self.has_height_bar:
            yt_bar_pause_image = videoExtensions.get_youtube_bar_image(self.previous_frame,
                                                                       self.current_contour,
                                                                       self.yt_bar_y)

        if yt_bar_pause_image is not None:
            self.has_unpaused_symbol_in_bar = videoExtensions.is_unpaused_symbol_in_bar(self.previous_frame)

    def make_scroll_bar_check(self):
        current_scroll_bar_bottom_edge = videoExtensions.find_bottom_scroll_bar_point(self.previous_frame,
                                                                                      self.FRAME_HEIGHT,
                                                                                      self.FRAME_WIDTH)

        if not self.has_scroll_bar:
            self.scroll_bar_bottom_edge = current_scroll_bar_bottom_edge
        elif current_scroll_bar_bottom_edge != self.scroll_bar_bottom_edge:
            scroll_difference = self.scroll_bar_bottom_edge - current_scroll_bar_bottom_edge
            self.scroll_bar_bottom_edge = current_scroll_bar_bottom_edge
            # TBD - updating components position when scrolled
            # self.update_components_position(scroll_difference)

    def update_components_position(self, difference):
        if self.has_height_bar:
            self.yt_bar_y += difference

        for point in self.current_contour:
            point[0] += difference
            point[1] += difference
