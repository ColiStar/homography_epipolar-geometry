# Homography & Epipolar Geometry Estimation

This project explores geometric relationships between multi-view images by estimating homography and fundamental matrices using both **manual point correspondences** and an **automated feature extraction pipeline**.

The work is divided into two phases:

- 📌 **Planar Projection via Manual Correspondence**
- ⚙️ **Automated Geometry Estimation using HLOC**

Each phase is documented in its own subfolder with implementation code, experiments, and analysis results.

---

## 🧭 Project Structure

| Folder | Description |
|--------|-------------|
| [`planar-projection-manual/`](./planar-projection-manual/) | Milestone 1 – Homography & Fundamental matrix estimation using manually selected keypoints |
| [`geometry-pipeline-auto/`](./geometry-pipeline-auto/) | Milestone 2 – Automated feature extraction & epipolar geometry validation using SuperPoint, SuperGlue, DISK, and LightGlue |
| `data/` | (Optional) Shared CSV files or sample input |
| `requirements.txt` | Python environment requirements |

---

## 🔧 Setup Instructions

Make sure you have Python 3.8+ and pip installed.

```bash
pip install -r requirements.txt
