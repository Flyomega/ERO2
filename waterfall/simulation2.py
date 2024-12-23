import simpy
import random

# Paramètres globaux
RANDOM_SEED = 42  # Pour rendre les résultats reproductibles
ARRIVAL_RATE = 5  # Taux d'arrivée des étudiants (tags soumis) par unité de temps
SERVICE_RATE_EXECUTION = 3  # Taux de traitement des serveurs d'exécution (par unité de temps)
SERVICE_RATE_FEEDBACK = 2  # Taux de traitement du serveur de feedback (par unité de temps)
EXEC_QUEUE_CAPACITY = 10  # Capacité maximale de la file d'attente d'exécution
FEEDBACK_QUEUE_CAPACITY = 5  # Capacité maximale de la file d'attente de feedback
SIMULATION_TIME = 50  # Temps total de simulation

# Statistiques globales
refus_executions = 0
refus_feedback = 0
temps_de_sejour_total = []

# Processus d'un étudiant
def student(env, exec_queue, feedback_queue):
    global refus_executions, refus_feedback

    arrival_time = env.now

    # Étape 1 : File d'exécution
    if len(exec_queue.queue) >= EXEC_QUEUE_CAPACITY:
        refus_executions += 1
        return

    with exec_queue.request() as req:
        yield req
        yield env.timeout(random.expovariate(SERVICE_RATE_EXECUTION))

    # Étape 2 : File de feedback
    if len(feedback_queue.queue) >= FEEDBACK_QUEUE_CAPACITY:
        refus_feedback += 1
        return

    with feedback_queue.request() as req:
        yield req
        yield env.timeout(random.expovariate(SERVICE_RATE_FEEDBACK))

    # Temps de séjour total
    temps_de_sejour_total.append(env.now - arrival_time)

# Générateur d'arrivées
def arrival_generator(env, exec_queue, feedback_queue):
    while True:
        yield env.timeout(random.expovariate(ARRIVAL_RATE))
        env.process(student(env, exec_queue, feedback_queue))

# Configuration de la simulation
random.seed(RANDOM_SEED)
env = simpy.Environment()
exec_queue = simpy.Resource(env, capacity=EXEC_QUEUE_CAPACITY)
feedback_queue = simpy.Resource(env, capacity=1)  # 1 serveur unique pour feedback

# Lancer le générateur d'arrivées
env.process(arrival_generator(env, exec_queue, feedback_queue))

# Lancer la simulation
env.run(until=SIMULATION_TIME)

# Résultats
print("Simulation terminée :")
print(f"Nombre total de refus dans la file d'exécution : {refus_executions}")
print(f"Nombre total de refus dans la file de feedback : {refus_feedback}")
if temps_de_sejour_total:
    print(f"Temps de séjour moyen : {sum(temps_de_sejour_total) / len(temps_de_sejour_total):.2f}")
    print(f"Temps de séjour max : {max(temps_de_sejour_total):.2f}")
else:
    print("Aucun étudiant n'a terminé le processus complet.")
