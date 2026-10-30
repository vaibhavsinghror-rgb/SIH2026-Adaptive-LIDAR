import numpy as np
from mapping.grid_engine import FoveatedGridEngine

class UniformGridEngine(FoveatedGridEngine):
    """
    Uniform high-resolution 2.5D grid engine.
    Used as the baseline for comparison.
    """
    def __init__(self, config):
        """
        Overrides the zones to use a single high-resolution zone across the entire range.
        """
        super().__init__(config)
        self.max_range = config.get('maximum_range', 100.0)
        baseline_res = config.get('near_resolution', 0.05)
        
        # Override with a single uniform zone
        self.zones = [
            {'max_r': self.max_range, 'res': baseline_res}
        ]
