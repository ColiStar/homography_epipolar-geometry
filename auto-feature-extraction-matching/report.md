# ECE 281 – Project 1 Milestone 2  
**Title:** Multi-View Geometry with Automatic Keypoint Matching  
**Authors:** Pin-Hsuan Chen  

---

## Overview

This report presents the implementation and evaluation of an automatic pipeline for estimating homography and fundamental matrices between images. It replaces manual correspondence selection (Milestone 1) with automated keypoint detection and matching using HLOC, including SuperPoint+SuperGlue and DISK+LightGlue.

---

## Pipeline Overview

- Input images: Image A, B, and C (same as Milestone 1)
- Detector/Matcher:
  - Option 1: SuperPoint + SuperGlue
  - Option 2: DISK + LightGlue
- Steps:
  1. Automatic feature extraction and matching
  2. RANSAC-based estimation of Homography (H) and Fundamental Matrix (F)
  3. Visualization of point correspondences
  4. Validation via cross-view consistency and epipolar geometry

