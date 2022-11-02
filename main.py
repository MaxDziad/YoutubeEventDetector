import cv2
import os
from videoStateMachine import VideoStateMachine

if __name__ == '__main__':

    # global parameters
    frame_reading_speed = 10

    # reading each video file in catalogue
    video_catalogue_path = "VideoSources"

    for file in os.listdir(video_catalogue_path):
        if file.endswith(".mp4"):
            video_path = video_catalogue_path + "/" + file
            print("Work on " + file + " has started... Please don't close the application.")

            # video reading
            video = cv2.VideoCapture(video_path)
            ret, previous_frame = video.read()

            WIDTH = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
            HEIGHT = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # initializing state machine
            stateMachine = VideoStateMachine()
            stateMachine.initialize(WIDTH, HEIGHT, file[0:-4])

            while video.isOpened():
                is_read, current_frame = video.read()

                if is_read:
                    copied_previous_frame = previous_frame.copy()
                    current_time = video.get(cv2.CAP_PROP_POS_MSEC)
                    stateMachine.run_current_state(copied_previous_frame, current_frame, current_time)

                    # enable both lines for activating frame debugging
                    #if cv2.waitKey(frame_reading_speed) == ord('q'):
                        #break

                    previous_frame = current_frame
                else:
                    break

            stateMachine.save_text_file()
            video.release()
            cv2.destroyAllWindows()
            print("Work on " + file + "has ended.")

    print("Application finished working.")
