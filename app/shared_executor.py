import concurrent.futures

shared_executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)
