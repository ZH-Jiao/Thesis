"""Provides a scripting component.
    Inputs:
        verticesOfSite: The list of endPoints of the surface
        edgesOfSite: The boundary of the site surface (limit to 4 sides)
        surfaceOfSite: The surface of the site
    Output:
        a: The a output variable"""

__author__ = "j9366"
__version__ = "2019.12.10"

import rhinoscriptsyntax as rs
import copy

"""
Class for Carpark
"""
class CarPark:
    width = 5.3

    def __init__(self, lineID=None, line=None):
        self.connectedToRoad = False
        self.next = None
        self.prev = None
        self.line = line
        self.lineID = lineID


    def getWidth(self):
        return self.width

    def getLineLength(self):
        return rs.CurveLength(self.line)

    def setConnection(self, connected):
        self.connectedToRoad = connected

    def isConnected(self):
        return self.connectedToRoad

"""
Class for Road
"""
class Road:
    width = 7

    def __init__(self, lineID=None, line=None):
        self.next = None
        self.prev = None
        self.line = line

    def getLineLength(self):
        return rs.CurveLength(self.line)

    def getWidth(self):
        return self.width



# class for calculating the best layout
class ParkingSolver:
    """
    Row arrangement solver
    """

    def __init__(self, vertices, edges, surface):

        self.size = 0
        self.carParkNum = 0

        # vertices
        self.vertices = vertices

        # Result from solve()
        self.result = []

        # Boundary of the site (4 edges in this version)
        self.edges = edges

        # Surface of the site
        self.surface = surface

        # Center point of the site surface
        self.center = rs.SurfaceAreaCentroid(surface)[0]

        # List of unit vectors that pointing from self.edges for offset
        self.offsetDirection = []

        # List of max offset length as a bound
        self.maxOffsetLength = self.getMaxOffsetLength()

        # self.siteWidth = siteWidth
        self.edgeDirection()


    def solve(self, edgeID, edge):
        """
        DFS
        Call this function to get all possible result of Car and Road Row placement.
        :return: a List of result [number of park, sum of car park width, "C", "R", "C", ...]
        """
        c = CarPark(edgeID, edge)
        r = Road(edgeID, edge)
        cWidth = CarPark.width
        rWidth = Road.width
        branchC = [0, 0]
        branchR = [0, 0]


        startC = self.growNode(None, c, branchC)
        startR = self.growNode(None, r, branchR)

        self.grow(startC, branchC, edgeID)
        self.grow(startR, branchR, edgeID)
        return self.result


    def growNode(self, node, newNode, branch):
        """
        Make the newNode grow on (old)node
        :rtype: newNode(the next node)
        """
        print(node)
        if node is not None:

            # if isinstance(node, CarPark) and isinstance(newNode, Road):
            #     print(node)
            #     print(newNode)
            #     node.connectedToRoad = True
            if isinstance(node, Road) and isinstance(newNode, CarPark):
                newNode.connectedToRoad = True

        newNode.prev = node

        if isinstance(newNode, CarPark):
            branch[1] += CarPark.width
            # Matric: the total row length of car parking
            if node is not None:
                branch[0] += node.getLineLength()
            branch.append(newNode)
        elif isinstance(newNode, Road):
            branch[1] += Road.width
            branch.append(newNode)

        return newNode

    def grow(self, node, branch, edgeID):
        """
        DFS for the parking algorithm. Each node represent a row of "C"carparking of "R"road.
        branch is a list of lists of "C" and "R" composition. Such as [number of park, sum of car and road width, "C", "R", "C", ...]
        :rtype: object
        """
        # base case
        # stop when current composition have one more "C" or "R"
        print("node",node)
        print("branch", branch)
        print("edgeID",edgeID)
        if branch[1] > self.maxOffsetLength[edgeID] - CarPark.width:
            if isinstance(node, CarPark) and isinstance(node.prev, CarPark):
                return

            self.result.append(branch)
            return

        # if this node is a "C" car park
        if isinstance(node, CarPark):
            if not node.isConnected():
                print("nodeline", rs.CurveLength(node.line))
                r = Road(edgeID, self.offsetRow(node.line, self.offsetDirection[edgeID], Road.width))
                print("r", r.line)
                newBranch = copy.deepcopy(branch)
                newNode = self.growNode(node, r, newBranch)
                self.grow(newNode, newBranch, edgeID)
            else:
                c = CarPark(edgeID, self.offsetRow(node.line, self.offsetDirection[edgeID], CarPark.width))
                r = Road(edgeID, self.offsetRow(node.line, self.offsetDirection[edgeID], Road.width))
                newBranch = copy.deepcopy(branch)
                newNode = self.growNode(node, c, newBranch)
                self.grow(newNode, newBranch, edgeID)

                newBranch = copy.deepcopy(branch)
                newNode = self.growNode(node, r, newBranch)
                self.grow(newNode, newBranch, edgeID)

        # if this node is a "R" road
        elif isinstance(node, Road):
            c = CarPark(edgeID, self.offsetRow(node.line, self.offsetDirection[edgeID], CarPark.width))
            newBranch = copy.deepcopy(branch)
            newNode = self.growNode(node, c, newBranch)
            self.grow(newNode, newBranch, edgeID)

    def getMaxOffsetLength(self):
        """
        Given the boundaries: self.edges, vertices: self.vertices
        get a corresponding list of maximum offset distance(like the width for the site)
        :rtype: List of max offset lengths
        """
        resList = []
        for edge in self.edges:
            maxLength = 0
            for vertex in self.vertices:
                currLength = rs.LineMinDistanceTo(edge, vertex)
                maxLength = max(maxLength, currLength)
            resList.append(maxLength)
        return resList

    def edgeDirection(self):
        """
        Calculate the unit vector of offset directions for self.edges and append in list: self.offsetDirection.
        :rtype: None (result in self.offsetDirection)
        """
        for edge in self.edges:
            # make vertical vector
            curveVector = rs.VectorCreate(rs.CurveStartPoint(edge), rs.CurveEndPoint(edge))
            midPoint = rs.CurveMidPoint(edge)
            vec1 = rs.VectorRotate(curveVector, 90.0, [0,0,1])
            vec2 = rs.VectorRotate(curveVector, -90.0, [0,0,1])
            midToCenterVec = rs.VectorCreate(midPoint, self.center)
            offsetVec = ""
            if (rs.VectorDotProduct(vec1, midToCenterVec) > 0):
                offsetVec = vec1
            else:
                offsetVec = vec2
            offsetVec = rs.VectorUnitize(offsetVec)
            #result
            self.offsetDirection.append(offsetVec)


    def offsetRow(self, edge, vec, width):
        """
        Offset a row depending on the type of width and direction.
        need to use self.edges
        :return:
        """
        print("edge", rs.CurveLength(edge))
        print("vec", vec)
        print("width", width)
        newRow = rs.OffsetCurve(edge, vec, width)
        # Magic number
        print("newRow", newRow)
        print("newRowCurve", rs.CurveLength(newRow))
        rs.ScaleObject(newRow, rs.CurveMidPoint(newRow), [20,20,0])
        print("ScaleNewRowCurve", rs.CurveLength(newRow))
        # Problem Below!!
        param = []
        for e in self.edges:
            intersect = rs.CurveCurveIntersection(newRow, e)
            # Follows the Rhino api
            if intersect is not None:
                param.append(intersect[0][5])
        print("param", param)

        if param[0] <= param[1]:
            newRow = rs.TrimCurve(newRow, [param[0], param[1]])
        else:
            newRow = rs.TrimCurve(newRow, [param[1], param[0]])


        # newRow = rs.TrimCurve(newRow, [param[0], param[1]])
        print("TrimNewRowCurve", rs.CurveLength(newRow))
        return newRow


class Node:

    def __init__(self, data, nextNode):
        self.data = data
        self.next = nextNode


def getPattern(lst):
   lst = lst[2:]
   res = []
   for i in lst:
       toAdd = None
       if i == 'C':
           toAdd = CarPark.width
       else:
           toAdd = Road.width
       res.append(toAdd)
   return res







# CarPark().width = parkingLength
# Road().width = roadWidth

solver = ParkingSolver(verticesOfSite, edgesOfSite, surfaceOfSite)


result = solver.solve(0, solver.edges[0])
order = sorted(result, key=lambda s: s[0], reverse=True)
a = getPattern(order[0])
b = order
print(order)
