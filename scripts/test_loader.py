import os
import sys

# Add src to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dataset.kitti_loader import KITTIOdometryDataset
import yaml

def main():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    dataset_cfg = config.get('dataset', {})
    root_dir = dataset_cfg.get('root_dir', '..')
    sequence = dataset_cfg.get('sequence', '00')
    
    print(f"Loading dataset from: {root_dir}, sequence: {sequence}")
    
    try:
        dataset = KITTIOdometryDataset(root_dir=root_dir, sequence=sequence)
        print(f"Successfully loaded dataset with {len(dataset)} scans.")
        
        # Load the first scan
        points, intensity = dataset[0]
        print(f"First scan loaded. Points shape: {points.shape}, Intensity shape: {intensity.shape}")
        print(f"Sample points:\n{points[:3]}")
    except Exception as e:
        print(f"Error loading dataset: {e}")

if __name__ == "__main__":
    main()
