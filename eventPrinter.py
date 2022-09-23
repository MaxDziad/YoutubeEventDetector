
def print_time_title_event(title, time):
    print(title + str(time))


def print_video_start_initializing(time):
    title = "Video started to initialize: "
    print_time_title_event(title, time)


def print_video_end_initializing(time):
    title = "Video ended initializing: "
    print_time_title_event(title, time)


def print_video_start_playing(time):
    title = "Video started playing: "
    print_time_title_event(title, time)
