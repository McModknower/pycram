import rospy

from demos.pycram_gpsr_demo import track_human, nlp_listening
from demos.pycram_gpsr_demo.setup_demo import *
import demos.pycram_gpsr_demo.utils as utils
import demos.pycram_gpsr_demo.nlp_processing as nlp
from stringcase import snakecase


# --- main control ---
# TODO: test on real robot
def gpsr():
    global todo_plans
    todo_plans = []
    # plan_list = utils.get_plans(high_level_plans) # get list of all available plans
    # init params
    # go to instruction point, look at human, etc.
    # high_level_plans.prepare_for_commands()

    # listen to instructions
    instruction_list = nlp.listen_to_commands()
    rospy.logwarn("[CRAM] instruction list: " + str(instruction_list))

    # TODO iterate over list of instructions and do stuff
    for instruction in instruction_list:
        rospy.logwarn("[CRAM] in instruction loop")
        rospy.loginfo(instruction)
        # do stuff
        # match instruction to plan
        utils.call_plan_by_name(plan_list, snakecase(instruction['intent']), instruction)

    # execute instructions

