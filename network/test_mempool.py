from mempool import Mempool

pool = Mempool()

pool.add_transaction("Alice","Bob",100)
pool.add_transaction("Bob", "Charlie", 40)
pool.add_transaction("Charlie", "Dave", 15)

print("Marime mempool:", pool.size())

pending = pool.get_pending(max_count=2)
print("Extrase pentru minare:", pending)

pool.remove_transactions(pending)
print("Marime dupa remove:", pool.size()) 

print("Ce a mai ramas:", pool.get_pending())