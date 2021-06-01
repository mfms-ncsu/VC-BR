__author__ = 'Nikhil, modified by Matthias Stallmann and Yang Ho'

import math

"""
 Implements a graph as a Python class.  A graph is a set of vertices and
 edges along with information related to the vertex cover problem. Each
 vertex has an adjacency list and a status, one of NOT_IN_COVER, IN_COVER, or
 UNDECIDED. In addition, a graph also has an upper bound - the number of
 vertices currently in the cover, and a lower bound - the minimum possible
 number of vertices in any cover. For the purpose of deciding which graph to
 process next during branch and bound a graph has a priority: the number of
 edges not covered by the set of vertices that are part of the cover.
"""

DEBUG = False

NOT_IN_COVER = 0
IN_COVER = 1
UNDECIDED = 2

# data fields for a graph G = (V,E) are as follows (some relate to the node containing G)
#  vertices = a list of vertices (each is an integer)
#  max_vertex = maximum number of any vertex (in case its not = # of vertices)
#  edges = a list of edges; each edge is a tuple of the form (v,w), where v,w are vertices
#  adjlist = a list of lists; adjlist[v] = a list of all neighbors of v
#  level = the depth of the node containing this graph in the B&B tree
#  max_matching = a maximum matching of the LR graph based on G
#                 (so that it can be augmented for a child of this node)
#  lb_runtime = total time spent computing LP reduction and/or lower bound for this node
#  lower_bound = lower bound for the node, based on lp_solution
#  vertex_status = a list with vertex_status[v] = one of
#      IN_COVER - there exists a minimum vertex cover of G containing v
#      NOT_IN_COVER - there exists a minimum vertex cover of G not containing v
#      UNDECIDED - neither of the previous two conditions necessarily holds
# Note: after an LP solution is computed, update_using_lp_solution()
#       updates both the vertex status and the lower_bound appropriately
class Graph:

    def __init__(self, vertices, max_vertex, edges, adjList):
        self.vertices = vertices
        self.max_vertex = max_vertex
        self.edges = edges
        self.adjList = adjList
        self.level = 0
        self.max_matching = set() 
        self.lower_bound = None
        self.vertex_status = {}
        for v in self.vertices:
            self.vertex_status[v] = UNDECIDED

    # dprinter us a debugging printer (see debug_printer.py) - so that the
    # printing of the graph will be indented appropriately
    def print_graph(self, dprinter):
        dprinter.dprint("graph:")
        vertex_string = " vertices:"
        for v in self.vertices:
            if self.vertex_status[v] == IN_COVER:
                vertex_string = "{0} {1:d}*".format(vertex_string, v)
            elif self.vertex_status[v] == NOT_IN_COVER:
                vertex_string = "{0} -{1:d}".format(vertex_string, v)
            else:
                vertex_string = "{0} {1:d}".format(vertex_string, v)
        dprinter.dprint(vertex_string)

        edge_string = " edges:"
        for e in self.edges:
            if not self.vertex_status[e[0]] == IN_COVER \
               and not self.vertex_status[e[1]] == IN_COVER:
                edge_string = "{0} ({1:d},{2:d})".format(edge_string, e[0], e[1])
        dprinter.dprint(edge_string)

    # sets status of v to be definitely IN_COVER or NOT_IN_COVER depending on
    # the value of is_in_min_vc; if a vertex is not in the cover, all of its
    # neighbors need to be
    def set_vertex_status(self, v, is_in_min_vc):
        if (is_in_min_vc):
            self.vertex_status[v] = IN_COVER
        else:
            self.vertex_status[v] = NOT_IN_COVER
            for u in self.adjList[v]:
                self.vertex_status[u] = IN_COVER
    
    # based on a theorem in Iwata et al., vertices whose LP solution value is
    # integral are in or out of the cover depending on that value
    # lp_solution is a dictionary, mapping vertices to their lp values
    # called after an LP lower bound or reduction is computed
    def update_using_lp_solution(self, lp_solution):
        for v in lp_solution:
            if lp_solution[v] == 1:
                self.vertex_status[v] = IN_COVER
            elif lp_solution[v] == 0:
                self.vertex_status[v] = NOT_IN_COVER
                
    # returns true if status of all vertices has been decided
    def is_solved(self):
        for v in self.vertices:
            if (self.vertex_status[v] == UNDECIDED):
                return False
        return True

    # can always get a trivial upper bound by putting the undecided vertices
    # in the cover
    def get_trivial_upper_bound(self):
        if DEBUG:
            print("-> graph.get_trivial_upper_bound")
        count = 0
        for v in self.vertices:
            if (self.vertex_status[v] == NOT_IN_COVER):
                continue
            count += 1
        if DEBUG:
            print("<- graph.get_trivial_upper_bound, count =", count)
        return count

    # updates the lower bound if the given value is better
    def set_lower_bound(self, lower_bound):
        if self.lower_bound == None or lower_bound > self.lower_bound:
            self.lower_bound = lower_bound
    

    def get_trivial_lower_bound(self):
        if DEBUG:
            print("-> graph.get_trivial_lower_bound")
        trivial_bound = 0
        for v in self.vertices:
            if (self.vertex_status[v] == IN_COVER):
                trivial_bound += 1
        if DEBUG:
            print("<- graph.get_trivial_lower_bound, lower_bound =", trivial_bound)
        return trivial_bound

    def get_lower_bound(self):
        return self.lower_bound

    # returns the effective number of vertices
    def get_num_undecided(self):
        if DEBUG:
            print("-> graph.get_num_undecided")
        count = 0
        for v in self.vertices:
            if (self.vertex_status[v] == UNDECIDED):
                count += 1
        if DEBUG:
            print("<- graph.get_num_undecided, count =", count)
        return count

    def select_branching_vertex(self):
        # For now select vertex with max degree; if there are ties, choose a
        # vertex that has the largest number of vertices within two hops.
        max_curr_deg_vertices = []
        max_curr_deg = 0
        for v in self.vertices:
            if self.vertex_status[v] == UNDECIDED:
                curr_deg = 0
                for u in self.adjList[v]:
                    if (self.vertex_status[u] == UNDECIDED):
                        curr_deg += 1
                if (curr_deg > max_curr_deg):        
                    max_curr_deg = curr_deg
                    max_curr_deg_vertices = [v]
                elif (curr_deg == max_curr_deg):
                    max_curr_deg_vertices.append(v)
        if (max_curr_deg == 2 or len(max_curr_deg_vertices) == 1):
            return max_curr_deg_vertices[0]
        v_having_max_num_u_with_curr_deg_2 = None
        max_num_u_with_curr_deg_2  = -1
        for v in max_curr_deg_vertices:
            num_u_with_curr_deg_2 = 0
            for u in self.adjList[v]:
                if (self.vertex_status[u] == UNDECIDED):
                    curr_deg_of_u = 0
                    for w in self.adjList[u]:
                        if (self.vertex_status[w] == UNDECIDED):
                            curr_deg_of_u += 1
                    if (curr_deg_of_u <= 2):
                        num_u_with_curr_deg_2 += 1
            if (num_u_with_curr_deg_2 > max_num_u_with_curr_deg_2):
                v_having_max_num_u_with_curr_deg_2 = v
                max_num_u_with_curr_deg_2 = num_u_with_curr_deg_2
        return v_having_max_num_u_with_curr_deg_2

    # return (as a set) the edges not covered by vertices known to be in a
    # minimum cover
    def get_uncovered_edges(self):
        uncovered_edges = set()
        for (u,v) in self.edges:
            u_status = self.vertex_status[u]
            v_status = self.vertex_status[v]
            if u_status != IN_COVER and v_status != IN_COVER:
                uncovered_edges.add((u,v))
        return uncovered_edges

    # return (as a list) the vertices whose status is not decided, i.e., the
    # ones in the effective graph at this node
    def get_undecided_vertices(self):
        undecided_vertices = []
        for v in self.vertices:
            if self.vertex_status[v] == UNDECIDED:
                undecided_vertices.append(v)
        return undecided_vertices

    # return (as a list) the edges both of whose endpoints are undecided,
    # i.e., the ones in the effective graph at this node
    def get_undecided_edges(self):
        undecided_edges = []
        for e in self.edges:
            v = e[0]
            w = e[1]
            if self.vertex_status[v] == UNDECIDED \
               and self.vertex_status[w] == UNDECIDED:
                undecided_edges.append(e)
        return undecided_edges

    # return (as a list) the vertices guaranteed to be in a miminum cover
    def get_vertices_in_cover(self):
        cover_vertices = []
        for v in self.vertices:
            if self.vertex_status[v] == IN_COVER:
                cover_vertices.append(v)
        return cover_vertices

    # return a tuple consisting of
    #   - vertices in the effective graph
    #   - edges in the effective graph
    #   - vertices known to be in a min cover
    #   - vertices for which a min cover exists that does not include them
    def get_stats(self):
        vertices_in_min_vc = []
        vertices_not_in_min_vc = []
        undecided_vertices = []
        undecided_edges = self.get_undecided_edges()
        # probably doesn't make much difference for now, but why not go
        # through the list of edges and check their endpoints instead of
        # looking at all neighbors of each vertex
        for v in self.vertices:
            if (self.vertex_status[v] == UNDECIDED):
                undecided_vertices.append(v)
            elif (self.vertex_status[v] == IN_COVER):
                vertices_in_min_vc.append(v)
            else:
                vertices_not_in_min_vc.append(v)

        return undecided_vertices, undecided_edges, vertices_in_min_vc, \
            vertices_not_in_min_vc

class GraphReader:

    def read_graph(self, file_path, file_format=None, directed=False):
        vertices = []
        max_vertex = 0
        edges = []
        adjList = {}
        # read in SNAP format
        # assume that no edge appears twice
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                # ignore comment line
                if (line.startswith("#")):
                    continue
                edge = line.split()
                u, v = int(edge[0]), int(edge[1])
                if u not in adjList:
                    vertices.append(u)
                    if u > max_vertex:
                        max_vertex = u
                    adjList[u] = set()
                if v not in adjList:
                    vertices.append(v)
                    if v > max_vertex:
                        max_vertex = v
                    adjList[v] = set()
                # at this point, both u and v are in the list of vertices and
                # each has a, possibly empty, adjacency list
                if v not in adjList[u]:
                    edges.append((u, v))
                    adjList[u].add(v)
                    if not directed:
                        adjList[v].add(u)
        return Graph(vertices=vertices, max_vertex = max_vertex,
                     edges=edges, adjList=adjList)

#  [Last modified: 2020 02 27 at 22:33:25 GMT]
