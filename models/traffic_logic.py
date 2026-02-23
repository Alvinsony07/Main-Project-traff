class TrafficLogic:
    def __init__(self, config):
        self.config = config

    def calculate_green_time(self, vehicle_count):
        """
        Sets a fixed duration of exactly 30 seconds for the green light, 
        as requested for the demonstration.
        """
        return 30

    def get_density_label(self, vehicle_count):
        if vehicle_count >= self.config.DENSITY_HIGH:
            return "High"
        elif vehicle_count >= self.config.DENSITY_LOW:
            return "Medium"
        else:
            return "Low"
