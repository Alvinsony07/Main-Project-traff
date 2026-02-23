import time
import threading

class SignalController:
    def __init__(self, num_lanes=4):
        self.num_lanes = num_lanes
        # States: 0=RED, 1=YELLOW, 2=GREEN
        self.states = ["RED"] * num_lanes
        self.current_green_lane = 0 # Start with lane 0 (1-indexed visually)
        self.remaining_time = 0
        self.ambulance_active = False
        self.ambulance_lane = -1
        self.ambulance_cooldown = 0
        self.lock = threading.Lock()
        
        # Initialize
        self.states[0] = "GREEN"
    
    def update_state(self, current_time, get_lane_counts_callback, traffic_logic_ref):
        """
        Main loop logic helper.
        get_lane_counts_callback: function() -> {0: count, 1: count, ...}
        traffic_logic_ref: Reference to traffic logic instance for duration calculation
        """
        with self.lock:
            # If ambulance mode is active, override everything
            if self.ambulance_active:
                # Ensure the ambulance lane is GREEN, others RED
                for i in range(self.num_lanes):
                    if i == self.ambulance_lane:
                        self.states[i] = "GREEN"
                    else:
                        self.states[i] = "RED"
                self.remaining_time = 999 
                return

            # Normal Logic
            if self.remaining_time > 0:
                self.remaining_time -= 1
            else:
                # Time to switch
                if self.states[self.current_green_lane] == "GREEN":
                    # Switch to Yellow
                    self.states[self.current_green_lane] = "YELLOW"
                    self.remaining_time = 3 
                    
                elif self.states[self.current_green_lane] == "YELLOW":
                    # Switch to Red
                    self.states[self.current_green_lane] = "RED"
                    
                    # --- DENSITY PRIORITY LOGIC ---
                    # Feature Request: Analyze existing traffic and adjust lights accordingly
                    lane_counts = get_lane_counts_callback()
                    
                    next_lane = -1
                    max_vehicles = -1
                    
                    # 1. Analyze all waiting lanes to find the highest traffic density
                    for candidate in range(self.num_lanes):
                        if candidate == self.current_green_lane:
                            continue # Skip the one that just finished
                            
                        count = lane_counts.get(candidate, 0)
                        if count > max_vehicles and count > 0:
                            max_vehicles = count
                            next_lane = candidate
                    
                    # 2. If traffic is empty or uniform zero, fallback to standard cycle
                    if next_lane == -1:
                        next_lane = (self.current_green_lane + 1) % self.num_lanes

                    self.current_green_lane = next_lane
                    
                    # Set next lane to GREEN
                    self.states[self.current_green_lane] = "GREEN"
                    
                    # Calculate new green time
                    count = lane_counts.get(self.current_green_lane, 0)
                    duration = traffic_logic_ref.calculate_green_time(count)
                    self.remaining_time = duration

    def set_ambulance_event(self, lane_index, active):
        with self.lock:
            if active:
                self.ambulance_active = True
                self.ambulance_lane = lane_index
                # Maximize time so it doesn't switch
                self.remaining_time = 999 
                # Reset cooldown (approx 2 seconds at 5 detection/sec)
                self.ambulance_cooldown = 10 
            else:
                # Debounce Logic: 
                # Only reset if we were previously active to avoid resetting 'remaining_time' 
                # constantly during normal operation.
                if self.ambulance_active:
                    if self.ambulance_cooldown > 0:
                        self.ambulance_cooldown -= 1
                        return

                    self.ambulance_active = False
                    self.ambulance_lane = -1
                    # Give a buffer before switching back to normal flow
                    self.remaining_time = 5 

    def force_switch(self, lane_index):
        """Manually force a specific lane to turn GREEN"""
        with self.lock:
            if 0 <= lane_index < self.num_lanes:
                self.ambulance_active = False # Disable ambulance mode if forced
                self.current_green_lane = lane_index
                
                # Set all to RED first
                for i in range(self.num_lanes):
                    self.states[i] = "RED"
                
                # Set target to GREEN
                self.states[lane_index] = "GREEN"
                self.remaining_time = 30 # Default manual override duration
                return True
            return False

    def get_status(self):
        with self.lock:
            return {
                "states": self.states,
                "current_green": self.current_green_lane,
                "remaining_time": self.remaining_time,
                "ambulance_mode": self.ambulance_active
            }
