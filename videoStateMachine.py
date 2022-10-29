from enum import Enum

import eventPrinter
import videoExtensions
from videoEventWriter import VideoEventWriter


class State(Enum):
    LOOKING_FOR_VIDEO = 0
    LOADING_VIDEO = 1
    PLAYING_VIDEO = 2
    PAUSED_VIDEO = 3
    SITE_CHANGED = 4


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

    # event writer
    eventWriter = None
    new_event_id = 0

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

    current_img_diff_count = 0

    # video parameters
    had_video_once = False
    skip_frame = False
    has_lost_video = False
    is_full_screen = False
    has_loading_popup = False

    possible_loading_popup_appear_time = 0
    possible_loading_popup_disappear_time = 0
    video_contour = None
    scroll_bar_bottom_edge = float('inf')

    # references
    has_scroll_bar = scroll_bar_bottom_edge != float('inf')

    def __init__(self):
        self.current_state = State.LOOKING_FOR_VIDEO

    def initialize(self, width, height, file_name):
        self.FRAME_WIDTH = width
        self.FRAME_HEIGHT = height
        self.SCREEN_CONTOUR = [(0, 0), (0, height), (width, 0), (width, height)]
        self.eventWriter = VideoEventWriter(file_name, (width, height))
        self.new_event_id = 1

    def run_current_state(self, previous_frame, next_frame, time):
        self.previous_frame = previous_frame
        self.next_frame = next_frame
        self.current_time = time

        self.eventWriter.receive_frame(previous_frame)

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
            case State.SITE_CHANGED:
                self.look_to_start_state()

    def change_state(self, state):
        self.current_img_diff_count = 0
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
        self.check_for_url_change()
        self.check_for_loading_popup()

    def look_for_continuation(self):
        self.check_full_screen_toggle()
        self.check_for_url_change()
        self.check_is_video_continuing()

    def look_to_start_state(self):
        self.check_is_video_initializing()

        if self.current_state == State.SITE_CHANGED:
            self.check_for_loading_popup(True)

    def try_get_video_contour(self):
        if not self.had_video_once:
            biggest_contour = videoExtensions.find_biggest_contour(self.previous_frame)
            self.video_contour = videoExtensions.simplify_contour(biggest_contour)

    def check_is_video_initializing(self):
        if videoExtensions.is_video_initializing(self.previous_frame, self.video_contour):
            self.had_video_once = True
            eventPrinter.print_video_start_initializing(self.current_time, str(self.new_event_id))
            self.eventWriter.request_event_write(str(self.new_event_id))
            self.new_event_id += 1
            self.skip_frame = True
            self.change_state(State.LOADING_VIDEO)

    def check_for_url_change(self):
        if not self.is_full_screen and not self.skip_frame\
                and videoExtensions.has_url_bar_changed(self.previous_frame, self.next_frame):
            eventPrinter.print_url_changed(self.current_time, str(self.new_event_id))
            self.eventWriter.request_event_write(str(self.new_event_id))
            self.new_event_id += 1
            self.scroll_bar_bottom_edge = float('inf')
            self.skip_frame = True
            self.change_state(State.SITE_CHANGED)
            self.reset_video_parameters()

    def check_is_video_starting(self):
        if videoExtensions.is_video_playing(self.previous_frame, self.next_frame, self.get_current_video_contour()):
            eventPrinter.print_video_start_playing(self.current_time, str(self.new_event_id))
            self.eventWriter.request_event_write(str(self.new_event_id))
            self.new_event_id += 1
            self.change_state(State.PLAYING_VIDEO)

    def check_is_video_continuing(self):
        has_found, diff_count = videoExtensions.has_loading_popup_appeared(
            self.get_no_camera_frame(self.previous_frame),
            self.get_no_camera_frame(self.next_frame),
            self.get_current_video_contour(),
            self.current_img_diff_count)

        if not has_found or diff_count > self.current_img_diff_count:
            if self.possible_loading_popup_disappear_time == 0:
                self.possible_loading_popup_disappear_time = self.current_time

            self.current_not_load_pop_count += 1
            self.current_img_diff_count = diff_count

            if self.current_not_load_pop_count >= self.MAX_NOT_LOAD_POP_COUNT:
                self.current_not_load_pop_count = 0
                self.current_img_diff_count = 0
                eventPrinter.print_video_resumed(self.possible_loading_popup_disappear_time, str(self.new_event_id))
                self.eventWriter.request_instant_event_write(str(self.new_event_id))
                self.new_event_id += 1
                self.possible_loading_popup_disappear_time = 0
                self.change_state(State.PLAYING_VIDEO)

        else:
            self.possible_loading_popup_disappear_time = 0
            self.current_not_load_pop_count = 0

    def check_full_screen_toggle(self):
        if videoExtensions.is_full_screen_toggled(self.previous_frame, self.next_frame):
            self.skip_frame = True
            self.is_full_screen = not self.is_full_screen
            eventPrinter.print_full_screen_toggle(self.current_time, self.is_full_screen, str(self.new_event_id))
            self.eventWriter.request_event_write(str(self.new_event_id))
            self.new_event_id += 1

    def check_for_loading_popup(self, black_background=False):
        has_found, diff_count = videoExtensions.has_loading_popup_appeared(self.get_no_camera_frame(self.previous_frame),
                                                                           self.get_no_camera_frame(self.next_frame),
                                                                           self.get_current_video_contour(),
                                                                           self.current_img_diff_count)
        self.current_img_diff_count = diff_count

        if black_background and not videoExtensions.is_video_initializing(self.previous_frame, self.video_contour, 4):
            return

        if has_found:
            if self.possible_loading_popup_appear_time == 0:
                self.possible_loading_popup_appear_time = self.current_time

            self.current_load_pop_count += 1

            if self.current_load_pop_count >= self.MAX_LOAD_POP_COUNT:
                self.current_load_pop_count = 0
                self.current_img_diff_count = 0

                if self.current_state != State.PLAYING_VIDEO:
                    eventPrinter.print_video_start_playing(self.possible_loading_popup_appear_time, str(self.new_event_id))
                    self.eventWriter.request_instant_event_write(str(self.new_event_id))
                    self.new_event_id += 1

                eventPrinter.print_video_connection_interruption(self.possible_loading_popup_appear_time, str(self.new_event_id))
                self.eventWriter.request_instant_event_write(str(self.new_event_id))
                self.new_event_id += 1
                self.possible_loading_popup_appear_time = 0
                self.change_state(State.PAUSED_VIDEO)
        else:
            self.possible_loading_popup_appear_time = 0
            self.current_load_pop_count = 0

# !Not implemented!
    def check_scroll_bar(self):
        if self.is_full_screen or self.skip_frame:
            return

        current_scroll_bar_bottom_edge = videoExtensions.find_bottom_scroll_bar_point(self.previous_frame,
                                                                                      self.FRAME_HEIGHT,
                                                                                      self.FRAME_WIDTH)
        if self.scroll_bar_bottom_edge == float('inf'):
            self.scroll_bar_bottom_edge = current_scroll_bar_bottom_edge

        if self.scroll_bar_bottom_edge != current_scroll_bar_bottom_edge:
            self.scroll_bar_bottom_edge = float('inf')
            eventPrinter.print_video_lost(self.current_time, str(self.new_event_id))
            self.eventWriter.request_event_write(str(self.new_event_id))
            self.new_event_id += 1
            self.has_lost_video = True
            # self.change_state(State.SCROLLED_VIDEO)

# !Not implemented!
    def has_video_came_back(self):
        if not self.skip_frame and \
                videoExtensions.is_video_back_in_place(self.get_no_camera_frame(self.previous_frame), self.video_contour):
            self.current_come_back_count += 1

            if self.current_come_back_count >= self.MAX_COME_BACK_COUNT:
                self.has_lost_video = False
                eventPrinter.print_video_come_back(self.current_time, str(self.new_event_id))
                self.eventWriter.request_event_write(str(self.new_event_id))
                self.new_event_id += 1
                self.change_state(self.previous_state)

        else:
            self.current_come_back_count = 0

    def reset_video_parameters(self):
        self.has_lost_video = False
        self.scroll_bar_bottom_edge = float('inf')

    def try_remove_frame_skip(self):
        if self.skip_frame:
            self.current_frame_skip_count += 1

        if self.current_frame_skip_count >= self.MAX_FRAME_SKIP_COUNT:
            self.current_frame_skip_count = 0
            self.skip_frame = False

    def get_current_video_contour(self):
        return self.SCREEN_CONTOUR if self.is_full_screen else self.video_contour

    def get_no_camera_frame(self, frame):
        return videoExtensions.get_no_camera_frame(frame, self.FRAME_WIDTH)
