import os
import sys
import yaml
import time
import argparse
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dataset.kitti_loader import KITTIOdometryDataset
from segmentation.heuristic_segmentation import HeuristicSegmenter, apply_semantic_colors
from mapping.grid_engine import FoveatedGridEngine
from mapping.baseline import UniformGridEngine
from visualization.dashboard import LiveDashboard

def print_header(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def main():
    parser = argparse.ArgumentParser(description="SIH 2026: Foveated 2.5D Mapping")
    parser.add_argument("--frame", type=int, default=None, help="Process a specific single frame")
    parser.add_argument("--play", action="store_true", help="Play the dataset as a continuous video sequence")
    parser.add_argument("--max-frames", type=int, default=None, help="Maximum number of frames to process in playback mode")
    parser.add_argument("--fps", type=float, default=10.0, help="Target FPS for playback")
    parser.add_argument("--no-vis", action="store_true", help="Run without opening the 3D visualization window")
    args = parser.parse_args()

    print_header("SIH 2026: ADAPTIVE VARIABLE RESOLUTION 2.5D MAPPING")
    
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    dataset_cfg = config.get('dataset', {})
    dataset = KITTIOdometryDataset(root_dir=dataset_cfg['root_dir'], sequence=dataset_cfg['sequence'])
    total_frames = len(dataset)
    print(f"Dataset loaded. Sequence {dataset_cfg['sequence']} contains {total_frames} frames.")

    segmenter = HeuristicSegmenter()
    fov_engine = FoveatedGridEngine(config['foveated_grid'])
    base_engine = UniformGridEngine(config['foveated_grid'])

    dashboard = None
    show_vis = config.get('visualization', {}).get('show_grid', True) and not args.no_vis
    if show_vis:
        try:
            dashboard = LiveDashboard()
        except Exception as e:
            print(f"Warning: Could not initialize 3D display ({e}). Continuing in headless mode.")
            dashboard = None

    start_frame = args.frame if args.frame is not None else 0
    if args.play:
        if args.max_frames is not None:
            end_frame = min(start_frame + args.max_frames, total_frames)
        else:
            end_frame = total_frames
    else:
        end_frame = start_frame + 1

    target_frame_time = 1.0 / args.fps
    bytes_per_cell = 12 # simulated struct size (12 bytes)
    
    total_pts = 0
    total_fov_cells = 0
    total_base_cells = 0
    total_fov_time = 0.0
    total_base_time = 0.0
    frames_processed = 0

    try:
        for frame_idx in range(start_frame, end_frame):
            frame_t0 = time.time()
            points, intensity = dataset[frame_idx]
            
            # 1. Semantic Segmentation
            t0 = time.time()
            labels = segmenter.infer(points)
            t_seg = time.time() - t0
            raw_colors = apply_semantic_colors(labels)
            
            # 2. Foveated Mapping
            t0 = time.time()
            fov_map = fov_engine.build_map(points, labels, intensity)
            t_fov = time.time() - t0
            
            # 3. Baseline Comparison
            t0 = time.time()
            base_map = base_engine.build_map(points, labels, intensity)
            t_base = time.time() - t0

            # Compute Metrics
            fov_mem_kb = (len(fov_map) * bytes_per_cell) / 1024.0
            base_mem_kb = (len(base_map) * bytes_per_cell) / 1024.0
            mem_reduction = (1.0 - fov_mem_kb / base_mem_kb) * 100 if base_mem_kb > 0 else 0
            
            total_pts += len(points)
            total_fov_cells += len(fov_map)
            total_base_cells += len(base_map)
            total_fov_time += (t_seg + t_fov)
            total_base_time += (t_seg + t_base)
            frames_processed += 1

            sys.stdout.write(f"\r[Frame {frame_idx:04d}] Pts: {len(points)} | Fov Cells: {len(fov_map)} (-{mem_reduction:.1f}% Mem) | Latency: {(t_seg+t_fov)*1000:.1f}ms")
            sys.stdout.flush()

            # Update Dashboard
            if dashboard is not None:
                fov_points, fov_labels, _ = fov_engine.map_to_point_cloud(fov_map)
                fov_colors = apply_semantic_colors(fov_labels)
                alive = dashboard.update(points, raw_colors, fov_points, fov_colors)
                if not alive:
                    print("\nVisualization window closed by user.")
                    break

            # Throttle playback speed
            elapsed = time.time() - frame_t0
            if args.play and elapsed < target_frame_time:
                time.sleep(target_frame_time - elapsed)

    except KeyboardInterrupt:
        print("\nPlayback interrupted by user.")
    
    print("\n")
    print_header("EXECUTION SUMMARY")
    if frames_processed > 0:
        avg_pts = total_pts / frames_processed
        avg_fov_cells = total_fov_cells / frames_processed
        avg_base_cells = total_base_cells / frames_processed
        avg_fov_ms = (total_fov_time / frames_processed) * 1000.0
        avg_base_ms = (total_base_time / frames_processed) * 1000.0
        overall_reduction = (1.0 - total_fov_cells / total_base_cells) * 100 if total_base_cells > 0 else 0
        
        print(f"Frames Processed:        {frames_processed}")
        print(f"Avg Points / Frame:      {avg_pts:,.0f}")
        print(f"Avg Foveated Cells:      {avg_fov_cells:,.0f} ({avg_fov_cells * bytes_per_cell / 1024:.2f} KB)")
        print(f"Avg Baseline Cells:      {avg_base_cells:,.0f} ({avg_base_cells * bytes_per_cell / 1024:.2f} KB)")
        print(f"Memory/Cell Reduction:   {overall_reduction:.2f}%")
        print(f"Avg Processing Latency:  {avg_fov_ms:.2f} ms (~{1000.0/avg_fov_ms:.1f} FPS)")
        print(f"Baseline Latency:        {avg_base_ms:.2f} ms (~{1000.0/avg_base_ms:.1f} FPS)")
    
    if dashboard is not None and not args.play:
        print("\nVisualization is open. Close the window to exit.")
        while dashboard.update(points, raw_colors, fov_points, fov_colors):
            time.sleep(0.05)
        dashboard.close()
    elif dashboard is not None:
        dashboard.close()

if __name__ == "__main__":
    main()
