import simpy
import random
import numpy as np
from icecream import ic
from collections import defaultdict

class WaterfallSimulation:
    def __init__(self, K, ks, kf, arrival_rate, service_rate_exec, service_rate_feedback, 
                 backup_probability=0.5, simulation_time=1000):
        self.env = simpy.Environment()
        self.exec_queue = simpy.Resource(self.env, capacity=K)
        self.feedback_queue = simpy.Resource(self.env, capacity=1)
        
        self.ks = ks  # Execution queue size
        self.kf = kf  # Feedback queue size
        self.arrival_rate = arrival_rate
        self.service_rate_exec = service_rate_exec
        self.service_rate_feedback = service_rate_feedback
        self.backup_probability = backup_probability
        
        # Statistics
        self.waiting_times_exec = []
        self.waiting_times_feedback = []
        self.service_times = []
        self.refusals_exec = 0
        self.refusals_feedback = 0
        self.backup_results = []

        self.simulation_time = simulation_time
        
    def student(self):
        arrival_time = self.env.now
        
        # Execution queue
        if len(self.exec_queue.queue) >= self.ks:
            self.refusals_exec += 1
            return
            
        queue_entry_time = self.env.now
        with self.exec_queue.request() as req:
            yield req
            self.waiting_times_exec.append(self.env.now - queue_entry_time)
            yield self.env.timeout(random.expovariate(self.service_rate_exec))
            
        # Simulate test result and backup
        result = f"result_{self.env.now}"
        if random.random() < self.backup_probability:
            self.backup_results.append(result)
            
        # Feedback queue
        if len(self.feedback_queue.queue) >= self.kf:
            self.refusals_feedback += 1
            return
            
        queue_entry_time = self.env.now
        with self.feedback_queue.request() as req:
            yield req
            self.waiting_times_feedback.append(self.env.now - queue_entry_time)
            yield self.env.timeout(random.expovariate(self.service_rate_feedback))
            
        self.service_times.append(self.env.now - arrival_time)
        
    def run(self):
        def arrival_generator():
            while True:
                yield self.env.timeout(random.expovariate(self.arrival_rate))
                self.env.process(self.student())
                
        self.env.process(arrival_generator())
        self.env.run(until=self.simulation_time)
        
    def get_statistics(self):
        stats = {
            'avg_waiting_time_exec': np.mean(self.waiting_times_exec) if self.waiting_times_exec else 0,
            'avg_waiting_time_feedback': np.mean(self.waiting_times_feedback) if self.waiting_times_feedback else 0,
            'avg_service_time': np.mean(self.service_times) if self.service_times else 0,
            'service_time_variance': np.var(self.service_times) if self.service_times else 0,
            'blocking_rate_exec': self.refusals_exec / (len(self.service_times) + self.refusals_exec) if (len(self.service_times) + self.refusals_exec) > 0 else 0,
            'blocking_rate_feedback': self.refusals_feedback / (len(self.service_times) + self.refusals_feedback) if (len(self.service_times) + self.refusals_feedback) > 0 else 0,
            'backup_ratio': len(self.backup_results) / len(self.service_times) if self.service_times else 0
        }
        return stats

# Usage example
sim = WaterfallSimulation(
    K=3,                    # Number of execution servers
    ks=10,                  # Execution queue capacity
    kf=5,                   # Feedback queue capacity
    arrival_rate=5,
    service_rate_exec=3,
    service_rate_feedback=2,
    backup_probability=0.5,
    simulation_time=1000
)
sim.run()
stats = sim.get_statistics()
ic(stats)