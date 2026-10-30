import numpy as np

class FoveatedGridEngine:
    """
    Core engine for variable-resolution 2.5D mapping.
    Points are assigned to concentric zones based on their radial distance.
    Within each zone, points are aggregated into a uniform 2D grid.
    """
    def __init__(self, config):
        """
        Args:
            config (dict): Grid configuration from config.yaml.
        """
        self.max_range = config.get('maximum_range', 100.0)
        
        # Define zones as a list of dictionaries
        self.zones = [
            {'max_r': config.get('near_radius', 10.0), 'res': config.get('near_resolution', 0.05)},
            {'max_r': config.get('mid_radius', 30.0), 'res': config.get('mid_resolution', 0.20)},
            {'max_r': self.max_range, 'res': config.get('far_resolution', 0.50)}
        ]

    def build_map(self, points, labels, intensities=None):
        """
        Converts 3D points into a foveated 2.5D representation.
        
        Args:
            points (np.ndarray): (N, 3) XYZ coordinates.
            labels (np.ndarray): (N,) semantic labels.
            intensities (np.ndarray, optional): (N, 1) intensities.
            
        Returns:
            dict: Mapping of (zone_idx, gx, gy) -> {
                'height': max_z, 
                'label': dominant_class, 
                'density': point_count,
                'center_x': cx,
                'center_y': cy,
                'res': cell_resolution
            }
        """
        N = points.shape[0]
        if N == 0:
            return {}

        # 1. Compute radial distances
        r = np.linalg.norm(points[:, :2], axis=1)
        
        # 2. Filter by max range
        valid_mask = r <= self.max_range
        points = points[valid_mask]
        labels = labels[valid_mask]
        r = r[valid_mask]
        
        # 3. Assign zones
        zone_indices = np.zeros(len(points), dtype=np.int32)
        current_min = 0.0
        
        # Assign points to zones
        for i, zone in enumerate(self.zones):
            zone_mask = (r > current_min) & (r <= zone['max_r'])
            zone_indices[zone_mask] = i
            current_min = zone['max_r']
            
        # 4. Compute grid indices per point
        # Extract resolutions array corresponding to each point's zone
        res_array = np.array([z['res'] for z in self.zones])
        point_res = res_array[zone_indices]
        
        # Compute gx, gy
        gx = np.floor(points[:, 0] / point_res).astype(np.int32)
        gy = np.floor(points[:, 1] / point_res).astype(np.int32)
        
        # 5. Group by (zone, gx, gy)
        # We can use np.unique on a structured array or string array to find unique cells.
        # Alternatively, using a dictionary for simple grouping:
        # (This is a naive grouping, can be optimized with pandas or np.lexsort for very large point clouds)
        
        # For optimization, we use a vectorized approach with np.unique
        # Create a single unique integer ID for each cell to group efficiently.
        # Since gx, gy can be negative and large, we hash them or pack them.
        # Packing into a single int64:
        # zone (8 bits) | gx (28 bits) | gy (28 bits)
        # Shift amounts:
        SHIFT_GX = 28
        SHIFT_ZONE = 56
        MASK_28 = (1 << 28) - 1
        
        # Offset to handle negative coordinates (assuming values fit in 28 bits)
        OFFSET = 1 << 27
        gx_offset = gx + OFFSET
        gy_offset = gy + OFFSET
        
        packed_ids = (zone_indices.astype(np.int64) << SHIFT_ZONE) | \
                     ((gx_offset.astype(np.int64) & MASK_28) << SHIFT_GX) | \
                     (gy_offset.astype(np.int64) & MASK_28)
                     
        unique_ids, inverse_indices = np.unique(packed_ids, return_inverse=True)
        
        # Aggregate properties
        num_cells = len(unique_ids)
        
        cell_heights = np.full(num_cells, -np.inf)
        cell_density = np.zeros(num_cells, dtype=np.int32)
        
        # For dominant label, we could do a bincount per cell, but for speed 
        # we can just take the max label (if higher labels are obstacles, which is safer)
        # or properly aggregate. Let's do max label for safety (obstacle > road > unlabeled).
        cell_labels = np.zeros(num_cells, dtype=np.int32)
        
        # Vectorized max height and max label (fast fallback for dominant)
        np.maximum.at(cell_heights, inverse_indices, points[:, 2])
        np.add.at(cell_density, inverse_indices, 1)
        np.maximum.at(cell_labels, inverse_indices, labels)
        
        # Unpack IDs to reconstruct dictionary or structured format
        out_zones = (unique_ids >> SHIFT_ZONE).astype(np.int32)
        out_gx = ((unique_ids >> SHIFT_GX) & MASK_28).astype(np.int32) - OFFSET
        out_gy = (unique_ids & MASK_28).astype(np.int32) - OFFSET
        
        # Build map
        foveated_map = {}
        for i in range(num_cells):
            z_idx = out_zones[i]
            res = self.zones[z_idx]['res']
            key = (z_idx, out_gx[i], out_gy[i])
            foveated_map[key] = {
                'height': cell_heights[i],
                'label': cell_labels[i],
                'density': cell_density[i],
                'center_x': (out_gx[i] + 0.5) * res,
                'center_y': (out_gy[i] + 0.5) * res,
                'res': res
            }
            
        return foveated_map

    def map_to_point_cloud(self, foveated_map):
        """
        Converts the 2.5D map back into a 3D point cloud for visualization (center of cells).
        
        Returns:
            points (np.ndarray): (M, 3)
            labels (np.ndarray): (M,)
            resolutions (np.ndarray): (M,)
        """
        M = len(foveated_map)
        points = np.zeros((M, 3))
        labels = np.zeros(M, dtype=np.int32)
        resolutions = np.zeros(M)
        
        for i, (key, cell) in enumerate(foveated_map.items()):
            points[i, 0] = cell['center_x']
            points[i, 1] = cell['center_y']
            points[i, 2] = cell['height']
            labels[i] = cell['label']
            resolutions[i] = cell['res']
            
        return points, labels, resolutions
