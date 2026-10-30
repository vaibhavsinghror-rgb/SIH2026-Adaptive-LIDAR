import os
import glob
import numpy as np

class KITTIOdometryDataset:
    def __init__(self, root_dir, sequence="00"):
        """
        Args:
            root_dir (str): Path to the sequences directory containing '00', '01', etc.
            sequence (str): Sequence number as a string, e.g., '00'.
        """
        self.root_dir = root_dir
        self.sequence = sequence
        if not os.path.isdir(os.path.join(self.root_dir, self.sequence, 'velodyne')): fallback = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')); self.root_dir = fallback if os.path.isdir(os.path.join(fallback, self.sequence, 'velodyne')) else self.root_dir
        self.velodyne_dir = os.path.join(self.root_dir, self.sequence, 'velodyne')
        
        if not os.path.isdir(self.velodyne_dir):
            raise ValueError(f"Directory not found: {self.velodyne_dir}")
            
        self.scan_files = sorted(glob.glob(os.path.join(self.velodyne_dir, "*.bin")))
        if len(self.scan_files) == 0:
            raise ValueError(f"No .bin files found in {self.velodyne_dir}")
            
    def __len__(self):
        return len(self.scan_files)
        
    def __getitem__(self, idx):
        """
        Args:
            idx (int): Index of the scan.
        Returns:
            points (np.ndarray): (N, 3) XYZ coordinates of points.
            intensity (np.ndarray): (N, 1) Intensities of points.
        """
        scan_path = self.scan_files[idx]
        # KITTI velodyne files are float32 Nx4 arrays: [x, y, z, intensity]
        scan = np.fromfile(scan_path, dtype=np.float32).reshape(-1, 4)
        
        points = scan[:, :3]
        intensity = scan[:, 3:4]
        
        return points, intensity
