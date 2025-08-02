import concurrent.futures

# Executor compartido para peticiones HTTP
shared_executor = concurrent.futures.ThreadPoolExecutor(max_workers=6)

# Executor separado para tareas programadas
scheduler_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
