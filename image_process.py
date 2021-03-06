import numpy as np
import cv2 as cv
from advanced_lane_detection import draw_lanes_method3
import time

########################## Region-of-interest vertices###############################################
trap_bottom_width = 0.85  # width of bottom edge of trapezoid, expressed as percentage of image width
trap_top_width = 0.35  # ditto for top edge of trapezoid
trap_height = 0.6 # height of the trapezoid expressed as percentage of image height
########################## Region-of-interest vertices###############################################

def roi(img, vertices):
    mask = np.zeros_like(img)
    cv.fillPoly(mask, vertices, 255)
    masked = cv.bitwise_and(img, mask)
    return masked

def draw_lanes_method1(img, lines):

    try:
        #find the maximum y value and minimum y value
        ys = []
        for i in lines:
            for ii in i:
                ys += [ii[1], ii[3]]
        min_y = min(ys)
        max_y = max(ys)
        new_lines = []
        line_dict = {}
        ###########################################

        for id, line in enumerate(lines):
            for positions in line:
                x_p = (positions[0], positions[2])
                y_p = (positions[1], positions[3])
                #print(np.vstack([x_p, np.ones(len(x_p))]))
                A = np.vstack([x_p, np.ones(len(x_p))]).T
                print(A)
                m, b = np.linalg.lstsq(A, y_p)[0]
                #print(m)

                # Calculating our new, and improved, xs
                x1 = (min_y - b) / m
                x2 = (max_y - b) / m

                line_dict[id] = [m, b, [int(x1), min_y, int(x2), max_y]]
                new_lines.append([int(x1), min_y, int(x2), max_y])

        final_lanes = {}

        for idx in line_dict:
            final_lanes_copy = final_lanes.copy()
            m = line_dict[idx][0]
            b = line_dict[idx][1]
            line = line_dict[idx][2]

            if len(final_lanes) == 0:
                final_lanes[m] = [[m, b, line]]

            else:
                found_copy = False

                for other_ms in final_lanes_copy:

                    if not found_copy:
                        if abs(other_ms * 1.2) > abs(m) > abs(other_ms * 0.8):
                            if abs(final_lanes_copy[other_ms][0][1] * 1.2) > abs(b) > abs(
                                            final_lanes_copy[other_ms][0][1] * 0.8):
                                final_lanes[other_ms].append([m, b, line])
                                found_copy = True
                                break
                        else:
                            final_lanes[m] = [[m, b, line]]

        line_counter = {}

        for lanes in final_lanes:
            line_counter[lanes] = len(final_lanes[lanes])

        top_lanes = sorted(line_counter.items(), key=lambda item: item[1])[::-1][:2]

        lane1_id = top_lanes[0][0]
        lane2_id = top_lanes[1][0]

        def average_lane(lane_data):
            x1s = []
            y1s = []
            x2s = []
            y2s = []
            for data in lane_data:
                x1s.append(data[2][0])
                y1s.append(data[2][1])
                x2s.append(data[2][2])
                y2s.append(data[2][3])
            return int(np.mean(x1s)), int(np.mean(y1s)), int(np.mean(x2s)), int(np.mean(y2s))

        l1_x1, l1_y1, l1_x2, l1_y2 = average_lane(final_lanes[lane1_id])
        l2_x1, l2_y1, l2_x2, l2_y2 = average_lane(final_lanes[lane2_id])

        return [l1_x1, l1_y1, l1_x2, l1_y2], [l2_x1, l2_y1, l2_x2, l2_y2], lane1_id, lane2_id

    except Exception as e:
        print('cannot detect lanes')

def draw_lanes_method2(image,lines,color,thickness):
    left_lines=[]
    right_lines=[]
    ys = []
    for i in lines:
        for ii in i:
            ys += [ii[1], ii[3]]
    min_y = np.min(ys)
    max_y = np.max(ys)
    new_lines = []
    line_dict = {}
    for line in lines:
        for x1,y1,x2,y2 in line:
            x_p = (x1,x2)
            y_p = (y1,y2)
            A = np.vstack([x_p, np.ones(len(x_p))]).T
            m, b = np.linalg.lstsq(A, y_p)[0]
            if m <-0.5:
                left_lines.append(line)
            elif m >0.5:
                right_lines.append(line)
            x1 = (min_y - b) / m
            x2 = (max_y - b) / m
        if len(left_lines)>1:
            left_array = np.vstack(left_lines)
            # [0, 1, 2, 3]
            #[[x1,y1,x2,y2]
            # [x1,y1,x2,y2]
            # [x1,y1,x2,y2]]
            x1 = np.min(left_array[:0])
            x2 = np.max(left_array[:2])
            y1 = left_array[np.argmin(left_array[:, 0]), 1]
            y2 = left_array[np.argmin(left_array[:, 2]), 3]
        cv.line(image, (x1, y1), (x2, y2), color, thickness)
        if len(right_lines)>1:
            right_array = np.vstack(right_lines)
            # [0, 1, 2, 3]
            #[[x1,y1,x2,y2]
            # [x1,y1,x2,y2]
            # [x1,y1,x2,y2]]
            x1 = np.min(right_array[:0])
            x2 = np.max(right_array[:2])
            y1 = right_array[np.argmin(right_array[:, 0]), 1]
            y2 = right_array[np.argmin(right_array[:, 2]), 3]
        cv.line(image, (x1, y1), (x2, y2), color, thickness)

def process_image(raw_img,do_roi):
        processed_img = cv.resize(raw_img, (600, 480))
        resized_image = processed_img
        # M = cv.getPerspectiveTransform(processed_img,dst)
        # unwarped = cv.warpPerspective(processed_img,M,(600,480),flags=cv.INTER_LINEAR)
        # cv.imshow('unwarped image',unwarped)

        resized_data = processed_img
        processed_img = cv.cvtColor(processed_img, cv.COLOR_BGR2GRAY)
        processed_img = cv.GaussianBlur(processed_img, (3, 3), 0)
        #cv.imshow("1 after GaussianBlur", processed_img)
        processed_img = cv.Canny(processed_img, threshold1=150, threshold2=300)
        #cv.imshow("2 after Canny", processed_img)

        ###############do HoughP on roi image###########################
        imshape = processed_img.shape
        vertices = np.array([[ \
            ((imshape[1] * (1 - trap_bottom_width)) // 2, imshape[0]), \
            ((imshape[1] * (1 - trap_top_width)) // 2, imshape[0] - imshape[0] * trap_height), \
            (imshape[1] - (imshape[1] * (1 - trap_top_width)) // 2, imshape[0] - imshape[0] * trap_height), \
            (imshape[1] - (imshape[1] * (1 - trap_bottom_width)) // 2, imshape[0])]] \
            , dtype=np.int32)
        processed_img = roi(processed_img, vertices)
        #cv.imshow('roi image',processed_img)

        lines = cv.HoughLinesP(processed_img, 1, np.pi / 180, 180, 20, 30)
        ################################################################

        if (do_roi):
            # Use region of interest
            print("do roi")
            vertices = np.array([[10, 500], [10, 300], [300, 200], [500, 200], [800, 300], [800, 500]], np.int32)
            processed_img = roi(processed_img, [vertices])
            lines = cv.HoughLinesP(processed_img, 1, np.pi / 180, 180, 20, 15)
            l1, l2, m1, m2 = draw_lanes_method1(processed_img, lines)
            cv.line(processed_img, (l1[0], l1[1]), (l1[2], l1[3]), [0, 255, 0], 30)
            cv.imshow("processed image with hough lines", processed_img)
        else:
            print("doesnt do roi")
            try:
                # l1, l2, m1, m2 = draw_lanes_method1(processed_img, lines)
                # cv.line(resized_data, (l1[0], l1[1]), (l1[2], l1[3]), [0, 0, 255], 10)
                # cv.line(resized_data, (l2[0], l2[1]), (l2[2], l2[3]), [0, 0, 255], 10)
                # cv.imshow("processed image with hough lines", resized_data)

                # draw_lanes_method2(processed_img, lines, [0,0,255], 10)
                # print("11")
                # cv.imshow("processed image with hough lines", resized_data)

                draw_lanes_method3(resized_image, lines,color=[0,0,255],thickness=10)
                cv.imshow("Draw Lanes Method 3",resized_image)
            except:
                print("No line detected")

            #l1, l2, m1, m2 = draw_lanes(processed_img, lines)

            # cv.line(resized_data, (l1[0], l1[1]), (l1[2], l1[3]), [0, 0, 255], 10)
            # cv.imshow("3 processed image with hough lines", resized_data)

        # if cv.waitKey(25) & 0xFF == ord('q'):
        #     cv.destroyAllWindows()
        #     break