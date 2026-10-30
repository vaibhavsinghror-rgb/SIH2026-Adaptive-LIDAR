import os
import sys
import yaml
import time
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dataset.kitti_loader import KITTIOdometryDataset
from segmentation.heuristic_segmentation import HeuristicSegmenter
from mapping.grid_engine import FoveatedGridEngine
from mapping.baseline import UniformGridEngine

def main():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    dataset_cfg = config.get('dataset', {})
    dataset = KITTIOdometryDataset(root_dir=dataset_cfg['root_dir'], sequence=dataset_cfg['sequence'])
    
    points, intensity = dataset[0]
    print(f"Loaded {len(points)} raw points.")
    
    # Segment
    segmenter = HeuristicSegmenter()
    
    t0 = time.time()
    labels = segmenter.infer(points)
    t_seg = time.time() - t0
    print(f"Segmentation took {t_seg*1000:.2f} ms")
    
    # Foveated Engine
    foveated = FoveatedGridEngine(config['foveated_grid'])
    t0 = time.time()
    fov_map = foveated.build_map(points, labels, intensity)
    t_fov = time.time() - t0
    
    # Baseline Engine
    baseline = UniformGridEngine(config['foveated_grid'])
    t0 = time.time()
    base_map = baseline.build_map(points, labels, intensity)
    t_base = time.time() - t0
    
    print("-" * 40)
    print("METRICS COMPARISON:")
    print(f"Input Points: {len(points)}")
    print(f"Foveated Cells: {len(fov_map)}")
    print(f"Baseline Cells: {len(base_map)}")
    print(f"Cell Reduction: {(1.0 - len(fov_map)/len(base_map))*100:.2f}%")
    print(f"Foveated Latency: {t_fov*1000:.2f} ms")
    print(f"Baseline Latency: {t_base*1000:.2f} ms")
    
    # Extract resolution stats
    res_counts = {}
    for cell in fov_map.values():
        r = cell['res']
        res_counts[r] = res_counts.get(r, 0) + 1
        
    print("Foveated Zone Breakdown:")
    for r, count in sorted(res_counts.items()):
        print(f"  Res {r:.2f}m: {count} cells")

if __name__ == "__main__":
    main()
