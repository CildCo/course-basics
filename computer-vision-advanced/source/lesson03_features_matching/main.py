import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import Image, display


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


output = Path("output")
output.mkdir(exist_ok=True)
print("输出目录已就绪")

import cv2
from PIL import Image as PILImage

pattern = np.array(PILImage.open(data_path("images/pattern.png")).convert("L"))
rotated = np.array(PILImage.open(data_path("images/pattern_rotated.png")).convert("L"))
print("原图形状：", pattern.shape)
print("变换后形状：", rotated.shape)
print("原图灰度范围：", int(pattern.min()), "到", int(pattern.max()))


orb = cv2.ORB_create(nfeatures=500)
keypoints_a, descriptors_a = orb.detectAndCompute(pattern, None)
keypoints_b, descriptors_b = orb.detectAndCompute(rotated, None)

print("原图关键点：", len(keypoints_a))
print("变换图关键点：", len(keypoints_b))
print("原图描述子形状：", descriptors_a.shape)
print("变换图描述子形状：", descriptors_b.shape)
print("单个描述子字节数：", descriptors_a.shape[1])

vis_a = cv2.drawKeypoints(pattern, keypoints_a, None, color=(220, 70, 60), flags=cv2.DRAW_MATCHES_FLAGS_DEFAULT)
vis_b = cv2.drawKeypoints(rotated, keypoints_b, None, color=(220, 70, 60), flags=cv2.DRAW_MATCHES_FLAGS_DEFAULT)
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].imshow(vis_a)
axes[0].set_title(f"原图：{len(keypoints_a)} 个关键点")
axes[1].imshow(vis_b)
axes[1].set_title(f"变换图：{len(keypoints_b)} 个关键点")
for ax in axes:
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "keypoints.png", dpi=110)
display(Image(filename=str(output / "keypoints.png")))
plt.close(fig)


matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
raw_matches = matcher.knnMatch(descriptors_a, descriptors_b, k=2)
good_matches = [first for first, second in raw_matches if first.distance < 0.75 * second.distance]

print("候选匹配：", len(raw_matches))
print("比值检验后：", len(good_matches))
print("保留比例：", f"{len(good_matches) / len(raw_matches):.1%}")

match_vis = cv2.drawMatches(
    pattern, keypoints_a,
    rotated, keypoints_b,
    good_matches[:40], None,
    flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
)
plt.figure(figsize=(12, 4.5))
plt.imshow(match_vis)
plt.title("比值检验后的前 40 对匹配")
plt.axis("off")
plt.tight_layout()
plt.savefig(output / "matches.png", dpi=110)
display(Image(filename=str(output / "matches.png")))
plt.close()


source_points = np.float32([keypoints_a[match.queryIdx].pt for match in good_matches]).reshape(-1, 1, 2)
target_points = np.float32([keypoints_b[match.trainIdx].pt for match in good_matches]).reshape(-1, 1, 2)
homography, inlier_mask = cv2.findHomography(source_points, target_points, cv2.RANSAC, 4.0)
inliers = int(inlier_mask.sum())

print("估计出的单应矩阵：")
print(np.round(homography, 3))
print("内点数量：", inliers)
print("内点比例：", f"{inliers / len(good_matches):.1%}")

height, width = pattern.shape
corners = np.float32([[0, 0], [width, 0], [width, height], [0, height]]).reshape(-1, 1, 2)
projected = cv2.perspectiveTransform(corners, homography).reshape(-1, 2)
print("原图四角变换后：")
print(np.round(projected, 1))

inlier_vis = cv2.drawMatches(
    pattern, keypoints_a,
    rotated, keypoints_b,
    good_matches, None,
    matchColor=(80, 170, 100),
    singlePointColor=(180, 180, 180),
    matchesMask=inlier_mask.ravel().astype(int).tolist(),
    flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
)
plt.figure(figsize=(12, 4.5))
plt.imshow(inlier_vis)
plt.title(f"RANSAC 内点：{inliers} 对")
plt.axis("off")
plt.tight_layout()
plt.savefig(output / "inliers.png", dpi=110)
display(Image(filename=str(output / "inliers.png")))
plt.close()
