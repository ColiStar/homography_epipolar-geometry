import cv2
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def select_points(img, window_name, num_points):
    """
    Allow user to manually select a fixed number of points on the image using mouse clicks.

    Args:
        img (np.ndarray): Image on which to select points.
        window_name (str): Title of the OpenCV window.
        num_points (int): Number of points to select.

    Returns:
        np.ndarray: Array of selected (x, y) coordinates.
    """
    pts = []

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(pts) < num_points:
            pts.append((x, y))
            cv2.circle(img_display, (x, y), 4, (0, 255, 0), -1)
            cv2.imshow(window_name, img_display)

    img_display = img.copy()
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 800, 600)
    cv2.imshow(window_name, img_display)
    cv2.setMouseCallback(window_name, on_mouse)

    while len(pts) < num_points:
        cv2.waitKey(1)

    cv2.destroyWindow(window_name)
    return np.array(pts, dtype=float)


def select_triplets(imgA, imgB, imgC, num_points):
    """
    Collect manually selected point correspondences across three images.

    Returns:
        Tuple of np.ndarrays: (ptsA, ptsB, ptsC)
    """
    ptsA = select_points(imgA.copy(), "Select points on Image A", num_points)
    ptsB = select_points(imgB.copy(), "Select matching points on Image B", num_points)
    ptsC = select_points(imgC.copy(), "Select matching points on Image C", num_points)
    return ptsA, ptsB, ptsC


def overlay_points_matplotlib(img, pts, title, color='y'):
    """Visualize selected points on image using Matplotlib."""
    plt.figure(figsize=(8, 6))
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.scatter(pts[:, 0], pts[:, 1], c=color, s=100)
    plt.title(title)
    plt.axis('off')
    plt.show()


# Load input images
imgA = cv2.imread("data/imga.jpg")
imgB = cv2.imread("data/imgb.jpg")
imgC = cv2.imread("data/imgc.jpg")

# Select correspondences
N = 10
ptsA, ptsB, ptsC = select_triplets(imgA, imgB, imgC, N)

# Save to CSV
df = pd.DataFrame({
    'ImageA_x': ptsA[:, 0], 'ImageA_y': ptsA[:, 1],
    'ImageB_x': ptsB[:, 0], 'ImageB_y': ptsB[:, 1],
    'ImageC_x': ptsC[:, 0], 'ImageC_y': ptsC[:, 1],
})
df.to_csv('manual_correspondences.csv', index=False)
print(df)

# Visualize correspondences
overlay_points_matplotlib(imgA, ptsA, "Selected Points on Image A", color='g')
overlay_points_matplotlib(imgB, ptsB, "Selected Points on Image B", color='g')
overlay_points_matplotlib(imgC, ptsC, "Selected Points on Image C", color='g')

# Compute homographies
H_AB, _ = cv2.findHomography(ptsA, ptsB, cv2.RANSAC, 3.0)
H_AC, _ = cv2.findHomography(ptsA, ptsC, cv2.RANSAC, 3.0)
print("H_AB:\n", H_AB)
print("H_AC:\n", H_AC)

# Project new point
newA = select_points(imgA.copy(), "Select new test point on Image A", 1)
overlay_points_matplotlib(imgA, newA, "New Test Point on Image A", color='r')
mappedB = cv2.perspectiveTransform(newA.reshape(-1, 1, 2), H_AB).reshape(-1, 2)
mappedC = cv2.perspectiveTransform(newA.reshape(-1, 1, 2), H_AC).reshape(-1, 2)
overlay_points_matplotlib(imgB, mappedB, "Projected Point on Image B", color='y')
overlay_points_matplotlib(imgC, mappedC, "Projected Point on Image C", color='y')

# Estimate fundamental matrix
F_AB, _ = cv2.findFundamentalMat(ptsA, ptsB, cv2.FM_RANSAC, 3.0, 0.99)
print("F_AB:\n", F_AB)

# Epipolar validation
lineB = cv2.computeCorrespondEpilines(newA.reshape(1, 1, 2), 1, F_AB).reshape(3)
x_vals = np.array([0, imgB.shape[1]])
y_vals = -(lineB[0] * x_vals + lineB[2]) / lineB[1]

plt.figure(figsize=(8, 6))
plt.imshow(cv2.cvtColor(imgB, cv2.COLOR_BGR2RGB))
plt.plot(x_vals, y_vals, '-g', label='Epipolar line')
trueB = select_points(imgB.copy(), "Select true corresponding point on Image B", 1)
plt.scatter(trueB[:, 0], trueB[:, 1], c='r', s=100, label='True match')
plt.title("Epipolar Line Validation")
plt.legend(); plt.axis('off'); plt.show()

# Cross-view consistency check
F_CB, _ = cv2.findFundamentalMat(ptsC, ptsB, cv2.FM_RANSAC, 3.0, 0.99)
newB_true = select_points(imgB.copy(), "Select true corresponding point on Image B (from C-mapped)", 1)
lineA_inB = cv2.computeCorrespondEpilines(newA.reshape(1, 1, 2), 1, F_AB).reshape(3)
lineC_inB = cv2.computeCorrespondEpilines(mappedC.reshape(1, 1, 2), 1, F_CB).reshape(3)

a1, b1, c1 = lineA_inB
a2, b2, c2 = lineC_inB
pt_intersect = np.linalg.solve(np.array([[a1, b1], [a2, b2]]), -np.array([c1, c2]))
error = np.linalg.norm(pt_intersect - newB_true[0])
print(f"Intersection: {pt_intersect}, Ground truth: {newB_true[0]}, Error: {error:.2f}px")

plt.figure(figsize=(8, 6))
plt.imshow(cv2.cvtColor(imgB, cv2.COLOR_BGR2RGB))
for a, b, c in (lineA_inB, lineC_inB):
    x0, y0 = 0, -c / b
    x1, y1 = imgB.shape[1], -(a * imgB.shape[1] + c) / b
    plt.plot([x0, x1], [y0, y1], '-g')

plt.scatter(*pt_intersect, c='y', s=80, label='Intersection')
plt.scatter(*newB_true[0], c='r', s=80, label='Ground Truth')
plt.legend(); plt.axis('off'); plt.show()
