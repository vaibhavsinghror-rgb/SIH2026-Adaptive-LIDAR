# Adaptive Variable Resolution 2.5D Lidar Mapping for Dynamic Environment Perception

This project provides an adaptive variable-resolution (foveated) 2.5D mapping system designed for **Smart India Hackathon 2026 (SIH26053)**. 

## Project Objective
Transform raw 3D LiDAR point clouds into an efficient 2.5D spatial grid. The system maintains high spatial detail near the vehicle, but progressively reduces detail farther away, mimicking human foveated vision. This significantly reduces memory and computational requirements while preserving critical elevation and semantic information.

## Story & Concept
- **Problem**: 3D LiDAR is expensive to process, and simple 2D maps lose critical elevation data.
- **Our Solution**: Foveated 2.5D representation.
- **Near Field**: 5 cm resolution cells for precise local navigation.
- **Far Field**: Progressively coarser cells (20 cm -> 50 cm) to save memory where precision is less critical.
- **Semantics**: Each cell retains knowledge of the terrain (drivable/non-drivable) and objects (obstacles).
- **Result**: Over 40% memory reduction with measurable performance gains!

---

## Environment Setup

Requires Python 3.10 and `uv`.

```bash
# Set up virtual environment and install dependencies
uv venv --python 3.10
.venv\Scripts\activate
uv pip install torch torchvision open3d numpy scipy pyyaml
```

## Dataset
This prototype runs on the KITTI Odometry dataset (Velodyne `.bin` point clouds).
Place the sequence folders (`00`, `01`, etc.) in the `sequences/` directory.

> **Note on Semantic Labels:** Since the provided raw KITTI dataset lacks ground-truth `.label` files, semantic classes are inferred on-the-fly using a geometric heuristic segmenter (`project/src/segmentation/heuristic_segmentation.py`). For a production environment with weights, simply swap the segmenter for a PointNet++ or sparse convolution model.

## Running the SIH Demonstration

The one-click demo loads a sequence, runs semantic processing, computes the foveated grid and baseline, displays live metrics, and launches an interactive 3D dashboard.

```bash
# Run on a single frame (default)
python project/scripts/run_demo.py

# Play the entire dataset sequence as a continuous animated visualization!
python project/scripts/run_demo.py --play --fps 15
```

### Dashboard Guide
- **LEFT**: Raw 3D Semantic Point Cloud.
- **RIGHT**: Foveated 2.5D Grid. The grid is color-coded by semantic class, and the varying cell resolution clearly demonstrates the foveated concept.

## Live Metrics Example
When running the system, you will see performance metrics like this:
```
==================================================
 LIVE METRICS & COMPARISON
==================================================
Input Points:           124668
Represented Cells:      37909

Grid Memory (Foveated): 444.25 KB
Grid Memory (Baseline): 783.73 KB
Memory Reduction:       43.32 %

Segmentation Time:      0.50 ms
Projection Time (Fov):  92.54 ms
Projection Time (Base): 146.52 ms
FPS (Foveated total):   10.75
```

## Architecture
- `config/config.yaml`: Defines resolution zones (near, mid, far).
- `src/dataset/kitti_loader.py`: Raw point cloud loader.
- `src/segmentation/heuristic_segmentation.py`: Simulated semantic engine.
- `src/mapping/grid_engine.py`: Fast vectorized foveated projection algorithm.
- `src/mapping/baseline.py`: Uniform high-resolution engine for fair benchmarking.
- `src/visualization/dashboard.py`: Open3D interactive views.

## Final SIH Acceptance
- [x] Real LiDAR dataset used.
- [x] Semantic classes interpreted.
- [x] Foveated grid works seamlessly without gaps or overlaps.
- [x] Baseline exists and Proposed system is benchmarked against it.
- [x] Memory usage, latency, and FPS are measured.
- [x] No fabricated metrics.

Built for **SIH 2026**.
