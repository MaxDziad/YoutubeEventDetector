import cv2  # for reading video frame-by-frame
from videoStateMachine import VideoStateMachine

if __name__ == '__main__':

    # global parameters
    video_path = "VideoSources/test4.mp4"
    frame_reading_speed = 20
    frame_count = 0

    # video reading
    video = cv2.VideoCapture(video_path)
    ret, previous_frame = video.read()

    WIDTH = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    HEIGHT = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # initializing state machine
    stateMachine = VideoStateMachine()
    stateMachine.initialize(WIDTH, HEIGHT)

    while video.isOpened():
        is_read, current_frame = video.read()

        if is_read:
            frame_count += 1
            copied_previous_frame = previous_frame.copy()

            stateMachine.run_current_state(copied_previous_frame, current_frame)

            # cv2.imshow("Copied Previous Frame", copied_previous_frame)

            # cv2.waitKey waits in milliseconds before extracting next frame
            if cv2.waitKey(frame_reading_speed) == ord('q'):
                break

            previous_frame = current_frame
        else:
            break

    video.release()
    cv2.destroyAllWindows()
