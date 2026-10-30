import open3d as o3d
import numpy as np

class LiveDashboard:
    def __init__(self, window_name="SIH 2026: Foveated LiDAR Mapping Demo"):
        self.vis = o3d.visualization.Visualizer()
        self.vis.create_window(window_name=window_name, width=1600, height=900)
        self.raw_pcd = o3d.geometry.PointCloud()
        self.fov_pcd = o3d.geometry.PointCloud()
        self.is_initialized = False

    def update(self, raw_points, raw_colors, fov_points, fov_colors, offset_x=120.0):
        # Update raw point cloud
        self.raw_pcd.points = o3d.utility.Vector3dVector(raw_points)
        self.raw_pcd.colors = o3d.utility.Vector3dVector(raw_colors)

        # Update foveated map (offset to the right)
        fov_points_shifted = fov_points.copy()
        fov_points_shifted[:, 0] += offset_x
        self.fov_pcd.points = o3d.utility.Vector3dVector(fov_points_shifted)
        self.fov_pcd.colors = o3d.utility.Vector3dVector(fov_colors)

        if not self.is_initialized:
            self.vis.add_geometry(self.raw_pcd)
            self.vis.add_geometry(self.fov_pcd)
            
            # Setup camera for better top-down/isometric view
            ctr = self.vis.get_view_control()
            ctr.set_lookat([offset_x/2.0, 0, 0])
            ctr.set_up([0, 0, 1])
            ctr.set_front([0.5, -0.5, 0.7])
            ctr.set_zoom(0.15)
            self.is_initialized = True
        else:
            self.vis.update_geometry(self.raw_pcd)
            self.vis.update_geometry(self.fov_pcd)

        # Process UI events
        alive = self.vis.poll_events()
        self.vis.update_renderer()
        return alive

    def close(self):
        self.vis.destroy_window()
