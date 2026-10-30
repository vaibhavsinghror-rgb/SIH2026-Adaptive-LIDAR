import numpy as np

class HeuristicSegmenter:
    """
    A rule-based segmentation algorithm to simulate semantic labels.
    Used when a pre-trained deep learning model is not available.
    
    Classes:
    0: Unlabeled
    1: Drivable (road)
    2: Non-drivable ground (sidewalk, elevated terrain)
    3: Obstacle (vehicle, building, pole)
    """
    def __init__(self, ground_z_min=-2.0, ground_z_max=-1.3):
        self.ground_z_min = ground_z_min
        self.ground_z_max = ground_z_max

    def infer(self, points):
        """
        Args:
            points (np.ndarray): (N, 3) point coordinates.
        Returns:
            labels (np.ndarray): (N,) integer class labels.
        """
        N = points.shape[0]
        labels = np.zeros(N, dtype=np.int32)
        
        if N == 0:
            return labels
            
        z = points[:, 2]
        
        # Simple heuristic based on height (z)
        
        # Ground (assuming sensor is ~1.7m above ground, so z ~ -1.7)
        is_ground = (z >= self.ground_z_min) & (z <= self.ground_z_max)
        labels[is_ground] = 1
        
        # Slightly elevated ground (sidewalks)
        is_sidewalk = (z > self.ground_z_max) & (z <= self.ground_z_max + 0.3)
        labels[is_sidewalk] = 2
        
        # Obstacles (above ground)
        is_obstacle = z > self.ground_z_max + 0.3
        labels[is_obstacle] = 3
        
        return labels

# Define a color map for visualization
SEMANTIC_COLORS = {
    0: [0.5, 0.5, 0.5], # Unlabeled: Gray
    1: [1.0, 0.0, 1.0], # Drivable: Magenta
    2: [0.0, 1.0, 1.0], # Sidewalk: Cyan
    3: [1.0, 1.0, 0.0], # Obstacle: Yellow
}

def apply_semantic_colors(labels):
    """
    Map label indices to RGB colors.
    """
    colors = np.zeros((len(labels), 3))
    for cls_idx, color in SEMANTIC_COLORS.items():
        mask = (labels == cls_idx)
        colors[mask] = color
    return colors
