import open3d as o3d
import numpy as np

def visualize_point_cloud(points, intensity=None, window_name="LiDAR Viewer"):
    """
    Visualizes a point cloud using Open3D.
    
    Args:
        points (np.ndarray): (N, 3) XYZ points.
        intensity (np.ndarray, optional): (N, 1) intensity values.
        window_name (str): Title of the visualization window.
    """
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    
    if intensity is not None:
        # Normalize intensity to [0, 1] for coloring (grayscale)
        intensity_norm = (intensity - np.min(intensity)) / (np.max(intensity) - np.min(intensity) + 1e-6)
        # Replicate to (N, 3) for RGB colors
        colors = np.repeat(intensity_norm, 3, axis=1)
        pcd.colors = o3d.utility.Vector3dVector(colors)
    else:
        # Default flat color
        pcd.paint_uniform_color([0.5, 0.5, 0.5])
        
    print("Opening Open3D visualization window. Close the window to continue...")
    o3d.visualization.draw_geometries([pcd], window_name=window_name)
