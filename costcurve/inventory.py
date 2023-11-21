import networkx as nx
from collections import Counter,defaultdict
from typing import List, Tuple, Set, Dict
from nlp import isit

class Inventory:
    def __init__(self, nodes: Set[str], edges: Set[Tuple[str, str]]):

        self._validate_edges(edges)
        self.graph = nx.DiGraph()
        self.graph.add_nodes_from(nodes)
        self.graph.add_edges_from(edges)
        self._set_indices()
        self.code_map = self._create_codes()

    def _validate_edges(self, edges: Set[Tuple[str, str]]):
        """
        Check that each child has only one parent

        TODO use typechecking to enforce that each tuple is a pair of strings
        """
        # Each child has only one parent implies that no node appears more than once as the second element in an edge
        children = [edge[1] for edge in edges]
        if len(children) != len(set(children)):
            raise Exception("Some nodes have more than one parent!")

    def _set_indices(self):
        """Initialize the indices of the nodes. The index is the digit in the place value that corresponds to the node depth"""
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

    def _get_children(self, node: str) -> List[str]:
        """Get the children of a node. Ie, get all x such that there is an edge (node,x) in the graph"""

        if not node in self.graph.nodes:
            raise Exception(f"{node} not in nodes: {list(self.graph.nodes)}")

        children = [child for (parent, child) in self.graph.edges if parent == node]
        return children


    def _get_parent(self, node: str) -> str:
        if not node in self.graph.nodes:
            raise Exception(f"{node} not in nodes: {list(self.graph.nodes)}")
        for edge in self.graph.edges:
            if edge[1] == node:
                return edge[0]

    def _get_ancestors(self, node, ancestors=None) -> List[str]:
        """Get the ancestors of a node recursively.
        we use the convention that every node is an ancestor of itself"""

        ancestors = ancestors or [node]
        parent = self._get_parent(node)
        if not parent:
            return ancestors
        else:
            ancestors.append(parent)
            anc = self._get_ancestors(parent, ancestors)
            return anc

    def _get_depth(self, node: str) -> int:
        """Get the number of ancestors of a node (including self)"""
        return len(self._get_ancestors(node))

    def _get_max_depth(self):
        return max([self._get_depth(nd) for nd in self.graph.nodes])

    def _get_code(self, node):
        """Construct the general ledger code of an item in the inventory"""

        index = nx.get_node_attributes(self.graph, "index")[node]
        multiplier = 10 ** (self._get_max_depth() - self._get_depth(node))
        parent = self._get_parent(node)
        if self._get_depth(node) == 1:
            return index * multiplier
        else:
            return index * multiplier + self._get_code(parent)

    def _create_codes(self) -> Dict[int, str]:
        code_item = {self._get_code(nd): nd for nd in self.graph.nodes}
        return {k: v for k, v in sorted(code_item.items())}

    def get_code_map(self) ->Dict[int,str]:
        return {k: v for k, v in sorted(self.code_map.items())}

    def _add_item_to_graph(self, item: str):
        if item in self.graph.nodes:
            raise Exception(f"{item} is already in nodes!")
        else:
            #if item is child of existing category, insert there
            parents = self._identify_parents(item)
            if len(parents) == 0:
                self._insert_root_category(item)
            elif len(parents) == 1:
                parent = parents[0]
                print("Parent",parent)
                self.graph.add_node(item)
                self.graph.add_edge(parent, item)
                #set the index of the new node
                siblings = self._get_children(parent)
                print("siblings", siblings)
                sibling_indices = [ind for nd, ind in nx.get_node_attributes(self.graph,name="index").items() if nd in siblings]
                max_sibling_index = max(sibling_indices)
                item_index = max_sibling_index +1
                nx.set_node_attributes(self.graph, values={item: item_index},name="index")
                self.code_map[self._get_code(item)] = item
            elif len(parents) > 1:
                raise NotImplementedError

    def _identify_parents(self, child) -> List[str]:
        """Find which category a new item belongs to using NLI"""
        depth_dict = defaultdict(list)
        for n in self.graph.nodes:
            depth_dict[self._get_depth(n)].append(n)

        for depth in sorted(range(1, self._get_max_depth() + 1), reverse=True):
            parents = list()
            items_at_depth = depth_dict[depth]
            for potential_parent in items_at_depth:
                print(child, potential_parent)
                if isit(child,potential_parent) > 0.5:
                    parents.append(potential_parent)
            if parents:
                #we only want the parent at the lowest depth of the tree (furthest from the roots)
                #(we don't want to retrieve all the ancestors)
                break

        return parents

    def _insert_root_category(self, item):
        """TODO check first to make sure that we have room for a root category. Then add it."""
        raise NotImplementedError