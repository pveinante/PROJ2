import cv2
import numpy as np
import dlib
import time

# Initialisation
img = cv2.imread("paul.jpg")
img2 = cv2.imread("antonin.jpg")
height, width, channels = img2.shape
img2_new_face = np.zeros((height, width, channels), np.uint8)
img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
mask = np.zeros_like(img_gray)
img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
def extract_index_nparray(nparray):
    index = None
    for num in nparray[0]:
        index = num
        break
    return index

# Detection des marqueurs faciaux sur le visage 1
faces = detector(img_gray)
for face in faces:
    landmarks = predictor(img_gray, face)
    landmarks_points = []
    for n in range(0, 68):
        x = landmarks.part(n).x
        y = landmarks.part(n).y
        landmarks_points.append((x, y))
        #cv2.circle(img, (x, y), 3, (0, 0, 255), -1) # dessiner les marqueurs

    # Definir l'enveloppe convexe des marqueurs 
    points = np.array(landmarks_points, np.int32)
    convexhull = cv2.convexHull(points)
    #cv2.polylines(img, [convexhull], True, (255, 0, 0), 3) # dessiner l'enveloppe
    cv2.fillConvexPoly(mask, convexhull, 255)
    face_image_1 = cv2.bitwise_and(img, img, mask=mask) # afficher le masque découpé dans un image

    # Triangularisation
    rect = cv2.boundingRect(convexhull)
    subdiv = cv2.Subdiv2D(rect)
    subdiv.insert(landmarks_points)
    triangles = subdiv.getTriangleList()
    triangles = np.array(triangles, dtype=np.int32)
    indexes_triangles = []
    for t in triangles:
        pt1 = (t[0], t[1])
        pt2 = (t[2], t[3])
        pt3 = (t[4], t[5])
        #cv2.line(face_image_1, pt1, pt2, (0, 0, 255), 1) # afficher les triangles
        #cv2.line(face_image_1, pt2, pt3, (0, 0, 255), 1)
        #cv2.line(face_image_1, pt1, pt3, (0, 0, 255), 1)

        # Enregistrer les triangles en fonction des index des marqueurs
        index_pt1 = np.where((points == pt1).all(axis=1))
        index_pt1 = extract_index_nparray(index_pt1)
        index_pt2 = np.where((points == pt2).all(axis=1))
        index_pt2 = extract_index_nparray(index_pt2)
        index_pt3 = np.where((points == pt3).all(axis=1))
        index_pt3 = extract_index_nparray(index_pt3)
        if index_pt1 is not None and index_pt2 is not None and index_pt3 is not None:
            triangle = [index_pt1, index_pt2, index_pt3]
            indexes_triangles.append(triangle)

# Detection des marqueurs faciaux sur le visage 2 
faces2 = detector(img2_gray)
for face in faces2:
    landmarks = predictor(img2_gray, face)
    landmarks_points2 = []
    for n in range(0, 68):
        x = landmarks.part(n).x
        y = landmarks.part(n).y
        landmarks_points2.append((x, y))
        #cv2.circle(img2, (x, y), 3, (0, 0, 255), -1) # dessiner les marqueurs
    points2 = np.array(landmarks_points2, np.int32)
    convexhull2 = cv2.convexHull(points2)

lines_space_new_face = np.zeros_like(img2)

# Triangularisations des 2 visages
for triangle_index in indexes_triangles:
    
    # Triangularisation du premier visage
    tr1_pt1 = landmarks_points[triangle_index[0]]
    tr1_pt2 = landmarks_points[triangle_index[1]]
    tr1_pt3 = landmarks_points[triangle_index[2]]
    triangle1 = np.array([tr1_pt1, tr1_pt2, tr1_pt3], np.int32)


    rect1 = cv2.boundingRect(triangle1)
    (x, y, w, h) = rect1
    cropped_triangle = img[y: y + h, x: x + w]
    cropped_tr1_mask = np.zeros((h, w), np.uint8)


    points = np.array([[tr1_pt1[0] - x, tr1_pt1[1] - y],
                       [tr1_pt2[0] - x, tr1_pt2[1] - y],
                       [tr1_pt3[0] - x, tr1_pt3[1] - y]], np.int32)

    cv2.fillConvexPoly(cropped_tr1_mask, points, 255)

    # Triangularisation du second visage
    tr2_pt1 = landmarks_points2[triangle_index[0]]
    tr2_pt2 = landmarks_points2[triangle_index[1]]
    tr2_pt3 = landmarks_points2[triangle_index[2]]
    #cv2.line(img2, tr2_pt1, tr2_pt2, 255) # Afficher Triangles
    #cv2.line(img2, tr2_pt2, tr2_pt3, 255)
    #cv2.line(img2, tr2_pt1, tr2_pt3, 255)
    triangle2 = np.array([tr2_pt1, tr2_pt2, tr2_pt3], np.int32)


    rect2 = cv2.boundingRect(triangle2)
    (x, y, w, h) = rect2

    cropped_tr2_mask = np.zeros((h, w), np.uint8)

    points2 = np.array([[tr2_pt1[0] - x, tr2_pt1[1] - y],
                        [tr2_pt2[0] - x, tr2_pt2[1] - y],
                        [tr2_pt3[0] - x, tr2_pt3[1] - y]], np.int32)

    cv2.fillConvexPoly(cropped_tr2_mask, points2, 255)

    # Warp triangles
    points = np.float32(points)
    points2 = np.float32(points2)
    M = cv2.getAffineTransform(points, points2)
    warped_triangle = cv2.warpAffine(cropped_triangle, M, (w, h))
    warped_triangle = cv2.bitwise_and(warped_triangle, warped_triangle, mask=cropped_tr2_mask)

    # Reconstructing destination face
    img2_new_face_rect_area = img2_new_face[y: y + h, x: x + w]
    img2_new_face_rect_area_gray = cv2.cvtColor(img2_new_face_rect_area, cv2.COLOR_BGR2GRAY)
    _, mask_triangles_designed = cv2.threshold(img2_new_face_rect_area_gray, 1, 255, cv2.THRESH_BINARY_INV)
    warped_triangle = cv2.bitwise_and(warped_triangle, warped_triangle, mask=mask_triangles_designed)

    img2_new_face_rect_area = cv2.add(img2_new_face_rect_area, warped_triangle)
    img2_new_face[y: y + h, x: x + w] = img2_new_face_rect_area


# coller le visag sur 
img2_face_mask = np.zeros_like(img2_gray)
img2_head_mask = cv2.fillConvexPoly(img2_face_mask, convexhull2, 255)
img2_face_mask = cv2.bitwise_not(img2_head_mask)


img2_head_noface = cv2.bitwise_and(img2, img2, mask=img2_face_mask)
result = cv2.add(img2_head_noface, img2_new_face)

(x, y, w, h) = cv2.boundingRect(convexhull2)
center_face2 = (int((x + x + w) / 2), int((y + y + h) / 2))

#cv2.imshow("img", img)
#cv2.imshow("img2", img2)
#cv2.imshow("result", result)


normal_clone = cv2.seamlessClone(result, img2, img2_head_mask, center_face2, cv2.NORMAL_CLONE)
mixed_clone = cv2.seamlessClone(result, img2, img2_head_mask, center_face2, cv2.MIXED_CLONE)
mono = cv2.seamlessClone(result, img2, img2_head_mask, center_face2, cv2.MONOCHROME_TRANSFER)

#------------------------------------------------------------------------------------------------------
# PARTIE TESTS, ESSAIS POUR ENLEVER LES ARTEFACTS

def bresenham_line(pt1, pt2):
    x0, y0 = pt1[0], pt1[1]
    x1, y1 = pt2[0], pt2[1]

    steep = abs(y1 - y0) > abs(x1 - x0)
    if steep:
        x0, y0 = y0, x0  
        x1, y1 = y1, x1

    switched = False
    if x0 > x1:
        switched = True
        x0, x1 = x1, x0
        y0, y1 = y1, y0

    if y0 < y1: 
        ystep = 1
    else:
        ystep = -1

    deltax = x1 - x0
    deltay = abs(y1 - y0)
    error = -deltax / 2
    y = y0

    line = []    
    for x in range(x0, x1 + 1):
        if steep:
            line.append((y,x))
        else:
            line.append((x,y))

        error = error + deltay
        if error > 0:
            y = y + ystep
            error = error - deltax
    if switched:
        line.reverse()
    return line

def DISPARAISSEZ(image):

    for triangle_index in indexes_triangles:

        tr2_pt1 = landmarks_points2[triangle_index[0]]
        tr2_pt2 = landmarks_points2[triangle_index[1]]
        tr2_pt3 = landmarks_points2[triangle_index[2]]

        line_1_2 = bresenham_line(tr2_pt1, tr2_pt2)
        line_2_3 = bresenham_line(tr2_pt2, tr2_pt3) # Obtention des coordonnées des points des lignes pour leur appliquer un filtre
        line_3_1 = bresenham_line(tr2_pt3, tr2_pt1)

        lines = [line_1_2, line_2_3, line_3_1]

        for line in lines:
            for pixel in line:
                image[pixel[1], pixel[0]] = (1.0/9.0)*(image[pixel[1]-1, pixel[0]-1] + image[pixel[1]-1, pixel[0]] + image[pixel[1]-1, pixel[0]+1]
                                                    +  image[pixel[1], pixel[0]-1] + image[pixel[1]-1, pixel[0]] + image[pixel[1]-1, pixel[0]+1]
                                                    + image[pixel[1]+1, pixel[0]-1] + image[pixel[1]-1, pixel[0]] + image[pixel[1]-1, pixel[0]+1])
                #print([pixel[0], pixel[1]])

        #cv2.line(normal_clone, tr2_pt1, tr2_pt2, 255) # Afficher Triangles
        #cv2.line(normal_clone, tr2_pt2, tr2_pt3, 255)
        #cv2.line(normal_clone, tr2_pt1, tr2_pt3, 255)

        #cv2.line(mixed_clone, tr2_pt1, tr2_pt2, 255) # Afficher Triangles
        #cv2.line(mixed_clone, tr2_pt2, tr2_pt3, 255)
        #cv2.line(mixed_clone, tr2_pt1, tr2_pt3, 255)

        #cv2.line(mono, tr2_pt1, tr2_pt2, 255) # Afficher Triangles
        #cv2.line(mono, tr2_pt2, tr2_pt3, 255)
        #cv2.line(mono, tr2_pt1, tr2_pt3, 255)
    return



DISPARAISSEZ(normal_clone)
cv2.imshow("normal_clone", normal_clone)
cv2.imwrite("Normal_clone.jpg", normal_clone)

cv2.imshow("mixed_clone", mixed_clone)

cv2.imwrite("Mixed_clone.jpg", mixed_clone)

#cv2.imshow("monochrome_transfer", mono)
cv2.imwrite("Monochrome_transfer.jpg", mono)

cv2.waitKey(0)

cv2.destroyAllWindows()