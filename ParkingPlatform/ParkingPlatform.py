"""
All Code for Parking Platform
Working on: 603 line

### Table of Content
# Solver
# RowSolverResult

"""

__author__ = "ZhihengJiao"
__version__ = "2019.12.10"

import rhinoscriptsyntax as rs
import copy
from Rhino.Geometry import Point3d
from abc import abstractmethod, ABCMeta, ABC
import math


def overrides(interface_class):
    def overrider(method):
        assert (method.__name__ in dir(interface_class))
        return method

    return overrider


def interface(interface_class):
    pass


########################################################################################################################
# CarStallMeta
########################################################################################################################
@interface
class CarStallMeta:
    """
    Road
    #####
    #   #
    #   #
    #   #
    #####
    Road
    # Vertical direction is width in Row
    # Horizontal direction is length in Row
    """
    width = 2.7
    length = 5.3
    geometry = None
    # Number of RoadRow that required to connected to this stall type
    requiredConnection = 1
    stallCount = 1

    def __init__(self, geometry=None):
        self.geometry = geometry


class NinetyDegCarStall(CarStallMeta):
    degree = math.pi
    width = CarStallMeta.length
    length = CarStallMeta.width


class SixtyDegCarStall(CarStallMeta):
    degree = math.pi * 2 / 3
    width = math.cos(degree) * CarStallMeta.width + math.sin(degree) * CarStallMeta.length
    length = math.cos(degree) * CarStallMeta.width


# Double
class SixtyDegCarStallDouble(CarStallMeta):
    requiredConnection = 2
    stallCount = 2
    degree = SixtyDegCarStall.degree
    width = math.cos(degree) * CarStallMeta.width + math.sin(degree) * CarStallMeta.length * 2
    length = SixtyDegCarStall.length


class FortyFiveDegCarStall(CarStallMeta):
    degree = math.pi / 2
    width = math.cos(degree) * CarStallMeta.width + math.sin(degree) * CarStallMeta.length
    length = math.cos(degree) * CarStallMeta.width


# Double
class FortyFiveDegCarStallDouble(CarStallMeta):
    requiredConnection = 2
    stallCount = 2
    degree = math.pi * 2 / 3
    width = math.cos(degree) * CarStallMeta.width + math.sin(degree) * CarStallMeta.length * 2
    length = math.cos(degree) * CarStallMeta.width


class ThirtyDegCarStall(CarStallMeta):
    degree = math.pi / 3
    width = math.cos(degree) * CarStallMeta.width + math.sin(degree) * CarStallMeta.length
    length = math.cos(degree) * CarStallMeta.width


# Double
class ThirtyDegCarStallDouble(CarStallMeta):
    requiredConnection = 2
    stallCount = 2
    degree = math.pi / 3
    width = math.cos(degree) * CarStallMeta.width + math.sin(degree) * CarStallMeta.length
    length = math.cos(degree) * CarStallMeta.width


class ZeroDegCarStall(CarStallMeta):
    degree = 0


class CarStallTypes:
    """
    The wrapper class of all carStallTypes
    """
    carStallTypeList = [NinetyDegCarStall, SixtyDegCarStall, SixtyDegCarStallDouble, FortyFiveDegCarStall,
                        FortyFiveDegCarStall, ThirtyDegCarStall, ThirtyDegCarStall, ZeroDegCarStall]


########################################################################################################################
# RoadRowMeta
########################################################################################################################
@interface
class RoadRowMeta:
    pass


class NormalRoadRow(RoadRowMeta):
    width = 7
    geometry = None

    def __init__(self, geometry=None):
        self.geometry = geometry


########################################################################################################################
# RowNode
########################################################################################################################
@interface
class RowNode:

    def __init__(self, baseLineID=None, referenceLine=None, metaItem=None):
        self.next: RowNode = None
        self.prev: RowNode = None
        self.metaItem = metaItem
        self.referenceLine = referenceLine
        self.baseLineID = baseLineID

    def getWidth(self):
        return self.metaItem.width

    def getBaseLineID(self):
        return self.baseLineID

    def getReferenceLine(self):
        return self.referenceLine;

    def getLineLength(self):
        return rs.CurveLength(self.referenceLine)

    @abstractmethod
    def __repr__(self):
        return "TBD"


class CarStallRow(RowNode):
    """
    "CarStallRow"
    """

    @overrides
    def __init__(self, baseLineID: int = None, referenceLine: object = None, carStallMeta: CarStallMeta = NinetyDegCarStall):
        super().__init__(baseLineID, referenceLine, carStallMeta)
        self.connectedToRoadRow = 0
        self.requiredConnection = carStallMeta.requiredConnection

    @overrides
    def __repr__(self):
        return "CarCarStallRow"

    def addConnection(self):
        self.requiredConnection -= 1

    def isConnectedToRoadRow(self):
        return self.requiredConnection <= 0


class RoadRowRow(RowNode):

    @overrides
    def __init__(self, baseLineID=None, referenceLine=None, RoadRowMeta=NinetyDegCarStall):
        super().__init__(baseLineID, referenceLine, RoadRowMeta)

    @overrides
    def __repr__(self):
        return "RoadRowRow"


########################################################################################################################
# Zone
########################################################################################################################
@interface
class Zone:
    def __init__(self, vertices, edges, surface):
        # vertices
        self.vertices = vertices

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

        self.appendEdgeDirection()

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

    def appendEdgeDirection(self):
        """
        Calculate the unit vector of offset directions for self.edges and append in list: self.offsetDirection.
        :rtype: None (result in self.offsetDirection)
        """
        for edge in self.edges:
            # make vertical vector
            curveVector = rs.VectorCreate(rs.CurveStartPoint(edge), rs.CurveEndPoint(edge))
            midPoint = rs.CurveMidPoint(edge)
            vec1 = rs.VectorRotate(curveVector, 90.0, [0, 0, 1])
            vec2 = rs.VectorRotate(curveVector, -90.0, [0, 0, 1])
            midToCenterVec = rs.VectorCreate(midPoint, self.center)
            offsetVec = ""
            if rs.VectorDotProduct(vec1, midToCenterVec) > 0:
                offsetVec = vec1
            else:
                offsetVec = vec2
            offsetVec = rs.VectorUnitize(offsetVec)
            # result
            self.offsetDirection.append(offsetVec)


########################################################################################################################
# Metric
########################################################################################################################
@interface
class Metric:
    def __init__(self, metricNumber):
        self.metricNumber = metricNumber

    def getMetricNumber(self):
        return self.metricNumber

    def calculate(self):
        pass


class StallCountMetric(Metric):
    @overrides
    def __init__(self, metricNumber):
        super().__init__()

    @overrides
    def calculate(self):
        pass


########################################################################################################################
# RowSolverResult
########################################################################################################################
class RowSolverResult:
    """

    """

    def __init__(self, result=[], metricClassInstance: Metric = None):
        """
        :param result: The representation of a result, vary by Solvers
        :param metric: The Number for sorting results. E.g. nums of parking stall
        """
        # some metrics and some format of result
        self.result = result
        # String representation of metric class it use.(Name of the metric)
        self.metricClassInstance = metricClassInstance

        self.totalWidth = 0;

    def getMetricNum(self):
        return self.metricClassInstance.metricNumber

    def getResult(self):
        return self.result

    def getTotalWidth(self):
        return self.totalWidth

    def addRow(self, rowNode: RowNode):
        self.result.append(rowNode)
        self.totalWidth += rowNode.getWidth()

    def __repr__(self):
        return str(self.metricClass) + str(" : ") + str(self.metric) + str(self.result)


########################################################################################################################
# Solver
########################################################################################################################
@interface
class Solver:
    """
    Interface of Solver
    """

    def __init__(self, metric):
        self.resultRepository = []  # some metrics and some format of result
        self.metric = metric

    def solve(self, solvers=None):
        """
        Input a list of Solver, and get all possible result from those solvers, and get
        a Result list.
        :param solvers: Solver[]
        """
        for sol in solvers:
            sol.solve()
        return self.resultRepository

    def sortResultByMetrics(self):
        return "sorted resultRepository"

    def setMetric(self, metric):
        self.metric = metric


class ParkingStallSolver(Solver):
    """
    Implementation of Solver
    """

    def __init__(self, metric, zone=None, childSolvers=None):
        super().__init__(metric)
        # site is an instance of Zone class
        self.zone = zone
        self.childSolvers = childSolvers

    @overrides(Solver.solve)
    def solve(self):
        for sol in self.childSolvers:
            sol.solve()
        solveSelf()

    @overrides(Solver.sortResultByMetrics)
    def sortResultByMetrics(self):
        self.metric


    def solveSelf(self):
        """
        DFS
        Call this function to get all possible result of Car and RoadRow Row placement.
        :return: a List of result [number of park, sum of car park width, "C", "R", "C", ...]
        """
        for baseLineID in range(len(self.zone.edges)):
            dfs(self, self.zone.edges[baseLineID])

    def dfs(self, baseLineID):

        c = CarStallRow(baseLineID=baseLineID, referenceLine=self.zone.edges[baseLineID])
        r = RoadRowRow(baseLineID=baseLineID, referenceLine=self.zone.edges[baseLineID])

        branchC = RowSolverResult([], metricClassInstance=StallCountMetric(0))
        branchR = RowSolverResult([], metricClassInstance=StallCountMetric(0))

        startC = self.growNode(None, c, branchC)
        startR = self.growNode(None, r, branchR)

        self.grow(startC, branchC, baseLineID)
        self.grow(startR, branchR, baseLineID)
        return self.resultRepository

    def growNode(self, node, newNode, branch):
        """
        Make the newNode grow on (old)node
        :rtype: newNode(the next node)
        """
        # print(node)
        if node is not None:

            # if isinstance(node, CarStallRow) and isinstance(newNode, RoadRow):
            #     print(node)
            #     print(newNode)
            #     node.connectedToRoadRow = True
            if isinstance(node, RoadRow) and isinstance(newNode, CarStallRow):
                newNode.connectedToRoadRow = True

        newNode.prev = node

        if isinstance(newNode, CarStallRow):
            branch[1] += CarStallRow.width
            # Matric: the total row length of car parking
            if node is not None:
                branch[0] += node.getLineLength()
            branch.append(newNode)
        elif isinstance(newNode, RoadRow):
            branch[1] += RoadRow.width
            branch.append(newNode)

        return newNode

    def grow(self, node: RowNode, branch: RowSolverResult, baseLineID: int):
        """
        DFS for the parking algorithm. Each node represent a row of "C"carparking of "R"road.
        branch is a list of lists of "C" and "R" composition. Such as [number of park, sum of car and road width, "C", "R", "C", ...]
        :rtype: object
        """

        # For loop for different options of Row type
        # Iterate through all type of CarStall degree
        for carStallType in CarStallTypes.carStallTypeList:

            # base case
            # stop when current composition have one more "C" or "R"
            # print("node",node)
            # print("branch", branch)
            # print("baseLineID",baseLineID)
            if branch.getTotalWidth() >= self.zone.maxOffsetLength[baseLineID]:
                # Stall row
                # if there are two car row in the end, means lack 1 connection
                if isinstance(node, CarStallRow) and not node.prev.isConnectedToRoadRow():
                    return

                self.resultRepository.append(branch)
                return

            if node.line is None:
                self.resultRepository.append(branch)
                return

            # if this node is a "C" car park
            if isinstance(node, CarStallRow):
                if not node.isConnected():
                    # print("nodeline", rs.CurveLength(node.line))
                    r = RoadRow(baseLineID=baseLineID, self.offsetRow(node.line, self.offsetDirection[baseLineID], RoadRow.width))
                    # print("r", r.line)
                    newBranch = copy.deepcopy(branch)
                    newNode = self.growNode(node, r, newBranch)
                    self.grow(newNode, newBranch, baseLineID)
                else:
                    c = CarStallRow(baseLineID, self.offsetRow(node.line, self.offsetDirection[baseLineID], CarStallRow.width))
                    r = RoadRow(baseLineID, self.offsetRow(node.line, self.offsetDirection[baseLineID], RoadRow.width))
                    newBranch = copy.deepcopy(branch)
                    newNode = self.growNode(node, c, newBranch)
                    self.grow(newNode, newBranch, baseLineID)

                    newBranch = copy.deepcopy(branch)
                    newNode = self.growNode(node, r, newBranch)
                    self.grow(newNode, newBranch, baseLineID)

            # if this node is a "R" road
            elif isinstance(node, RoadRow):
                c = CarStallRow(baseLineID, self.offsetRow(node.line, self.offsetDirection[baseLineID], CarStallRow.width))
                newBranch = copy.deepcopy(branch)
                newNode = self.growNode(node, c, newBranch)
                self.grow(newNode, newBranch, baseLineID)

    def withInput(self, vertices, edges, surface):
        # vertices
        # Boundary of the site (4 edges in this version)
        pass


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

    def solve(self, baseLineID, edge):
        """
        DFS
        Call this function to get all possible result of Car and RoadRow Row placement.
        :return: a List of result [number of park, sum of car park width, "C", "R", "C", ...]
        """
        c = CarStallRow(baseLineID, edge)
        r = RoadRow(baseLineID, edge)
        cWidth = CarStallRow.width
        rWidth = RoadRow.width
        branchC = [0, 0]
        branchR = [0, 0]

        startC = self.growNode(None, c, branchC)
        startR = self.growNode(None, r, branchR)

        self.grow(startC, branchC, baseLineID)
        self.grow(startR, branchR, baseLineID)
        return self.result

    def growNode(self, node, newNode, branch):
        """
        Make the newNode grow on (old)node
        :rtype: newNode(the next node)
        """
        # print(node)
        if node is not None:

            # if isinstance(node, CarStallRow) and isinstance(newNode, RoadRow):
            #     print(node)
            #     print(newNode)
            #     node.connectedToRoadRow = True
            if isinstance(node, RoadRow) and isinstance(newNode, CarStallRow):
                newNode.connectedToRoadRow = True

        newNode.prev = node

        if isinstance(newNode, CarStallRow):
            branch[1] += CarStallRow.width
            # Matric: the total row length of car parking
            if node is not None:
                branch[0] += node.getLineLength()
            branch.append(newNode)
        elif isinstance(newNode, RoadRow):
            branch[1] += RoadRow.width
            branch.append(newNode)

        return newNode

    def grow(self, node, branch: , baseLineID):
        """
        DFS for the parking algorithm. Each node represent a row of "C"carparking of "R"road.
        branch is a list of lists of "C" and "R" composition. Such as [number of park, sum of car and road width, "C", "R", "C", ...]
        :rtype: object
        """
        # base case
        # stop when current composition have one more "C" or "R"
        # print("node",node)
        # print("branch", branch)
        # print("baseLineID",baseLineID)
        if branch > self.maxOffsetLength[baseLineID] - CarStallRow.width:
            if isinstance(node, CarStallRow) and isinstance(node.prev, CarStallRow):
                return

            self.result.append(branch)
            return

        if node.referenceLine is None:
            self.result.append(branch)
            return

        # if this node is a "C" car park
        if isinstance(node, CarStallRow):
            if not node.isConnectedToRoadRow():
                # print("nodereferenceLine", rs.CurveLength(node.referenceLine))
                r = RoadRow(baseLineID, self.offsetRow(node.referenceLine, self.offsetDirection[baseLineID], RoadRow.width))
                # print("r", r.referenceLine)
                newBranch = copy.deepcopy(branch)
                newNode = self.growNode(node, r, newBranch)
                self.grow(newNode, newBranch, baseLineID)
            else:
                c = CarStallRow(baseLineID, self.offsetRow(node.referenceLine, self.offsetDirection[baseLineID], CarStallRow.width))
                r = RoadRow(baseLineID, self.offsetRow(node.referenceLine, self.offsetDirection[baseLineID], RoadRow.width))
                newBranch = copy.deepcopy(branch)
                newNode = self.growNode(node, c, newBranch)
                self.grow(newNode, newBranch, baseLineID)

                newBranch = copy.deepcopy(branch)
                newNode = self.growNode(node, r, newBranch)
                self.grow(newNode, newBranch, baseLineID)

        # if this node is a "R" road
        elif isinstance(node, RoadRow):
            c = CarStallRow(baseLineID, self.offsetRow(node.referenceLine, self.offsetDirection[baseLineID], CarStallRow.width))
            newBranch = copy.deepcopy(branch)
            newNode = self.growNode(node, c, newBranch)
            self.grow(newNode, newBranch, baseLineID)

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
            vec1 = rs.VectorRotate(curveVector, 90.0, [0, 0, 1])
            vec2 = rs.VectorRotate(curveVector, -90.0, [0, 0, 1])
            midToCenterVec = rs.VectorCreate(midPoint, self.center)
            offsetVec = ""
            if (rs.VectorDotProduct(vec1, midToCenterVec) > 0):
                offsetVec = vec1
            else:
                offsetVec = vec2
            offsetVec = rs.VectorUnitize(offsetVec)
            # result
            self.offsetDirection.append(offsetVec)

    def offsetRow(self, edge, vec, width):
        """
        Offset a row depending on the type of width and direction.
        need to use self.edges
        :return:
        """
        # print("edge", rs.CurveLength(edge))
        # print("vec", vec)
        # print("width", width)
        newRow = rs.OffsetCurve(edge, vec, width)
        # Magic number
        # print("newRow", newRow)
        # print("newRowCurve", rs.CurveLength(newRow))
        rs.ScaleObject(newRow, rs.CurveMidPoint(newRow), [20, 20, 0])
        # print("ScaleNewRowCurve", rs.CurveLength(newRow))
        # Problem Below!!
        param = []
        for e in self.edges:
            intersect = rs.CurveCurveIntersection(newRow, e)
            # Follows the Rhino api
            if intersect is not None:
                param.append(intersect[0][5])
        # print("param", param)

        if param[0] < param[1]:
            newRow = rs.TrimCurve(newRow, [param[0], param[1]])
        elif param[0] > param[1]:
            newRow = rs.TrimCurve(newRow, [param[1], param[0]])

        else:
            # only one intersection, it's time to stop
            newRow = None

        # newRow = rs.TrimCurve(newRow, [param[0], param[1]])
        # print("TrimNewRowCurve", rs.CurveLength(newRow))
        return newRow


def getPattern(lst):
    lst = lst[2:]
    res = []
    for i in lst:
        toAdd = None
        if i == 'C':
            toAdd = CarStallRow.width
        else:
            toAdd = RoadRow.width
        res.append(toAdd)
    return res

########################################################################################################################
# RowSolverResult
########################################################################################################################
