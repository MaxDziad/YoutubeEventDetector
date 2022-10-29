import numpy as np
import cv2

# global parameters
BLACK = [0, 0, 0]
WHITE = [255, 255, 255]
DEBUG_COLOR = [0, 255, 0]
FOURCC = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')


def find_bottom_scroll_bar_point(frame, height, width):
    screen_to_scroll_bar_spacing = 9

    for iy in range(height - 2, 1, -1):
        point_x = width - screen_to_scroll_bar_spacing
        previous_point = frame[iy - 1][point_x]
        next_point = frame[iy][point_x]
        if not np.array_equal(previous_point, next_point):
            # DEBUG
            # cv2.circle(frame, [point_x, iy], 10, DEBUG_COLOR, -1)
            # cv2.imshow("LOL", frame)

            return iy

    return float('inf')


def has_url_bar_changed(previous_frame, next_frame):
    upper_left_point = (120, 45)
    lower_right_point = (1300, 60)
    img_diff = get_img_diff_between_frames(previous_frame, next_frame, [upper_left_point, lower_right_point])
    contours = find_all_contours(img_diff, 100)
    return len(contours) >= 30


def is_full_screen_toggled(previous_frame, next_frame):
    upper_left_point = (1300, 5)
    lower_right_point = (1315, 20)
    img_diff = get_img_diff_between_frames(previous_frame, next_frame, [upper_left_point, lower_right_point])
    contours = find_all_contours(img_diff)
    return len(contours) > 0


def find_all_hard_contours(frame):
    modified_frame = frame
    modified_frame = apply_grayscale(modified_frame)
    modified_frame = apply_threshold(modified_frame)

    # applying close morphology
    kernel = np.ones((111, 111), np.uint8)
    modified_frame = cv2.morphologyEx(modified_frame, cv2.MORPH_OPEN, kernel)

    # inverting colours
    modified_frame = 255 - modified_frame

    contours = cv2.findContours(modified_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]

    # DEBUG
    # cv2.imshow("lol", modified_frame)

    return contours


def find_all_contours(frame, trs_value=5):
    modified_frame = frame
    modified_frame = apply_grayscale(modified_frame)
    modified_frame = apply_threshold(modified_frame, trs_value)

    contours = cv2.findContours(modified_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]

    # DEBUG
    # cv2.imshow("lol", modified_frame)

    return contours


def find_all_smooth_contours(frame, trs_value=5):
    modified_frame = frame
    modified_frame = apply_grayscale(modified_frame)
    modified_frame = apply_threshold(modified_frame, trs_value)

    # blur image for smoothing sharp edges
    modified_frame = cv2.GaussianBlur(modified_frame, (5, 5), 0)

    #  dilation for noise and imperfections removal
    modified_frame = cv2.dilate(modified_frame, None, iterations=4)

    contours = cv2.findContours(modified_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]

    # DEBUG
    # cv2.imshow("lol", modified_frame)

    return contours


def apply_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def apply_threshold(image, min_thresh=0):
    return cv2.threshold(image, min_thresh, 255, cv2.THRESH_BINARY)[1]


def find_biggest_contour(frame):
    all_contours = find_all_hard_contours(frame)
    return max(all_contours, key=cv2.contourArea)


def get_no_camera_frame(frame, frame_width):
    img = frame.copy()
    cv2.rectangle(img, (1332, 0), (frame_width, 327), 255, -1)
    return img


def get_youtube_bar_image(frame, contour, bar_height):
    min_x, max_x, min_y, max_y = find_min_max_coordinates(contour)

    if bar_height > max_y or bar_height < min_y:
        return None

    bar_image = frame[bar_height:max_y, min_x:min_x + 50]
    return bar_image


def simplify_contour(contour):
    ensured_contour = []

    for point in contour:
        tuple_rem_point = point[0]
        if not is_point_close_to_others(ensured_contour, tuple_rem_point, 200):
            ensured_contour.append([tuple_rem_point[0], tuple_rem_point[1]])

    ndarray_contour = np.array(ensured_contour)
    return ndarray_contour


def is_video_playing(previous_frame, next_frame, contour):
    num_contours_threshold = 100
    img_diff = get_img_diff_between_frames(previous_frame, next_frame, contour)
    contours = find_all_contours(img_diff)
    return len(contours) > num_contours_threshold


def is_point_close_to_others(point_list, new_point, dist_tres):
    for current_point in point_list:
        if abs(current_point[0] - new_point[0]) <= dist_tres and abs(current_point[1] - new_point[1]) <= dist_tres:
            return True

    return False


def is_video_initializing(frame, contour, grid_check_size=10):
    # higher value gives error -1073740940 (0xC0000374) which means Access Violation error (heap to big?)
    return is_contour_rectangular(contour) and is_contour_all_black(frame, contour, grid_check_size)


def is_contour_rectangular(contour):
    return len(contour) == 4


def is_contour_all_black(frame, contour, grid_size):
    grid_size += 1
    min_x, max_x, min_y, max_y = find_min_max_coordinates(contour)
    contour_width = max_x - min_x
    contour_height = max_y - min_y
    x_spacing = int(contour_width / grid_size)
    y_spacing = int(contour_height / grid_size)
    possible_mouse_encounters = 0

    for ix in range(1, grid_size):
        for iy in range(1, grid_size):
            point_x = int(min_x + ix * x_spacing)
            point_y = int(min_y + iy * y_spacing)
            current_pixel = frame[point_y][point_x]

            if not np.array_equal(current_pixel, BLACK):
                possible_mouse_encounters += 1

                if possible_mouse_encounters > 1:
                    return False

            # DEBUG
            # cv2.circle(frame, [point_x, point_y], 10, debug_color, -1)

    return True


def get_no_bar_contour(contour, bar_height):
    min_x, max_x, min_y, max_y = find_min_max_coordinates(contour)
    no_bar_contour = [[min_x, min_y], [max_x, bar_height - 5]]
    return no_bar_contour


def get_img_diff_between_frames(prev_frame, next_frame, contour=None):
    prev_img = get_contour_img(prev_frame, contour) if contour is not None else prev_frame
    next_img = get_contour_img(next_frame, contour) if contour is not None else next_frame
    img_diff = cv2.absdiff(prev_img, next_img)

    # DEBUG
    # cv2.imshow("lol", img_diff)

    return img_diff


def has_loading_popup_appeared(prev_frame, next_frame, contour, img_diff_count):
    diff_count = img_diff_count
    img_diff = get_img_diff_between_frames(prev_frame, next_frame)

    no_popup_img = img_diff.copy()
    paint_img_popup_place(no_popup_img, contour, 0.1, 0.2)
    no_popup_img = get_contour_img(no_popup_img, contour)
    no_popup_contours = find_all_contours(no_popup_img, 5)

    popup_img = get_contour_img(img_diff, contour, 0.1, 0.2)
    popup_contours = find_all_smooth_contours(popup_img)

    has_possible_popup = 0 < len(popup_contours) <= 4

    if len(no_popup_contours) >= 35:
        diff_count += 1

    if diff_count == 3:
        return False, 0

    return has_possible_popup, diff_count


def is_video_back_in_place(frame, contour):
    min_x, max_x, min_y, max_y = find_min_max_coordinates(contour)
    width = max_x - min_x
    pixel_above = (max_x - int(width/2), min_y - 4)
    return are_pixels_inline_same(frame, pixel_above, pixel_above[0], pixel_above[1], 15, 10)


def paint_img_popup_place(frame, contour, width_offset=1.0, height_offset=1.0):
    min_x, max_x, min_y, max_y = find_min_max_coordinates(contour)
    half_height = int((max_y - min_y) / 2)
    half_width = int((max_x - min_x) / 2)

    new_min_y = min_y + half_height - int(height_offset * half_height)
    new_max_y = max_y - half_height + int(height_offset * half_height)
    new_min_x = min_x + half_width - int(width_offset * half_width)
    new_max_x = max_x - half_width + int(width_offset * half_width)

    cv2.rectangle(frame, (new_min_x, new_min_y), (new_max_x, new_max_y),DEBUG_COLOR, -1)

    # DEBUG
    # cv2.imshow("LOL", frame)


def get_contour_img(frame, contour, width_offset=1.0, height_offset=1.0):
    min_x, max_x, min_y, max_y = find_min_max_coordinates(contour)
    half_height = int((max_y - min_y) / 2)
    half_width = int((max_x - min_x) / 2)

    new_min_y = min_y + half_height - int(height_offset * half_height)
    new_max_y = max_y - half_height + int(height_offset * half_height)
    new_min_x = min_x + half_width - int(width_offset * half_width)
    new_max_x = max_x - half_width + int(width_offset * half_width)

    return frame[new_min_y:new_max_y, new_min_x:new_max_x]


def are_pixels_inline_same(frame, pixel, x_position, y_position, checks=3, spacing=100):
    possible_mouse_encounters = 0

    for ix in range(1, checks + 1):
        right_x = x_position + int(spacing * ix)
        left_x = x_position - int(spacing * ix)
        right_pixel = frame[y_position][right_x]
        left_pixel = frame[y_position][left_x]

        if not np.array_equal(pixel, right_pixel):
            possible_mouse_encounters += 1

        if not np.array_equal(pixel, left_pixel):
            possible_mouse_encounters += 1

        # DEBUG
        # cv2.circle(frame, [right_x, y_position], 10, DEBUG_COLOR, 1)
        # cv2.circle(frame, [left_x, y_position], 10, DEBUG_COLOR, 1)
        # cv2.imshow("LOL", frame)

        if possible_mouse_encounters > 1:
            return False

    return True


def find_min_max_coordinates(contour):
    min_x = float('inf')
    max_x = 0
    min_y = float('inf')
    max_y = 0

    for point in contour:
        current_x = point[0]
        current_y = point[1]

        if current_x < min_x:
            min_x = current_x

        if current_x > max_x:
            max_x = current_x

        if current_y < min_y:
            min_y = current_y

        if current_y > max_y:
            max_y = current_y

    return min_x, max_x, min_y, max_y


def save_video_event(images, video_path, resolution):
    out = cv2.VideoWriter(video_path, FOURCC, 60, resolution)

    for image in images:
        out.write(image)

    out.release()
