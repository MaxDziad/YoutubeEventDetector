# extension methods for manipulating video frame
import numpy as np
import cv2

# global parameters
BLACK = [0, 0, 0]
WHITE = [255, 255, 255]
DEBUG_COLOR = [0, 255, 0]


def find_bottom_scroll_bar_point(frame, height, width):
    screen_to_scroll_bar_spacing = 9

    for iy in range(height - 2, 1, -1):
        point_x = width - screen_to_scroll_bar_spacing
        previous_point = frame[iy - 1][point_x]
        next_point = frame[iy][point_x]
        if not np.array_equal(previous_point, next_point):

            # DEBUG
            # cv2.circle(frame, [point_x, iy], 10, debug_color, -1)

            return iy

    return float('inf')


def find_all_contours(frame):
    # applying gray scale
    modified_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # applying threshold
    modified_frame = cv2.threshold(modified_frame, 0, 255, cv2.THRESH_BINARY)[1]

    # applying close morphology
    kernel = np.ones((111, 111), np.uint8)
    modified_frame = cv2.morphologyEx(modified_frame, cv2.MORPH_OPEN, kernel)

    # inverting colours
    modified_frame = 255 - modified_frame

    contours = cv2.findContours(modified_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]

    return contours


def find_biggest_contour(frame):
    all_contours = find_all_contours(frame)
    return max(all_contours, key=cv2.contourArea)


def is_unpaused_symbol_in_bar(frame):
    all_contours = find_all_contours(frame)
    return len(all_contours) == 2


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
        if not is_point_close_to_others(ensured_contour, tuple_rem_point, 5):
            ensured_contour.append([tuple_rem_point[0], tuple_rem_point[1]])

    ndarray_contour = np.array(ensured_contour)
    return ndarray_contour


def is_point_close_to_others(point_list, new_point, dist_tres):
    for current_point in point_list:
        if abs(current_point[0] - new_point[0]) <= dist_tres and abs(current_point[1] - new_point[1]) <= dist_tres:
            return True

    return False


def is_video_initializing(frame, contour):
    # higher value gives error -1073740940 (0xC0000374) which means Access Violation error (heap to big?)
    grid_check_size = 3
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


def try_get_yt_bar_height(frame, contour):
    min_x, max_x, min_y, max_y = find_min_max_coordinates(contour)
    contour_width = max_x - min_x
    center_x = min_x + int(contour_width / 2)

    for y in range(max_y, min_y, -1):
        current_pixel = frame[y][center_x]

        if not np.array_equal(current_pixel, BLACK) and are_pixels_inline_same(frame, current_pixel, center_x, y):
            return y

    return float('-inf')


def are_pixels_inline_same(frame, pixel, x_position, y_position):
    possible_mouse_encounters = 0
    check_spacing = 100
    one_side_count_checks = 3

    for ix in range(1, one_side_count_checks + 1):
        right_x = x_position + int(check_spacing * ix)
        left_x = x_position - int(check_spacing * ix)
        right_pixel = frame[y_position][right_x]
        left_pixel = frame[y_position][left_x]

        if not np.array_equal(pixel, right_pixel):
            possible_mouse_encounters += 1

        if not np.array_equal(pixel, left_pixel):
            possible_mouse_encounters += 1

        # DEBUG
        # cv2.circle(frame, [right_x, y_position], 10, debug_color, -1)
        # cv2.circle(frame, [left_x, y_position], 10, debug_color, -1)

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
