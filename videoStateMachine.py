from enum import Enum

import eventPrinter
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
    current_time = None

    previous_frame = None
    next_frame = None

    has_lost_video = False
    is_full_screen = False
    has_unpaused_symbol_in_bar = False
    is_no_diff_between_frames = False

    possible_interruption_time = None
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

    def run_current_state(self, previous_frame, next_frame, time):
        self.previous_frame = previous_frame
        self.next_frame = next_frame
        self.current_time = time

        match self.current_state:
            case State.LOOKING_FOR_VIDEO:
                self.look_for_video()
            case State.LOADING_VIDEO:
                self.wait_for_video_to_load()
            case State.PLAYING_VIDEO:
                self.look_for_interruptions()
            case State.PAUSED_VIDEO:
                self.look_for_continuation()

    def change_state(self, state):
        self.current_state = state

    def look_for_video(self):
        videoExtensions.has_url_bar_changed(self.previous_frame, self.next_frame)
        biggest_contour = videoExtensions.find_biggest_contour(self.previous_frame)
        self.current_contour = videoExtensions.simplify_contour(biggest_contour)

        if videoExtensions.is_video_initializing(self.previous_frame, self.current_contour):
            eventPrinter.print_video_start_initializing(self.current_time)
            self.change_state(State.LOADING_VIDEO)

    def wait_for_video_to_load(self):
        self.try_look_for_bar()
        self.make_scroll_bar_check()
        self.check_is_video_starting()

    def look_for_interruptions(self):
        self.make_scroll_bar_check()
        self.check_for_loading_popup()

    def look_for_continuation(self):
        self.check_is_video_starting()
        return 0

    def try_look_for_bar(self):
        yt_bar_pause_image = None
        has_height_bar = self.yt_bar_y != float('-inf')

        if not has_height_bar:
            self.yt_bar_y = videoExtensions.try_get_yt_bar_height(self.previous_frame, self.current_contour)
        else:
            yt_bar_pause_image = videoExtensions.get_youtube_bar_image(self.previous_frame,
                                                                       self.current_contour,
                                                                       self.yt_bar_y)

        if yt_bar_pause_image is not None\
                and videoExtensions.is_unpaused_symbol_in_bar(yt_bar_pause_image) \
                and self.has_unpaused_symbol_in_bar is False:

            eventPrinter.print_video_end_initializing(self.current_time)
            self.has_unpaused_symbol_in_bar = True

    def check_is_video_starting(self):
        if self.has_unpaused_symbol_in_bar and videoExtensions.is_video_playing(self.previous_frame, self.next_frame, self.current_contour):
            eventPrinter.print_video_start_playing(self.current_time)
            self.has_unpaused_symbol_in_bar = False
            self.change_state(State.PLAYING_VIDEO)

    def check_is_video_continuing(self):
        if videoExtensions.is_video_playing(self.previous_frame, self.next_frame, self.current_contour):
            eventPrinter.print_video_resumed(self.current_time)
            self.change_state(State.PLAYING_VIDEO)

    def check_for_loading_popup(self):
        if self.possible_interruption_time is not None \
                and videoExtensions.has_loading_popup_appeared(self.previous_frame, self.next_frame, self.current_contour):
            eventPrinter.print_video_connection_interruption(self.current_time)
            self.change_state(State.PAUSED_VIDEO)
            return

        img_diff = videoExtensions.get_img_diff_between_frames(self.previous_frame,
                                                               self.next_frame,
                                                               self.current_contour)
        contours = videoExtensions.find_all_contours(img_diff)
        self.possible_interruption_time = self.current_time if len(contours) == 0 else None

    def make_scroll_bar_check(self):
        current_scroll_bar_bottom_edge = videoExtensions.find_bottom_scroll_bar_point(self.previous_frame,
                                                                                      self.FRAME_HEIGHT,
                                                                                      self.FRAME_WIDTH)

        if not self.has_scroll_bar:
            self.scroll_bar_bottom_edge = current_scroll_bar_bottom_edge
        elif current_scroll_bar_bottom_edge != self.scroll_bar_bottom_edge:
            self.has_lost_video = True
            # TBD - updating components position when scrolled
            # self.update_components_position(scroll_difference)

    def update_components_position(self, difference):
        if self.has_height_bar:
            self.yt_bar_y += difference

        for point in self.current_contour:
            point[0] += difference
            point[1] += difference
