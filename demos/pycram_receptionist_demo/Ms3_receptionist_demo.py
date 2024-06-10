import rospy

from pycram.designators.action_designator import *
from demos.pycram_receptionist_demo.utils.new_misc import *
from pycram.enums import ObjectType
from pycram.process_module import real_robot
import pycram.external_interfaces.giskard as giskardpy
from pycram.ros.robot_state_updater import RobotStateUpdater
from pycram.ros.viz_marker_publisher import VizMarkerPublisher
from pycram.designators.location_designator import *
from pycram.designators.object_designator import *
from pycram.bullet_world import BulletWorld, Object
from std_msgs.msg import String, Bool

world = BulletWorld("DIRECT")
#v = VizMarkerPublisher()

robot = Object("hsrb", "robot", "../../resources/" + robot_description.name + ".urdf")
robot_desig = ObjectDesignatorDescription(names=["hsrb"]).resolve()
robot.set_color([0.5, 0.5, 0.9, 1])

kitchen = Object("kitchen", ObjectType.ENVIRONMENT, "suturo_lab_version_15.urdf")
giskardpy.init_giskard_interface()
#RobotStateUpdater("/tf", "/giskard_joint_states")
kitchen_desig = ObjectDesignatorDescription(names=["kitchen"])


# giskardpy.sync_worlds()

# variables for communcation with nlp
pub_nlp = rospy.Publisher('/startListener', String, queue_size=10)
response = ""
callback = False
doorbell = False

# Declare variables for humans
host = HumanDescription("Lucas", fav_drink="water")
guest1 = HumanDescription("guest", fav_drink="tea")
guest2 = HumanDescription("guest2")
seat_number = 2


def data_cb(data):
    global response
    global callback
    global doorbell

    response = data.data.split(",")
    response.append("None")
    callback = True


def doorbell_cb(data):
    global doorbell
    doorbell = True



with real_robot:

    # signal start
    TalkingMotion("waiting for guests").resolve().perform()

    # receive data from nlp via topic
    rospy.Subscriber("nlp_out", String, data_cb)
    rospy.Subscriber("nlp_out2", String, doorbell_cb)

    while not doorbell:
        print("no bell")

    # Pre-Pose for door opening
    ParkArmsAction([Arms.LEFT]).resolve().perform()
    pose1 = Pose([1.45, 4.5, 0], [0, 0, 1, 0])
    NavigateAction([pose1]).resolve().perform()
    MoveJointsMotion(["wrist_roll_joint"], [-1.57]).resolve().perform()
    MoveTorsoAction([0.35]).resolve().perform()
    MoveGripperMotion(motion="open", gripper="left").resolve().perform()

    # grasp door
    giskardpy.grasp_doorhandle("iai_kitchen/living_room:arena:door_handle_inside")
    MoveGripperMotion(motion="close", gripper="left").resolve().perform()

    # open door
    giskardpy.open_doorhandle("kitchen_2/living_room:arena:door_handle_inside")
    MoveGripperMotion(motion="open", gripper="left").resolve().perform()

    # # move away from door
    pose2 = Pose([1.85, 4.5, 0], [0, 0, 1, 0])
    NavigateAction([pose2]).resolve().perform()

    TalkingMotion("Welcome, please step in front of me").resolve().perform()
    ParkArmsAction([Arms.LEFT]).resolve().perform()

    # look for human
    DetectAction(technique='human').resolve().perform()

    # look at guest and introduce
    HeadFollowAction('start').resolve().perform()
    TalkingMotion("Hello, i am Toya and my favorite drink is oil. What about you, talk to me?").resolve().perform()
    rospy.sleep(3)

    # signal to start listening
    pub_nlp.publish("start listening")

    # wait for nlp answer
    while not callback:
        rospy.sleep(1)
    callback = False

    if response[0] == "<GUEST>":
        # success a name and intent was understood
        if response[1] != "<None>":
            TalkingMotion("please confirm if i got your name right").resolve().perform()
            guest1.set_drink(response[2])
            rospy.sleep(1)
            guest1.set_name(name_confirm(response[1]))

        else:
            # save heard drink
            if response[2]:
                guest1.set_drink(response[2])

            # ask for name again once
            guest1.set_name(name_repeat())

        # confirm favorite drink
        guest1.set_drink(drink_confirm(guest1.fav_drink))

    else:
        # two chances to get name and drink
        i = 0
        while i < 2:
            TalkingMotion("please repeat your name and drink loud and clear").resolve().perform()
            pub_nlp.publish("start")

            while not callback:
                rospy.sleep(1)
            callback = False

            if response[0] == "<GUEST>":
                guest1.set_name(response[1])
                guest1.set_drink(response[2])
                break
            else:
                i += 1

    TalkingMotion("i will show you the living room now").resolve().perform()

    # get attributes
    attr_list = DetectAction(technique='attributes', state='start').resolve().perform()
    guest1.set_attributes(attr_list)
    rospy.loginfo(attr_list)

    TalkingMotion("please step out of the way and follow me").resolve().perform()

    # stop looking at human
    HeadFollowAction('stop').resolve().perform()
    DetectAction(technique='human', state='stop').resolve().perform()

    # lead human to living room
    NavigateAction([door_to_couch]).resolve().perform()
    MoveGripperMotion(motion="close", gripper="left").resolve().perform()

    # place new guest in livingroom
    TalkingMotion("Welcome to the living room").resolve().perform()

    # detect host
    host_pose = DetectAction(technique='human').resolve().perform()
    host.set_pose(host_pose[1])
    host_pose = DetectAction(technique='human', state='stop').resolve().perform()

    # detect free seat
    seat = DetectAction(technique='location', state="sofa").resolve().perform()
    for place in seat[1]:
        if place[0] == 'False':
            PointingMotion(float(place[1]), float(place[2]), float(place[3])).resolve().perform()
            pose_guest1 = PoseStamped()
            pose_guest1.header.frame_id = "/map"
            pose_guest1.pose.position.x = float(place[1])
            pose_guest1.pose.position.y = float(place[2])
            pose_guest1.pose.position.z = float(place[3])
            guest1.set_pose(pose_guest1)
            break

    HeadFollowAction('start').resolve().perform()
    rospy.sleep(1.2)
    pub_pose.publish(guest1.pose)
    TalkingMotion("please take a seat next to your host").resolve().perform()
    rospy.sleep(3)

    # introduce humans and look at them
    introduce(host, guest1)
    rospy.sleep(2)

    # describe guest
    describe(guest1)
    HeadFollowAction('stop').resolve().perform()

    TalkingMotion("end").resolve().perform()

