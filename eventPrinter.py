
def print_time_title_event(title, time):
    hours = int(time / 3600000)
    minutes = int((time % 3600000) / 60000)
    seconds = round((time % 60000) / 1000, 2)

    time_message = str(hours) + "h " if hours > 0 else ""
    time_message += str(minutes) + "min " if hours > 0 or minutes > 0 else ""
    time_message += str(seconds) + "s"
    print(title + time_message)


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
    title = "Full screen toggled to " + str(value) + ":"
    print_time_title_event(title, time)


def print_url_changed(time):
    title = "URL changed: "
    print_time_title_event(title, time)


def print_video_lost(time):
    title = "Scroll bar changed: "
    print_time_title_event(title, time)


def print_video_come_back(time):
    title = "Video came back to place: "
    print_time_title_event(title, time)
