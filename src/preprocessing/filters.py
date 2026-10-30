import numpy as np

def crop_by_range(points, intensity=None, labels=None, min_range=0.0, max_range=100.0):
    """
    Filter points that fall outside the specified range [min_range, max_range] in the XY plane.
    
    Args:
        points (np.ndarray): (N, 3) point coordinates.
        intensity (np.ndarray, optional): (N, 1) intensity values.
        labels (np.ndarray, optional): (N,) semantic labels.
        min_range (float): Minimum radial distance in XY.
        max_range (float): Maximum radial distance in XY.
        
    Returns:
        Filtered points, intensity (if provided), labels (if provided)
    """
    if len(points) == 0:
        return points, intensity, labels
        
    # Calculate distance in XY plane
    r = np.linalg.norm(points[:, :2], axis=1)
    
    mask = (r >= min_range) & (r <= max_range)
    
    filtered_points = points[mask]
    
    filtered_intensity = intensity[mask] if intensity is not None else None
    filtered_labels = labels[mask] if labels is not None else None
    
    return filtered_points, filtered_intensity, filtered_labels

def remove_ground_heuristic(points, height_threshold=-1.5):
    """
    A simple heuristic to remove points below a certain Z threshold,
    assuming the sensor is mounted at a specific height.
    This is just a fallback if semantic segmentation is not used.
    
    Args:
        points (np.ndarray): (N, 3) point coordinates.
        height_threshold (float): Z coordinate threshold.
    """
    mask = points[:, 2] > height_threshold
    return points[mask]

def voxel_downsample(points, voxel_size=0.05):
    """
    Simple voxel grid downsampling using Open3D.
    Note: Loses exact intensity/labels unless carefully interpolated.
    Primarily useful for quick visualization or geometric baseline.
    """
    import open3d as o3d
    
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    
    downpcd = pcd.voxel_down_sample(voxel_size=voxel_size)
    return np.asarray(downpcd.points)
