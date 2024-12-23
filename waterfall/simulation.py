import simpy
import random
import numpy as np
from icecream import ic
from collections import defaultdict

class TestingInfrastructureSimulation:
    def __init__(self, test_servers, exec_queue_size, feedback_queue_size, 
                 tag_rate, test_execution_rate, feedback_rate, simulation_time=1000):
        self.env = simpy.Environment()
        self.test_servers = simpy.Resource(self.env, capacity=test_servers)
        self.feedback_server = simpy.Resource(self.env, capacity=1)
        
        self.exec_queue_size = exec_queue_size
        self.feedback_queue_size = feedback_queue_size
        self.tag_rate = tag_rate  # Taux d'arrivée des push tags
        self.test_execution_rate = test_execution_rate  # Taux de service des tests
        self.feedback_rate = feedback_rate  # Taux de service du feedback
        
        # Statistiques détaillées
        self.waiting_times_exec = []
        self.waiting_times_feedback = []
        self.total_processing_times = []
        self.queue_lengths_exec = []
        self.queue_lengths_feedback = []
        self.rejections_exec = 0
        self.rejections_feedback = 0
        self.total_submissions = 0
        
        self.simulation_time = simulation_time
        
    def student_submission(self):
        arrival_time = self.env.now
        self.total_submissions += 1
        
        # Phase d'exécution des tests
        if len(self.test_servers.queue) >= self.exec_queue_size:
            self.rejections_exec += 1
            return
            
        queue_entry_time = self.env.now
        self.queue_lengths_exec.append(len(self.test_servers.queue))
        
        with self.test_servers.request() as req:
            yield req
            wait_time = self.env.now - queue_entry_time
            self.waiting_times_exec.append(wait_time)
            # Simulation de l'exécution des tests
            yield self.env.timeout(random.expovariate(self.test_execution_rate))
        
        # Phase de feedback
        if len(self.feedback_server.queue) >= self.feedback_queue_size:
            self.rejections_feedback += 1
            return
            
        queue_entry_time = self.env.now
        self.queue_lengths_feedback.append(len(self.feedback_server.queue))
        
        with self.feedback_server.request() as req:
            yield req
            wait_time = self.env.now - queue_entry_time
            self.waiting_times_feedback.append(wait_time)
            yield self.env.timeout(random.expovariate(self.feedback_rate))
        
        self.total_processing_times.append(self.env.now - arrival_time)
        
    def run(self):
        def tag_generator():
            while True:
                yield self.env.timeout(random.expovariate(self.tag_rate))
                self.env.process(self.student_submission())
                
        self.env.process(tag_generator())
        self.env.run(until=self.simulation_time)
        
    def get_statistics(self):
        stats = {
            'Métriques temporelles': {
                'temps_attente_moyen_tests': np.mean(self.waiting_times_exec) if self.waiting_times_exec else 0,
                'temps_attente_moyen_feedback': np.mean(self.waiting_times_feedback) if self.waiting_times_feedback else 0,
                'temps_total_moyen': np.mean(self.total_processing_times) if self.total_processing_times else 0,
                'variance_temps_total': np.var(self.total_processing_times) if self.total_processing_times else 0
            },
            'Métriques de charge': {
                'longueur_moyenne_file_tests': np.mean(self.queue_lengths_exec) if self.queue_lengths_exec else 0,
                'longueur_moyenne_file_feedback': np.mean(self.queue_lengths_feedback) if self.queue_lengths_feedback else 0
            },
            'Métriques de rejet': {
                'taux_rejet_tests': self.rejections_exec / self.total_submissions if self.total_submissions > 0 else 0,
                'taux_rejet_feedback': self.rejections_feedback / self.total_submissions if self.total_submissions > 0 else 0
            }
        }
        return stats

# Exemple d'utilisation avec des paramètres réalistes
sim = TestingInfrastructureSimulation(
    test_servers=3,           # Nombre de serveurs pour l'exécution des tests
    exec_queue_size=20,       # Capacité de la file d'attente des tests
    feedback_queue_size=10,   # Capacité de la file d'attente du feedback
    tag_rate=1.0,            # En moyenne 1 push tag par unité de temps
    test_execution_rate=0.5,  # En moyenne 2 unités de temps par test
    feedback_rate=2.0,        # En moyenne 0.5 unité de temps par feedback
    simulation_time=1000
)
sim.run()
stats = sim.get_statistics()
ic(stats)