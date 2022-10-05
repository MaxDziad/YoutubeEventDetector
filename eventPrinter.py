
def print_time_title_event(title, time):
    time = round((time / 1000), 3)
    print(title + str(time) + " s")


def print_video_start_initializing(time):
    title = "Video started to initialize: "
    print_time_title_event(title, time)


def print_video_end_initializing(time):
    title = "Video ended initializing: "
    print_time_title_event(title, time)


def print_video_start_playing(time):
    title = "Video started playing: "
    print_time_title_event(title, time)


def print_video_connection_interruption(time):
    title = "Video connection interruption: "
    print_time_title_event(title, time)


def print_video_resumed(time):
    title = "Video resumed: "
    print_time_title_event(title, time)


def print_full_screen_toggle(time, value):
    title = "Fullscreen toggled to: " + str(value)
    print_time_title_event(title, time)


def print_url_changed(time):
    title = "URL changed: "
    print_time_title_event(title, time)


def print_scroll_bar_changed(time):
    title = "Scroll bar changed: "
    print_time_title_event(title,time)