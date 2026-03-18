import heapq
import math

class CurrencyGraph:
    def __init__(self):
        self.adj_list = {}

    def add_edge(self, from_currency, to_currency, rate):
        if from_currency not in self.adj_list:
            self.adj_list[from_currency] = []
        
        # Dijkstra için maliyeti -log(rate) olarak hesapla
        cost = -math.log(rate)
        self.adj_list[from_currency].append({
            'to': to_currency, 
            'cost': cost, 
            'rate': rate
        })

    def get_best_conversion_rate(self, start_curr, target_curr):
        if start_curr not in self.adj_list:
            return None, 0.0

        pq = [(0, start_curr, [start_curr])]
        visited = set()
        best_rates = {start_curr: 1.0}

        while pq:
            current_cost, current_node, path = heapq.heappop(pq)

            if current_node == target_curr:
                return path, best_rates[current_node]

            if current_node in visited:
                continue
            
            visited.add(current_node)

            for neighbor in self.adj_list.get(current_node, []):
                neighbor_node = neighbor['to']
                edge_cost = neighbor['cost']
                edge_rate = neighbor['rate']

                if neighbor_node not in visited:
                    new_cost = current_cost + edge_cost
                    new_path = path + [neighbor_node]
                    
                    best_rates[neighbor_node] = best_rates.get(current_node, 1.0) * edge_rate
                    heapq.heappush(pq, (new_cost, neighbor_node, new_path))
        
        return None, 0.0