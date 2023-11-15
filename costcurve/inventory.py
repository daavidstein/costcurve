import networkx as nx
from collections import Counter,defaultdict
from typing import List, Tuple, Set, Dict
from nlp import isit
class Inventory:
    def __init__(self, nodes: Set[str], edges: Set[Tuple[str, str]]):

        self.validate_edges(edges)
        self.graph = nx.DiGraph()
        self.graph.add_nodes_from(nodes)
        self.graph.add_edges_from(edges)
        self.set_indices()
        self.code_map = self.create_codes()

    def validate_edges(self, edges: Set[Tuple[str, str]]):
        """
        Check that each child has only one parent

        TODO use typechecking to enforce that each tuple is a pair of strings
        """
        # Each child has only one parent implies that no node appears more than once as the second element in an edge
        children = [edge[1] for edge in edges]
        if len(children) != len(set(children)):
            raise Exception("Some nodes have more than one parent!")

    def set_indices(self):
        seen = Counter()
        indices = dict()
        for e in self.graph.edges:
            seen[e[0]] += 1
            indices[e[1]] = seen[e[0]]

        # set indices of root nodes
        root_nodes = [node for node, degree in self.graph.in_degree() if degree == 0]
        for i, rt in enumerate(root_nodes):
            indices[rt] = i + 1

        nx.set_node_attributes(self.graph, indices, "index")

    def get_parent(self, node: str) -> str:
        if not node in self.graph.nodes:
            raise Exception(f"{node} not in nodes: {list(self.graph.nodes)}")
        for edge in self.graph.edges:
            if edge[1] == node:
                return edge[0]

    def get_ancestors(self, node, ancestors=None) -> List[str]:
        """Get the ancestors of a node recursively.
        we use the convention that every node is an ancestor of itself"""

        ancestors = ancestors or [node]
        parent = self.get_parent(node)
        if not parent:
            return ancestors
        else:
            ancestors.append(parent)
            anc = self.get_ancestors(parent, ancestors)
            return anc

    def get_depth(self, node: str) -> int:
        """Get the number of ancestors of a node (including self)"""
        return len(self.get_ancestors(node))

    def get_max_depth(self):
        return max([self.get_depth(nd) for nd in self.graph.nodes])

    def get_code(self, node):
        """Construct the general ledger code of an item in the inventory"""

        index = nx.get_node_attributes(self.graph, "index")[node]
        multiplier = 10 ** (self.get_max_depth() - self.get_depth(node))
        parent = self.get_parent(node)
        if self.get_depth(node) == 1:
            return index * multiplier
        else:
            return index * multiplier + self.get_code(parent)

    def create_codes(self) -> Dict[int, str]:
        code_item = {self.get_code(nd): nd for nd in self.graph.nodes}
        return {k: v for k, v in sorted(code_item.items())}

    def add_item_to_graph(self,item: str):
        if item in self.graph.nodes:
            raise Exception(f"{item} is already in nodes!")
        else:
            #if item is child of existing category, insert there
            parents = self.identify_parents(item)
            if len(parents) == 0:
                self.insert_root_category(item)
            elif len(parents) == 1:
                parent = parents[0]
                self.graph.add_node(item)
                self.graph.add_edge(parent, item)
                self.code_map[self.get_code(item)] = item
            elif len(parents) > 1:
                raise NotImplementedError
    def identify_parents(self,child) -> List[str]:
        """FIXME instead of querying gpt individually for every node at a depth level
        we could probably reduce the number of requests (and waiting time) by giving gpt a list of items at that depth
        and asking whether the item is a member of any of those
        b"""
        depth_dict = defaultdict(list)
        for n in self.graph.nodes:
            depth_dict[self.get_depth(n)].append(n)

        parents = list()
        for depth in sorted(range(1, self.get_max_depth()+1), reverse=True):
            items_at_depth = depth_dict[depth]
            for potential_parent in items_at_depth:
                if isit(child, potential_parent):
                    parents.append(potential_parent)
            if parents:
                #we only want the parent at the lowest depth of the tree (furthest from the roots)
                #(we don't want to retrieve all the ancestors)
                break

        return parents

    def insert_root_category(self,item):
        """TODO check first to make sure that we have room for a root category. Then add it."""
        raise NotImplementedError