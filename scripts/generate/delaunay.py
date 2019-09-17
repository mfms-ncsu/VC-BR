#! /usr/bin/env python3

"""
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
"""

import numpy
from numpy import array
import math
import copy
import sys
from collections import deque   # for use as a queue in triangulateInfiniteFace


class Delaunay2d:

  EPS = 1.23456789e-14

  def __init__(self, points):

    # data structures
    # a copy of the set of points, which gets mangled in the process
    self.points = points[:]
    # a list of triangles, each is a list of the three vertices, indexes into
    # the list of points (not necessarily the same order as input points)
    self.triangles = []
    # the following maps each edge tuple (v,w) to a list of one (if on the
    # boundary) or two triangles, represented as indexes into the triangles
    # list
    self.edge2Triangles = {}
    self.boundaryEdges = set()
    self.appliedBoundaryEdges = None
    self.holes = None

    
    # compute center of gravity
    cg = numpy.zeros((2,), numpy.float64)
    for pt in points:
      cg += pt
    cg /= len(points)

    # sort
    def distanceSquare(pt):
      d = pt - cg
      return numpy.dot(d, d)
    self.points.sort(key = distanceSquare)
    self.sorted_points = self.points[:]

    # create first triangle, make sure we're getting a non-zero area otherwise
    # drop the points
    area = 0.0
    index = 0
    stop = False
    while not stop and index + 2 < len(points):
      area = self.getArea(index, index + 1, index + 2)
      if abs(area) < self.EPS:
        del self.points[index]
      else:
        stop = True
    if index <= len(self.points) - 3:
      tri = [index, index + 1, index + 2]
      self.makeCounterClockwise(tri)
      self.triangles.append(tri)

      # boundary edges
      e01 = (tri[0], tri[1])
      self.boundaryEdges.add(e01)
      e12 = (tri[1], tri[2])
      self.boundaryEdges.add(e12)
      e20 = (tri[2], tri[0])
      self.boundaryEdges.add(e20)

      e01 = self.makeKey(e01[0], e01[1])
      self.edge2Triangles[e01] = [0,]

      e12 = self.makeKey(e12[0], e12[1])
      self.edge2Triangles[e12] = [0,]

      e20 = self.makeKey(e20[0], e20[1])
      self.edge2Triangles[e20] = [0,]

    else:
      # all the points fall on a line
      return

    # add additional points
    for i in range(3, len(self.points)):
      self.addPoint(i)

    self.triangleEdges = set(self.edge2Triangles.keys())
    self.boundaryVertices = self.computeBoundaryVertices()
    
  def sortedEdge(self, edge):
    """
    @param edge a tuple giving the two endpoints of an edge
    @return a tuple with the endpoints sorted in ascending order,
            useful when an edge is a key in a map
    """
    edgeSorted = list(edge)
    edgeSorted.sort()
    return tuple(edgeSorted)

  def getPoints(self):
    """
    @return a list of the points, each point an array of length 2 (numpy)
            in the order used by the algorithm,
            which is not necessarily the same as the input order
    """
    return self.sorted_points

  def getTriangles(self):
    """
    @return triangles as a list in which each element is a list of three triangle vertices
    """
    return self.triangles

  def getEdges(self):
    """
    @return triangle edges as a set, each edge is a pair (tuple of length 2)
    """
    return self.triangleEdges

  def getDualEdges(self):
    """
    @return edges of the dual graph as a set,
            assuming it has been computed using computeDual
    """
    return self.dualEdges

  def getDualPoints(self):
    """
    @return centroids of the triangles, which become the points/vertices of the dual,
            as arrays of length 2 (numpy)
    """
    return self.dualPoints

  def getBoundaryEdges(self):
    """
    @return boundary edges as a set; not valid after infinite face has been triangulated
    """
    return self.boundaryEdges

  def getBoundaryVertices(self):
    """
    @return the vertices on the boundary in cyclic order (as a list);
            not valid after the infinite face is triangulated
    """
    return self.boundaryVertices
  
  def getArea(self, ip0, ip1, ip2):
    """
    Compute the parallelipiped area
    @param ip0 index of first vertex
    @param ip1 index of second vertex
    @param ip2 index of third vertex
    """
    d1 = self.points[ip1] - self.points[ip0]
    d2 = self.points[ip2] - self.points[ip0]
    return (d1[0]*d2[1] - d1[1]*d2[0])

  def isEdgeVisible(self, ip, edge):
    """
    Return true iff the point lies to its right when the edge points down
    @param ip point index
    @param edge (2 point indices with orientation)
    @return True if visible    
    """
    area = self.getArea(ip, edge[0], edge[1])
    if area < self.EPS:
      return True
    return False

  def makeCounterClockwise(self, ips):
    """
    Re-order nodes to ensure positive area (in-place operation)
    """
    area = self.getArea(ips[0], ips[1], ips[2])
    if area < -self.EPS:
      ip1, ip2 = ips[1], ips[2]
      # swap
      ips[1], ips[2] = ip2, ip1

  def flipOneEdge(self, edge):
    """
    Flip one edge then update the data structures
    @return set of edges to interate over at next iteration
    """

    # start with empty set
    res = set()

    # assume edge is sorted
    tris = self.edge2Triangles.get(edge, [])
    if len(tris) < 2:
        # nothing to do, just return
        return res

    iTri1, iTri2 = tris
    tri1 = self.triangles[iTri1]
    tri2 = self.triangles[iTri2]

    # find the opposite vertices, not part of the edge
    iOpposite1 = -1
    iOpposite2 = -1
    for i in range(3):
      if not tri1[i] in edge:
        iOpposite1 = tri1[i]
      if not tri2[i] in edge:
        iOpposite2 = tri2[i]

    # compute the 2 angles at the opposite vertices
    da1 = self.points[edge[0]] - self.points[iOpposite1]
    db1 = self.points[edge[1]] - self.points[iOpposite1]
    da2 = self.points[edge[0]] - self.points[iOpposite2]
    db2 = self.points[edge[1]] - self.points[iOpposite2]
    crossProd1 = self.getArea(iOpposite1, edge[0], edge[1])
    crossProd2 = self.getArea(iOpposite2, edge[1], edge[0])
    dotProd1 = numpy.dot(da1, db1)
    dotProd2 = numpy.dot(da2, db2)
    angle1 = abs(math.atan2(crossProd1, dotProd1))
    angle2 = abs(math.atan2(crossProd2, dotProd2))
    
    # Delaunay's test
    if angle1 + angle2 > math.pi*(1.0 + self.EPS):

      # flip the triangles
      #             / ^ \                    / b \
      # iOpposite1 + a|b + iOpposite2  =>   + - > +
      #             \   /                    \ a /

      newTri1 = [iOpposite1, edge[0], iOpposite2] # triangle a
      newTri2 = [iOpposite1, iOpposite2, edge[1]] # triangle b

      # update the triangle data structure
      self.triangles[iTri1] = newTri1
      self.triangles[iTri2] = newTri2

      # now handle the topolgy of the edges

      # remove this edge
      del self.edge2Triangles[edge]

      # add new edge
      e = self.makeKey(iOpposite1, iOpposite2)
      self.edge2Triangles[e] = [iTri1, iTri2]

      # modify two edge entries which now connect to 
      # a different triangle
      e = self.makeKey(iOpposite1, edge[1])
      v = self.edge2Triangles[e]
      for i in range(len(v)):
        if v[i] == iTri1:
          v[i] = iTri2
      res.add(e)

      e = self.makeKey(iOpposite2, edge[0])
      v = self.edge2Triangles[e]
      for i in range(len(v)):
        if v[i] == iTri2:
          v[i] = iTri1
      res.add(e)

      # these two edges might need to be flipped at the
      # next iteration
      res.add(self.makeKey(iOpposite1, edge[0]))
      res.add(self.makeKey(iOpposite2, edge[1]))

    return res 

  def flipEdges(self):
    """
    Flip edges to statisfy Delaunay's criterion
    """

    # start with all the edges
    edgeSet = set(self.edge2Triangles.keys())

    continueFlipping = True

    while continueFlipping:

      #
      # iterate until there are no more edges to flip
      #

      # collect the edges to flip
      newEdgeSet = set()
      for edge in edgeSet:
        # union
        newEdgeSet |= self.flipOneEdge(edge)

      edgeSet = copy.copy(newEdgeSet)
      continueFlipping = (len(edgeSet) > 0)

  def addPoint(self, ip):
    """
    Add point
    @param ip point index
    """

    # collection for later updates
    boundaryEdgesToRemove = set()
    boundaryEdgesToAdd = set()

    for edge in self.boundaryEdges:

      if self.isEdgeVisible(ip, edge):

        # create new triangle
        newTri = [edge[0], edge[1], ip]
        newTri.sort()
        self.makeCounterClockwise(newTri)
        self.triangles.append(newTri)

        # update the edge to triangle map
        e = list(edge[:])
        e.sort()
        iTri = len(self.triangles) - 1 
        self.edge2Triangles[tuple(e)].append(iTri)

        # add the two boundary edges
        e1 = [ip, edge[0]]
        e1.sort()
        e1 = tuple(e1)
        e2 = [edge[1], ip]
        e2.sort()
        e2 = tuple(e2)
        v1 = self.edge2Triangles.get(e1, [])
        v1.append(iTri)
        v2 = self.edge2Triangles.get(e2, [])
        v2.append(iTri)
        self.edge2Triangles[e1] = v1
        self.edge2Triangles[e2] = v2

        # keep track of the boundary edges to update
        boundaryEdgesToRemove.add(edge)
        boundaryEdgesToAdd.add( (edge[0], ip) )
        boundaryEdgesToAdd.add( (ip, edge[1]) )

    # update the boundary edges
    for bedge in boundaryEdgesToRemove:
      self.boundaryEdges.remove(bedge)
    for bedge in boundaryEdgesToAdd:
      bEdgeSorted = self.sortedEdge(bedge)
      if len(self.edge2Triangles[bEdgeSorted]) == 1:
        # only add boundary edge if it does not appear
        # twice in different order
        self.boundaryEdges.add(bedge)

    # recursively flip edges
    flipped = True
    while flipped:
      flipped = self.flipEdges()

  def makeKey(self, i1, i2):
    """
    Make a tuple key such at i1 < i2
    """
    if i1 < i2:
      return (i1, i2)
    return (i2, i1)

  def otherEnd(self, e, v):
    """
    @param e an edge represented as a list of two vertices (integers)
    @param v a vertex (integer)
    @return the vertex in e that is not v
    """
    if e[0] == v:
      return e[1]
    else:
      return e[0]

  def cycleVertices(self, vertex2Neighbors):
    """
    @param vertex2Neighbors a map from each vertex
           to its two neighbors in a cycle (as a list)
    @return a list of vertices in the cycle in clockwise order
    """
    start = list(vertex2Neighbors.keys())[0]
    vertexList = [start]
    previous = start
    # choose an arbitrary of previous to get going
    current = vertex2Neighbors[previous][0]
    while current != start:
      vertexList.append(current)
      nextVertex = self.otherEnd(vertex2Neighbors[current], previous)
      previous = current
      current = nextVertex
    return vertexList
    
  def computeBoundaryVertices(self):
    """
    @return the boundary vertices in cyclic order (as a list);
            assume boundary edges have been computed
    """
    # map each boundary vertex to a pair of its neighbors
    vertex2Neighbors = {}
    for edge in self.boundaryEdges:
      v = edge[0]
      w = edge[1]
      if not v in vertex2Neighbors:
        vertex2Neighbors[v] = [w]
      else:
        vertex2Neighbors[v].append(w)
      if not w in vertex2Neighbors:
        vertex2Neighbors[w] = [v]
      else:
        vertex2Neighbors[w].append(v)
    # create a list of vertices on the infinite face in clockwise order
    outerFace = self.cycleVertices(vertex2Neighbors)
    return outerFace
    
  def triangulateInfiniteFace(self):
    """
    adds extra triangles and edges, i.e., extends self.triangles and
    self.triangleEdges so that the boundary is a triangle
    """
    # turn outer face into a queue
    Q = deque()
    for v in self.boundaryVertices:
      Q.append(v)

    # while Q has more than 3 vertices, do
    #   - pop first three vertices: v, w_1, w_2
    #   - if edge vw_2 is already a triangle edge, push(v) and put w_1,w_2 back;
    #     next new triangle edge will start at w_1
    #   - otherwise, add edge vw_2 and triangle [v, w_1, w_2] to the triangulation
    #     and push v, w_2 (w_1 is no longer in Q)
    while len(Q) > 3:
      v = Q.popleft()
      w_1 = Q.popleft()
      w_2 = Q.popleft()
      if (v, w_2) in self.triangleEdges or (w_2,v) in self.triangleEdges:
        # already a triangle involving v and the successor of the successor
        # on the infinite face; do nothing but rotate v to the end of Q
        Q.append(v)
        Q.appendleft(w_2)
        Q.appendleft(w_1)
      else:
        # add a new triangle on the outer face
        new_edge = (v, w_2)
        new_edge = self.sortedEdge(new_edge)
        new_triangle = [v, w_1, w_2]
        new_triangle.sort()
        self.triangleEdges.add(new_edge)
        self.triangles.append(new_triangle)
        new_triangle_index = len(self.triangles) - 1
        self.edge2Triangles[new_edge] = [new_triangle_index]
        first_other_edge = self.sortedEdge((v, w_1))
        second_other_edge = self.sortedEdge((w_1, w_2))
        self.edge2Triangles[first_other_edge].append(new_triangle_index)
        self.edge2Triangles[second_other_edge].append(new_triangle_index)
        
        # v and w_2 are still on outer face, rotate them to the end of Q
        Q.append(v)
        Q.append(w_2)
    # now account for remaining outer triangle
    outer_triangle = list(Q)
    self.triangles.append(outer_triangle)
    outer_triangle_index = len(self.triangles) - 1
    # traverse edges of outer triangle
    for index in range(3):
      edge = self.sortedEdge((outer_triangle[index],
                              outer_triangle[(index + 1) % 3]))
      self.edge2Triangles[edge].append(outer_triangle_index)
    self.boundaryEdges = None
    self.boundaryVertices = None

  def computeDual(self):
    """computes the dual and modifies the list of edges and points accordingly;
    the list of triangles is no longer relevant, and, if the infinite face
    has been triangulated, the points may not make sense - they are centroids
    of the triangles
    """
    # each dual point is the centroid of its face
    self.dualPoints = []
    for triangle in self.triangles:
      avgX = (self.sorted_points[triangle[0]][0]
              + self.sorted_points[triangle[1]][0]
              + self.sorted_points[triangle[2]][0]) / 3
      avgY = (self.sorted_points[triangle[0]][1]
              + self.sorted_points[triangle[1]][1]
              + self.sorted_points[triangle[2]][1]) / 3
      self.dualPoints.append(array([avgX, avgY]))
    if self.boundaryVertices:
      # non-triangular outer face; just take centroid of all points
      xCoords = [pt[0] for pt in self.sorted_points]
      yCoords = [pt[1] for pt in self.sorted_points]
      avgX = sum(xCoords) / len(xCoords)
      avgY = sum(yCoords) / len(yCoords)
      self.dualPoints.append(array([avgX, avgY]))
      # now add infinite face to map of boundary edges to triangles
      infinite_face_index = len(self.dualPoints) - 1
    self.dualEdges = set()
    for edge in self.getEdges():
      triangles = self.edge2Triangles[edge]
      if len(triangles) == 2:
        # normal case, connect the dual points
        dual_edge = self.sortedEdge(tuple(triangles))
      else:
        # otherwise, one side of edge is the infinite face
        dual_edge = (triangles[0], infinite_face_index)
      self.dualEdges.add(dual_edge)
        
if __name__ == '__main__':
  sys.stderr.write("Use random_delaunay.py instead if you want to create a random\n"
                   + " triangulation from scratch\n"
                   + " Otherwise input a list of points.")
  stream = sys.stdin
  points = []
  line = stream.readline()
  while ( line ):
    split_line = line.split()
    point = array([float(split_line[0]), float(split_line[1])])
    points.append(point)
    line = stream.readline()
    delaunay = Delaunay2d(points)
    print("points:   ", delaunay.getPoints())
    print("triangles:", delaunay.getTriangles())
    print("edges:    ", delaunay.getEdges())
    print("-- boundary")
    print("edges:    ", delaunay.getBoundaryEdges())
    print("vertices: ", delaunay.getBoundaryVertices())
    delaunay.computeDual()
    delaunay.triangulateInfiniteFace()
    print("-------- triangulate infinite face")
    print("boundary", delaunay.getBoundaryEdges(), delaunay.getBoundaryVertices())
    print("triangles:", delaunay.getTriangles())
    print("edges:    ", delaunay.getEdges())
    delaunay.computeDual()

#  [Last modified: 2019 09 17 at 21:48:21 GMT]
