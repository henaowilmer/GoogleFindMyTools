import concurrent.futures

# Executor compartido para toda la aplicación
shared_executor = concurrent.futures.ThreadPoolExecutor(max_workers=6)
