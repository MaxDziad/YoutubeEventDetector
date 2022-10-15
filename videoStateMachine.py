from enum import Enum

import eventPrinter
import videoExtensions


class State(Enum):
    LOOKING_FOR_VIDEO = 0
    LOADING_VIDEO = 1
    PLAYING_VIDEO = 2
    PAUSED_VIDEO = 3
    SCROLLED_VIDEO = 4
    SITE_CHANGED = 5


class VideoStateMachine:
    # static parameters
    FRAME_WIDTH = 0
    FRAME_HEIGHT = 0
    SCREEN_CONTOUR = None

    MAX_FRAME_SKIP_COUNT = 5
    MAX_SCROLL_BAR_COUNT = 5
    MAX_COME_BACK_COUNT = 20
    MAX_LOAD_POP_COUNT = 15
    MAX_NOT_LOAD_POP_COUNT = 15

    # dynamic parameters
    previous_state = None
    current_state = None
    current_time = None

    previous_frame = None
    next_frame = None

    current_frame_skip_count = 0
    current_scroll_bar_count = 0
    current_come_back_count = 0
    current_load_pop_count = 0
    current_not_load_pop_count = 0

    # video parameters
    had_video_once = False
    skip_frame = False
    has_lost_video = False
    is_full_screen = False
    has_loading_popup = False

    possible_interruption_time = None
    video_contour = None
    scroll_bar_bottom_edge = float('inf')
    possible_scroll_bar_edge = 0

    # references
    has_scroll_bar = scroll_bar_bottom_edge != float('inf')

    def __init__(self):
        self.current_state = State.LOOKING_FOR_VIDEO

    def initialize(self, width, height):
        self.FRAME_WIDTH = width
        self.FRAME_HEIGHT = height
        self.SCREEN_CONTOUR = [(0, 0), (0, height), (width, 0), (width, height)]

    def run_current_state(self, previous_frame, next_frame, time):
        self.previous_frame = previous_frame
        self.next_frame = next_frame
        self.current_time = time

        self.try_remove_frame_skip()
        if self.skip_frame:
            return

        match self.current_state:
            case State.LOOKING_FOR_VIDEO:
                self.look_for_video()
            case State.LOADING_VIDEO:
                self.wait_for_video_to_load()
            case State.PLAYING_VIDEO:
                self.look_for_interruptions()
            case State.PAUSED_VIDEO:
                self.look_for_continuation()
            case State.SCROLLED_VIDEO:
                self.look_for_comeback()
            case State.SITE_CHANGED:
                self.look_to_start_state()

    def change_state(self, state):
        self.previous_state = self.current_state
        self.current_state = state

    def look_for_video(self):
        self.try_get_video_contour()
        self.check_is_video_initializing()

    def wait_for_video_to_load(self):
        self.check_full_screen_toggle()
        self.check_for_url_change()
        self.check_for_loading_popup()
        self.check_is_video_starting()

    def look_for_interruptions(self):
        self.has_video_came_back()
        self.check_full_screen_toggle()
        self.check_scroll_bar()
        self.check_for_url_change()
        self.check_for_loading_popup()

    def look_for_continuation(self):
        self.check_full_screen_toggle()
        self.check_scroll_bar()
        self.check_for_url_change()
        self.check_is_video_continuing()

    def look_for_comeback(self):
        self.check_for_url_change()
        self.has_video_came_back()

    def look_to_start_state(self):
        self.check_is_video_initializing()

        if self.current_state == State.SITE_CHANGED:
            self.check_for_loading_popup()

    def try_get_video_contour(self):
        if not self.had_video_once:
            biggest_contour = videoExtensions.find_biggest_contour(self.previous_frame)
            self.video_contour = videoExtensions.simplify_contour(biggest_contour)

    def check_is_video_initializing(self):
        if videoExtensions.is_video_initializing(self.previous_frame, self.video_contour):
            self.had_video_once = True
            eventPrinter.print_video_start_initializing(self.current_time)
            self.change_state(State.LOADING_VIDEO)

    def check_for_url_change(self):
        if not self.is_full_screen and not self.skip_frame\
                and videoExtensions.has_url_bar_changed(self.previous_frame, self.next_frame):
            eventPrinter.print_url_changed(self.current_time)
            skip_frame = True
            self.change_state(State.SITE_CHANGED)
            self.reset_video_parameters()

    def check_is_video_starting(self):
        if videoExtensions.is_video_playing(self.previous_frame, self.next_frame, self.get_current_video_contour()):
            eventPrinter.print_video_start_playing(self.current_time)
            self.change_state(State.PLAYING_VIDEO)

    def check_is_video_continuing(self):
        if not videoExtensions.has_loading_popup_appeared(self.previous_frame,
                                                          self.next_frame,
                                                          self.get_current_video_contour()):
            self.current_not_load_pop_count += 1

            if self.current_not_load_pop_count >= self.MAX_NOT_LOAD_POP_COUNT:
                self.current_not_load_pop_count = 0
                eventPrinter.print_video_resumed(self.current_time)
                self.change_state(State.PLAYING_VIDEO)

        else:
            self.current_not_load_pop_count = 0

    def check_full_screen_toggle(self):
        if videoExtensions.is_full_screen_toggled(self.previous_frame, self.next_frame):
            self.is_full_screen = not self.is_full_screen
            eventPrinter.print_full_screen_toggle(self.current_time, self.is_full_screen)
            self.skip_frame = True

    def check_for_loading_popup(self):
        if videoExtensions.has_loading_popup_appeared(self.previous_frame,
                                                      self.next_frame,
                                                      self.get_current_video_contour()):
            self.current_load_pop_count += 1

            if self.current_load_pop_count >= self.MAX_LOAD_POP_COUNT:
                self.current_load_pop_count = 0

                if self.current_state != State.PLAYING_VIDEO:
                    eventPrinter.print_video_start_playing(self.current_time)

                eventPrinter.print_video_connection_interruption(self.current_time)
                self.change_state(State.PAUSED_VIDEO)
        else:
            self.current_load_pop_count = 0

    def check_scroll_bar(self):
        if self.is_full_screen:
            self.current_scroll_bar_count = 0
            self.scroll_bar_bottom_edge = float('inf')
            return

        current_scroll_bar_bottom_edge = videoExtensions.find_bottom_scroll_bar_point(self.previous_frame,
                                                                                      self.FRAME_HEIGHT,
                                                                                      self.FRAME_WIDTH)

        if self.possible_scroll_bar_edge == current_scroll_bar_bottom_edge:
            self.current_scroll_bar_count += 1
        else:
            self.current_scroll_bar_count = 0

        if self.current_scroll_bar_count >= self.MAX_SCROLL_BAR_COUNT:
            self.scroll_bar_bottom_edge = current_scroll_bar_bottom_edge

        if self.scroll_bar_bottom_edge != float('inf') and current_scroll_bar_bottom_edge != self.scroll_bar_bottom_edge:
            eventPrinter.print_video_lost(self.current_time)
            self.current_scroll_bar_count = 0
            self.has_lost_video = True
            self.change_state(State.SCROLLED_VIDEO)

        self.possible_scroll_bar_edge = current_scroll_bar_bottom_edge

    def has_video_came_back(self):
        if not self.skip_frame and \
                videoExtensions.is_video_back_in_place(self.get_no_camera_frame(self.previous_frame), self.video_contour):
            self.current_come_back_count += 1

            if self.current_come_back_count >= self.MAX_COME_BACK_COUNT:
                self.has_lost_video = False
                eventPrinter.print_video_come_back(self.current_time)
                self.change_state(self.previous_state)

        else:
            self.current_come_back_count = 0

    def reset_video_parameters(self):
        self.has_lost_video = False
        self.possible_interruption_time = None
        self.scroll_bar_bottom_edge = float('inf')

    def try_remove_frame_skip(self):
        if self.skip_frame:
            self.current_frame_skip_count += 1

        if self.current_scroll_bar_count >= self.MAX_FRAME_SKIP_COUNT:
            self.skip_frame = False

    def get_current_video_contour(self):
        return self.SCREEN_CONTOUR if self.is_full_screen else self.video_contour

    def get_no_camera_frame(self, frame):
        return videoExtensions.get_no_camera_frame(frame, self.FRAME_WIDTH)
