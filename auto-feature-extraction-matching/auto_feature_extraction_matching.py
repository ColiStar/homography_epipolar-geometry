# Clone and install HLOC
!git clone --recursive https://github.com/cvg/Hierarchical-Localization.git
%cd Hierarchical-Localization
!pip install -e . --quiet

import os
from pathlib import Path
import cv2
import h5py
import numpy as np
import matplotlib.pyplot as plt
import tqdm
import tqdm.notebook

from hloc import extract_features, match_features, pairs_from_exhaustive, reconstruction
from hloc.visualization import read_image, plot_images
%cd ..
tqdm.tqdm = tqdm.notebook.tqdm

# Set paths
images = Path("datasets/front-door/")
outputs = Path("outputs/milestone2/")
if outputs.exists():
    os.system(f"rm -rf {outputs}")
outputs.mkdir(parents=True, exist_ok=True)

# Define output files
sfm_pairs = outputs / "pairs-sfm.txt"
features = outputs / "features.h5"
matches = outputs / "matches.h5"
images_dir = "datasets/front-door/"

# Select feature extractor and matcher
feature_conf = extract_features.confs["disk"]
matcher_conf = match_features.confs["disk+lightglue"]

# Load image list
references = [p.relative_to(images).as_posix() for p in images.iterdir()]
print(f"Found {len(references)} images for mapping")
plot_images([read_image(images / r) for r in references], dpi=75)

# Run feature extraction and matching
extract_features.main(feature_conf, images, image_list=references, feature_path=features)
pairs_from_exhaustive.main(sfm_pairs, image_list=references)
match_features.main(matcher_conf, sfm_pairs, features=features, matches=matches)

# Reconstruct and verify geometry
reconstruction.main(
    image_dir=images,
    image_list=references,
    pairs=sfm_pairs,
    features=features,
    matches=matches,
    sfm_dir=outputs / "sfm",
    skip_geometric_verification=False
)

# Load matched features
feats = h5py.File(features, 'r')
matches = h5py.File(matches, 'r')

# Build image pairs
pairs = [(a, b) for a in matches.keys() for b in matches[a].keys() if a < b]
print("All pairs:", pairs)

for img1_name, img2_name in pairs:
    print(f"\n=== Processing {img1_name} <-> {img2_name} ===")

    # Load keypoints
    kp1 = feats[img1_name]["keypoints"][:]
    kp2 = feats[img2_name]["keypoints"][:]

    # Filter valid matches
    idx_arr = matches[img1_name][img2_name]["matches0"][:]
    valid = idx_arr >= 0
    pts1 = kp1[valid].astype(np.float32)
    pts2 = kp2[idx_arr[valid]].astype(np.float32)
    print(f"Number of valid matches: {len(pts1)}")

    # Estimate homography
    H, mask_H = cv2.findHomography(pts1, pts2, cv2.RANSAC, 3.0)
    print("Homography H:\n", H)

    in1 = pts1[mask_H.ravel() == 1]
    in2 = pts2[mask_H.ravel() == 1]
    proj = cv2.perspectiveTransform(in1.reshape(-1,1,2), H).reshape(-1,2)
    errs = np.linalg.norm(in2 - proj, axis=1)
    print(f"Reprojection error: mean={errs.mean():.2f}, max={errs.max():.2f}")

    # Show reprojection
    img2 = read_image(f"{images_dir}/{img2_name}")
    plt.figure(figsize=(6,6))
    plt.imshow(img2); plt.axis('off')
    plt.scatter(in2[:,0], in2[:,1], s=8, c='g', marker='o', label='true inliers')
    plt.scatter(proj[:,0], proj[:,1], s=8, c='r', marker='+', label='projected points')
    plt.title(f"Homography reprojection: {img1_name}→{img2_name}")
    plt.legend()
    plt.show()

    # Estimate fundamental matrix
    F, mask_F = cv2.findFundamentalMat(pts1, pts2, cv2.FM_RANSAC, 1.0, 0.99)
    print("Fundamental F:\n", F)

    in1_f = pts1[mask_F.ravel() == 1]
    in2_f = pts2[mask_F.ravel() == 1]

    # Compute epipolar lines
    lines1 = cv2.computeCorrespondEpilines(in2_f.reshape(-1,1,2), 2, F).reshape(-1,3)
    lines2 = cv2.computeCorrespondEpilines(in1_f.reshape(-1,1,2), 1, F).reshape(-1,3)

    # Draw epipolar lines
    def draw_epilines(img, lines, pts):
        out = img.copy()
        h, w = out.shape[:2]
        for (a, b, c), (x, y) in zip(lines, pts):
            x0, y0 = 0, int(-c/b)
            x1, y1 = w, int(-(c + a*w)/b)
            cv2.line(out, (x0, y0), (x1, y1), (0,255,0), 1)
            cv2.circle(out, (int(x), int(y)), 3, (0,0,255), -1)
        return out

    img1 = cv2.cvtColor(read_image(f"{images_dir}/{img1_name}"), cv2.COLOR_RGB2BGR)
    img2 = cv2.cvtColor(read_image(f"{images_dir}/{img2_name}"), cv2.COLOR_RGB2BGR)
    ep1 = draw_epilines(img1, lines1, in1_f)
    ep2 = draw_epilines(img2, lines2, in2_f)

    # Show epipolar lines
    plt.figure(figsize=(12,5))
    plt.subplot(1,2,1)
    plt.imshow(cv2.cvtColor(ep1, cv2.COLOR_BGR2RGB))
    plt.title("Epipolar lines on image 1")
    plt.axis('off')
    plt.subplot(1,2,2)
    plt.imshow(cv2.cvtColor(ep2, cv2.COLOR_BGR2RGB))
    plt.title("Epipolar lines on image 2")
    plt.axis('off')
    plt.show()
