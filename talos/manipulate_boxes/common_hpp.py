#/usr/bin/env python
from math import sqrt
from hpp.corbaserver.manipulation.robot import Robot
from hpp.corbaserver.manipulation import ProblemSolver, ConstraintGraph, Rule
from hpp.gepetto.manipulation import ViewerFactory
from datetime import datetime
a = sqrt (2)/2

Robot.packageName = "talos_data"
Robot.urdfName = "talos"
Robot.urdfSuffix = '_full_v2'
Robot.srdfSuffix= ''

class Box (object):
  def __init__ (self, name, vf) :
    self.name = name
    self.handles = [ name + "/" + h for h in self.__class__.handles ]
    self.contacts = [ name + "/" + h for h in self.__class__.contacts ]
    vf.loadObjectModel (self.__class__, name)

  rootJointType = 'freeflyer'
  packageName = 'gerard_bauzil'
  urdfName = 'plank_of_wood1'
  urdfSuffix = ""
  srdfSuffix = ""
  handles = ["handle1", "handle2", "handle3", "handle4"]
  contacts = [ "front_surface", "rear_surface", ]

class Table (object):
  def __init__ (self, name, vf) :
    self.name = name
    self.handles = [ name + "/" + h for h in self.__class__.handles ]
    self.contacts = [ name + "/" + h for h in self.__class__.contacts ]
    vf.loadObjectModel (self.__class__, name)

  rootJointType = 'anchor'
  packageName = 'gerard_bauzil'
  urdfName = 'table_140_70_73'
  urdfSuffix = ""
  srdfSuffix = ""
  pose = "pose"
  handles = []
  contacts = [ "top", ]

Object = Box
half_sitting = [
        # -0.74,0,1.0192720229567027,0,0,0,1, # root_joint
        0.6,-0.65,1.0192720229567027,0,0,sqrt(2)/2,sqrt(2)/2, # root_joint
        0.0, 0.0, -0.411354, 0.859395, -0.448041, -0.001708, # leg_left
        0.0, 0.0, -0.411354, 0.859395, -0.448041, -0.001708, # leg_right
        0, 0.006761, # torso
        0.25847, 0.173046, -0.0002, -0.525366, 0, 0, 0.1, # arm_left
        0, 0, 0, 0, 0, 0, 0, # gripper_left
        -0.25847, -0.173046, 0.0002, -0.525366, 0, 0, 0.1, # arm_right
        0, 0, 0, 0, 0, 0, 0, # gripper_right
        0, 0, # head

        -0.04,0,1.095+0.071,0,0,1,0, # box
        ]

# Load an object of type Type with name name
def loadObject (vf, Type, name) :
    vf.loadObjectModel (Type, name)
    obj = Type (name)
    obj.handles = [ name + "/" + h for h in Type.handles ]
    obj.contacts = [ name + "/" + h for h in Type.contacts ]
    return obj

def makeRobotProblemAndViewerFactory (clients):
    objects = list ()
    robot = Robot ('talos', 'talos', rootJointType = "freeflyer",
                   client = clients)
    robot. leftAnkle = "talos/leg_left_6_joint"
    robot.rightAnkle = "talos/leg_right_6_joint"

    robot.setJointBounds ("talos/root_joint", [-10, 10, -10, 10, 0, 2])

    ps = ProblemSolver (robot)
    ps.setErrorThreshold (1e-3)
    ps.setMaxIterProjection (40)

    ps.addPathOptimizer("SimpleTimeParameterization")

    vf = ViewerFactory (ps)
    objects.append (Object (name = 'box', vf = vf))
    robot.setJointBounds ("box/root_joint", [-10, 10, -10, 10, 0, 2])

    # Loaded as an object to get the visual tags at the right position.
    # vf.loadEnvironmentModel (Table, 'table')
    table = Table (name = 'table', vf = vf)

    return robot, ps, vf, table, objects

def makeGraph (robot, table, objects):
    from hpp.corbaserver.manipulation.constraint_graph_factory import \
      ConstraintGraphFactory
    graph = ConstraintGraph(robot, 'graph')
    factory = ConstraintGraphFactory (graph)
    factory.setGrippers ([ "talos/left_gripper", "talos/right_gripper"])
    factory.setObjects ([ obj.name for obj in objects],
                        [ obj.handles for obj in objects ],
                        [ obj.contacts for obj in objects])
    factory.environmentContacts (table.contacts)
    factory.generate ()
    return graph

def shootConfig (robot, q, i):
  """
  Shoot a random config if i > 0, return input configuration otherwise
  """
  if i==0: return q
  return robot.shootRandomConfig ()

def createConnection (ps, graph, e, q, maxIter):
  """
  Try to build a path along a transition from a given configuration
  """
  for i in range (maxIter):
    q_rand = shootConfig (ps.robot, q, i)
    res, q1, err = graph.generateTargetConfig (e, q, q_rand)
    if not res: continue
    res, p, msg = ps.directPath (q, q1, True)
    if not res: continue
    ps.addConfigToRoadmap (q1)
    ps.addEdgeToRoadmap (q, q1, p, True)
    return p, q1
  return (None, None)

class Solver (object):
  """
  Solver that tries direct connections before calling RRT.
  """
  def __init__ (self, ps, graph, q_init, q_goal, e1, e2, e3, e4, e14, e23):
    self.ps = ps; self.graph = graph
    self.e1 = e1; self.e2 = e2; self.e3 = e3; self.e4 = e4
    self.e14 = e14; self.e23 = e23
    self.q_init = q_init; self.q_goal = q_goal

  def solve (self):
    start = datetime.now ()
    self.ps.addConfigToRoadmap (self.q_init)
    self.ps.addConfigToRoadmap (self.q_goal)

    p1, q1 = createConnection (self.ps, self.graph, self.e1, self.q_init, 1000)
    p2, q2 = createConnection (self.ps, self.graph, self.e2, self.q_init , 1000)
    p3, q3 = createConnection (self.ps, self.graph, self.e3, self.q_goal, 1000)
    p4, q4 = createConnection (self.ps, self.graph, self.e4, self.q_goal, 1000)
    if q1:
      p14, q14 = createConnection (self.ps, self.graph, self.e14, q1, 1000)
    if q2:
      p23, q23 = createConnection (self.ps, self.graph, self.e23, q2, 1000)
    self.ps.setInitialConfig (self.q_init)
    self.ps.addGoalConfig (self.q_goal)
    self.ps.solve ()
    end = datetime.now ()
    print ("Resolution time : {0}". format (end - start))
