## Scripts that generate instances or convert format of instances ##

### Files in lexicographic order

------------------------------------------------------------------------

-   **[affinity_graph.py](affinity_graph.py)**

         affinity_graph.py - offers a mechanism for producing an affinity graph as follows:
           - create a random bipartite graph G_B = (V_0, V_1, A)
           - for each v,w in V_0, add edge vw if there exists x in V_1 such that vx,wx in A
           - remove V_1

         @author Matthias Stallmann
         @date 2018/3/29

-   **[ba_gen.py](ba_gen.py)**

        ba_gen.py - a generator of a Barabasi-Albert graph given number of
        vertices and desired average degree

-   **[bl_rg.py](bl_rg.py)**

        bl_rg.py - (bucket-list random graph) generates graphs with a specified degree variance,
                   minimum degree and maximum degree
                   uses a list of buckets, each bucket storing vertices of the same degree
                   a graph is printed to standard output in snap format

        @author Matt Stallmann
        @date 2018/7/18

-   **[cl_gen.py](cl_gen.py)**

        cl_gen.py - a generator of a Chung-Lu graph given various parameters relating to
                    degree sequence generation; also has option of reading sequence from
                    file or standard input

-   **[cluster_graphs.py](cluster_graphs.py)**

            Given a stochastic block matrix, compute the expected number of edges

-   **[create_lpx.sh](create_lpx.sh)**

         creates a directory containing cplex input instances from instances in a given directory
         note: snap2lpx.py must be in the same directory as this script

-   **[delaunay.py](delaunay.py)**

         Obtained from
          http://code.activestate.com/recipes/579021-delaunay-triangulation/
         The algorithm uses the S-hull method by D A Sinclair
         (http://www.s-hull.org/paper/s_hull.pdf). The method involves ordering the
         points in increasing distance from the cloud's center of gravity, creating
         a triangle with the first three points, and adding the remaining points
         while contructing triangles between the point and boundary edges - only
         triangles with a definite sign need to be added (the edge must be
         visible). Finally, an edge flipping step ensures that the triangles are
         well formed, i.e. the sum of opposite angles to an edge is < 180 degree
         (the so-called Delaunay criterion).

-   **[permute_graph.py](permute_graph.py)**

        creates a given number of copies of a graph in snap format;
        the vertices are randomly renumbered and edges put in random order in each copy

-   **[random_delaunay.py](random_delaunay.py)**

         creates a random Delaunay triangulation using delaunay.py to do the
         triangulation after a random set of points have been
         chosen; there is an option to triangulate the infinite face

-   **[snap2edgelist.py](snap2edgelist.py)**

        converts snap format to a simple edgelist format where the first line gives
        number of vertices and edges, respectively, and the remaining lines give
        endpoints of edges. Vertex numbers in the output range from 0 to n-1, where
        n is the number of vertices.
        The following assumptions are made about the input:
          - vertex numbers go from 1 to n
          - if a vertex number is > n, then the max vertex number is used as number of vertices
            in the output (no harm done for the oct estimator)

-   **[snap2graphml.py](snap2graphml.py)**

         translates from snap format, described below, to the graphml format
         used by Galant or Gephi;
         this program is a simple filter, translating from standard input to standard output.

         snap format is as follows:

            # comment line 1
            ...
            # comment line k

            source_1 target_1
            ...
            source_m target_m

         sources and targets are vertex numbers starting at 1

-   **[snap2lpx.py](snap2lpx.py)**

         lightweight script to convert a snap file to a CPLEX-readable file;
         vertices numbered 0 through the maximum vertex number are assumed to exist;
         no harm done if they don't - it simply means that
         there will be variables not involved in any constraints;
         reason for this is so that the -verify option in cplex_ilp produces a string
         of 0's and 1's that represents vertices starting at vertex 0.

-   **[wcg_gen.py](wcg_gen.py)**

        wcg_gen.py - generates dense graphs with small vertex covers by expanding a construction
                     that shows the greedy heuristic to have arbitrarily bad approximation ratio

[Matthias F. (Matt) Stallmann](http://people.engr.ncsu.edu/mfms/)
Created: Thu Nov 21 15:15:00 EST 2019
