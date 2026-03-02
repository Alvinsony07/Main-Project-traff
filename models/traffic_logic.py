class TrafficLogic:
    def __init__(self, config):
        self.config = config

    def calculate_green_time(self, vehicle_count):
        """
        Calculates adaptive green-light duration based on real-time vehicle density.
        Uses linear interpolation between MIN_GREEN_TIME and MAX_GREEN_TIME
        scaled by the ratio of current count to DENSITY_HIGH threshold.
        """
        min_t = self.config.MIN_GREEN_TIME   # e.g. 10s
        max_t = self.config.MAX_GREEN_TIME   # e.g. 120s
        high  = self.config.DENSITY_HIGH     # e.g. 30 vehicles

        if vehicle_count <= 0:
            return min_t

        # Linear scale: 0 vehicles → min_t, DENSITY_HIGH vehicles → max_t
        ratio = min(vehicle_count / high, 1.0)
        duration = int(min_t + (max_t - min_t) * ratio)
        return max(min_t, min(duration, max_t))

    def get_density_label(self, vehicle_count):
        if vehicle_count >= self.config.DENSITY_HIGH:
            return "High"
        elif vehicle_count >= self.config.DENSITY_LOW:
            return "Medium"
        else:
            return "Low"
