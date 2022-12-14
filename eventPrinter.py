
def print_time_title_event(title, time, file, event_id):
    hours = int(time / 3600000)
    minutes = int((time % 3600000) / 60000)
    seconds = round((time % 60000) / 1000, 2)

    time_message = str(hours) + "h " if hours > 0 else ""
    time_message += str(minutes) + "min " if hours > 0 or minutes > 0 else ""
    time_message += str(seconds) + "s"

    full_event = str(event_id) + ";" + title + ";" + str(time) + ";" + time_message + "\n"
    file.write(full_event)


def print_video_start_initializing(file, time, event_id):
    title = "Video started to initialize: "
    print_time_title_event(title, time, file, event_id)


def print_video_end_initializing(file, time, event_id):
    title = "Video ended initializing: "
    print_time_title_event(title, time, file, event_id)


def print_video_start_playing(file, time, event_id):
    title = "Video started playing: "
    print_time_title_event(title, time, file, event_id)


def print_video_connection_interruption(file, time, event_id):
    title = "Video connection interruption: "
    print_time_title_event(title, time, file, event_id)


def print_video_resumed(file, time, event_id):
    title = "Video resumed: "
    print_time_title_event(title, time, file, event_id)


def print_full_screen_toggle(file, time, value, event_id):
    title = "Full screen toggled to " + str(value) + ":"
    print_time_title_event(title, time, file, event_id)


def print_url_changed(file, time, event_id):
    title = "URL changed: "
    print_time_title_event(title, time, file, event_id)


# Not Implemented!
def print_video_lost(file, time, event_id):
    title = "Scroll bar changed: "
    print_time_title_event(title, time, file, event_id)


# Not Implemented!
def print_video_come_back(file, time, event_id):
    title = "Video came back to place: "
    print_time_title_event(title, time, file, event_id)
