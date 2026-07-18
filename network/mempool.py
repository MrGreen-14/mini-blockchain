import threading

class Mempool:
    def __init__(self):
        self._transactions=[]# lista de tuple (sender, receiver, amount)
        self._lock = threading.Lock()

    def add_transaction(self,sender: str, receiver: str, amount: int):
        with self._lock:
            self._transactions.append((sender,receiver,amount))

    def get_pending(self,max_count: int= None):
        """Returneaza o COPIE a tranzactiilor curente (nu le scoate)."""
        with self._lock:
            if max_count is None:
                return list(self._transactions)
            return list(self._transactions[:max_count])
    def remove_transactions(self,txs_to_remove):
        """Scoate exact tranzactiile date (dupa minare cu succes)."""
        with self._lock:
            for tx in txs_to_remove:
                if tx in txs_to_remove:
                    self._transactions.remove(tx)
    def size(self):
        with self._lock:
            return len(self._transactions)