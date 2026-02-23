class TrafficLogic:
    def __init__(self, config):
        self.config = config

    def calculate_green_time(self, vehicle_count):
        """
        Calculates green light duration based on vehicle count.
        """
        if vehicle_count >= self.config.DENSITY_HIGH:
            return 90 # High traffic
        elif vehicle_count >= self.config.DENSITY_LOW:
            return 45 # Medium traffic
        else:
            return 15 # Low traffic

    def get_density_label(self, vehicle_count):
        if vehicle_count >= self.config.DENSITY_HIGH:
            return "High"
        elif vehicle_count >= self.config.DENSITY_LOW:
            return "Medium"
        else:
            return "Low"
