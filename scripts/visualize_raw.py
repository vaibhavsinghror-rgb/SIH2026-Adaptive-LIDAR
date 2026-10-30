import os
import sys
import yaml
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dataset.kitti_loader import KITTIOdometryDataset
from visualization.visualizer import visualize_point_cloud

def main():
    parser = argparse.ArgumentParser(description="Visualize raw LiDAR point cloud.")
    parser.add_argument("--frame", type=int, default=0, help="Frame index to visualize")
    args = parser.parse_args()

    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    dataset_cfg = config.get('dataset', {})
    root_dir = dataset_cfg.get('root_dir', 'd:/downloads/dataset/sequences')
    sequence = dataset_cfg.get('sequence', '00')
    
    try:
        dataset = KITTIOdometryDataset(root_dir=root_dir, sequence=sequence)
        points, intensity = dataset[args.frame]
        
        print(f"Visualizing frame {args.frame} | Points: {len(points)}")
        visualize_point_cloud(points, intensity, window_name=f"Raw LiDAR - Seq {sequence} Frame {args.frame}")
        
    except Exception as e:
        print(f"Error during visualization: {e}")

if __name__ == "__main__":
    main()
