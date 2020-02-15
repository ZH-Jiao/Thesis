"""
Interface of ResultRepository
"""

__author__ = "ZhihengJiao"
__version__ = "2019.12.10"

import rhinoscriptsyntax as rs
import copy
from Rhino.Geometry import Point3d
from abc import abstractmethod, ABCMeta, ABC


def overrides(interface_class):
    def overrider(method):
        assert (method.__name__ in dir(interface_class))
        return method

    return overrider


class SolverResult:
    """

    """

    def __init__(self, result, metric, metricClass=None):
        """
        :param result: The representation of a result, vary by Solvers
        :param metric: The Number for sorting results. E.g. nums of parking stall
        """
        # some metrics and some format of result
        self.result = result
        self.metric = metric
        # String representation of metric class it use.(Name of the metric)
        self.metricClass = metricClass

    def getMetric(self):
        return self.metric

    def getResult(self):
        return self.result

    def __repr__(self):
        return str(self.metricClass) + str(" : ") + str(self.metric) + str(self.result)
