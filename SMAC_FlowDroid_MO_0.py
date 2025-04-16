"""
Aim: search for optimal configuration of cgalgo to minimize
    the difference between found-leaks and expected-leaks
    (this is the target function in train function)
cgalgo: Callgraph algorithm to use
    (AUTO, CHA, VTA, RTA, SPARK, GEOM)
use APK-file of DroidBench:
/Users/ljubarah/DroidBench-develop/apk/InterComponentCommunication/PublicAPIField1.apk
contains one leak with:
<android.util.Log: int i(java.lang.String,java.lang.String)> -> _SINK_
<android.telephony.TelephonyManager: java.lang.String getDeviceId()> -> _SOURCE_

this file is based on the example of the SMAC3-website:
https://automl.github.io/SMAC3/v2.3.0/examples/1%20Basics/1_quadratic_function/
"""
from distributed.diagnostics.task_stream import prefix

"""
Configuration is a class of package ConfigSpace and contains only one configuration
ConfigurationSpace is also a class and contains multiple configurations, 
i.e. configurations can be sampled from the ConfigurationSpace
Categorical creates a CategoricalHyperparameter
"""
import re
from ConfigSpace import Configuration, ConfigurationSpace, Categorical
import statistics
import time
from smac.multi_objective.parego import ParEGO

# from matplotlib import pyplot as plt
# from smac.facade.algorithm_configuration_facade import AlgorithmConfigurationFacade as ACFacade
from smac.facade.hyperparameter_optimization_facade import \
    HyperparameterOptimizationFacade as HPOFacade  # todo: change smac.facade?

"""
RunHistory: contains information of evaluated/running trials and calculates the cost
(SMAC automatically generates an output file -> have a look into that)
Scenario: contains variables of the environment: configuration space, number of trials, time limit etc.
"""
from smac import Scenario  # ,RunHistory

"""os to execute FlowDroid from this python-script"""
import os


class FlowDroid_configuration_SMAC:
    """
    Callgraph algorithm to use
    (AUTO, CHA, VTA, RTA, SPARK, GEOM)
    """

    @property
    def configspace(self) -> ConfigurationSpace:

        """
        ConfigurationSpace with seed=0 is created
        and search space of cgalgo is the set ("AUTO", "CHA", "VTA", "RTA", "SPARK", "GEOM")
        default of cgalgo is CHA
        so the ConfigurationSpace contains the option cgalgo and the possible values of cgalgo
        at the end the aim of SMAC is to find the best option for cgalgo (of course depending on the target/train function)
        here to minimize the false positives/false negatives i.e. the false leaks

        returns ConfigurationSpace

        """
        cs = ConfigurationSpace(seed=0)
        #cgalgo = Categorical("cgalgo", ["AUTO", "CHA", "VTA", "RTA", "SPARK", "GEOM"], default="CHA")  # -cg
        # cgalgo =Categorical("cgalgo",["RTA", "AUTO"]) # -cg

        #cs.add([cgalgo])

        aliasalgo = Categorical("aliasalgo", ["NONE", "FLOWSENSITIVE", "PTSBASED", "LAZY"])
        cs.add([aliasalgo])  # -aa



        layoutmode = Categorical("layoutmode", ["NONE", "PWD", "ALL"])
        cs.add([layoutmode])

        callbackanalyzer = Categorical("callbackanalyzer",
                                       ["DEFAULT", "FAST"])
        cs.add([callbackanalyzer])

        #pathreconstructionmode = Categorical("pathreconstructionmode",   ["NONE", "FAST", "PRECISE"])
        #cs.add([pathreconstructionmode])
        ################################################################
        """



        ################################################################
        
        ################################################################
        codeelimination = Categorical("codeelimination", ["NONE", "PROPAGATECONSTS", "REMOVECODE"])
        cs.add([codeelimination])"""
        ################################################################
        """
        ################################################################
        
        ################################################################
        dataflowsolver = Categorical("dataflowsolver",
                                     ["CONTEXTFLOWSENSITIVE", "FLOWINSENSITIVE"])
        cs.add([dataflowsolver])
        ################################################################
        implicit = Categorical("implicit", ["NONE", "ARRAYONLY", "ALL"])
        cs.add([implicit])
        ################################################################
        layoutmode = Categorical("layoutmode", ["NONE", "PWD", "ALL"])
        cs.add([layoutmode])
        ################################################################
        pathalgo = Categorical("pathalgo",
                               ["CONTEXTSENSITIVE", "CONTEXTINSENSITIVE", "SOURCESONLY"])
        cs.add([pathalgo])
        ################################################################

        ################################################################
        staticmode = Categorical("staticmode",
                                 ["CONTEXTFLOWSENSITIVE", "CONTEXTFLOWINSENSITIVE", "NONE"])
        cs.add([staticmode])
        ################################################################
        taintwrapper = Categorical("taintwrapper",
                                   ["NONE", "EASY", "STUBDROID", "MULTI"])
        cs.add([taintwrapper])
        ################################################################
        callbacksourcemode = Categorical("callbacksourcemode", ["NONE", "ALL", "SOURCELIST"])
        cs.add([callbacksourcemode])
"""
        return cs

    def train(self, config: Configuration, seed: int = 0):
        #  f-measure F = 2TP / (2TP + FP +FN)
        # aim is to maximize f_score which assumes values in interval [0,1] -> SMAC minimizes cost -> i.e. minimize 1-f_score
        start_time = time.time()
        # todo: remove seed
        """
        run train method on each apk-file of one subset of DroidBench with configuration.
        at the end you should have an optimal configuration for this subset of DroidBench.

        optimal configuration is which minimizes the costs.
        the cost is the sum of the list which contains the cost of each apk-file. the cost of each apk-file is number of
        differences between found leaks and expected leaks.

        :param
        expected_leaks: expected leaks from expected file
        found_leaks: leaks found by FlowDroid saved in output file
        :return
        all_false_positives = sum(cost)

        """
        aliasalgo = config["aliasalgo"]  # -aa
        callbackanalyzer = config["callbackanalyzer"]  # -ca
        layoutmode = config["layoutmode"]  # -l
        #cgalgo = config["cgalgo"]  # -cg
        #pathreconstructionmode = config["pathreconstructionmode"]  # -pr

        #
        # codeelimination = config["codeelimination"] # -ce

        # callbacksourcemode = config["callbacksourcemode"] # -cs
        # dataflowsolver = config["dataflowsolver"] # -ds
        # implicit = config["implicit"] # -i
        #
        # pathalgo = config["pathalgo"] # -pa
        # staticmode = config["staticmode"] # -sf
        # taintwrapper = config["taintwrapper"] # -tw

        # now FlowDroid is executed with selected cgalgo by SMAC:
        path_to_sdk = "/Users/ljubarah/Library/Android/sdk/platforms"  # sdk platform (always same)
        SourcesAndSinks = "/Users/ljubarah/DroidBench-develop/SourcesAndSinks.txt"  # sources and sinks file (always same)

        # ------------------------------------------------------------------
        # define apk-files by their path
        # todo: why does not each apk-file contain an expected-output file? -> get the missing expected files
        # ------------------------------------------------------------------
        path = "/Users/ljubarah/DroidBench-develop"
        list_of_all_apk_files = os.listdir(path + "/apk/InterComponentCommunication")
        # list_of_all_apk_files = ["PublicAPIField2.apk"]

        apk_files = []
        for file in list_of_all_apk_files:
            file = "/Users/ljubarah/DroidBench-develop/apk/InterComponentCommunication/" + file
            apk_files.append(file)
        # apk_files = ["/Users/ljubarah/DroidBench-develop/apk/InterComponentCommunication/PublicAPIField2.apk"]

        names = []
        for i in list_of_all_apk_files:
            i = i[:-4]
            names.append(i)
        # names = ["PublicAPIField2"]

        # ------------------------------------------------------------------
        # define expected-files by their path
        # ------------------------------------------------------------------
        expected_files = [path + "/eclipse-project/InterComponentCommunication/" + i + "/expected-info-flows.txt" for i
                          in names]

        # ------------------------------------------------------------------
        # define output-files by their path and by their configuration
        # ------------------------------------------------------------------
        # output_files = [path + "/eclipse-project/InterComponentCommunication/" + i + f"/OutputOfSMAC_three/output_{aliasalgo}_{cgalgo}_{pathreconstructionmode}.xml" for i in names]
        # output_files = [path + f"/eclipse-project/InterComponentCommunication/OutputSMAC/{i}_output_{aliasalgo}_{cgalgo}_{pathreconstructionmode}.xml" for i in names]

        # output_files = [f"/Users/ljubarah/Downloads/{i}_output_{aliasalgo}_{cgalgo}_{pathreconstructionmode}.xml" for i in names]
        # output_files = [f"/Users/ljubarah/Downloads/{i}_output_{cgalgo}_{aliasalgo}.xml" for i in names]
        output_files = [
            path + "/eclipse-project/InterComponentCommunication/" + i + f"/{callbackanalyzer}_{aliasalgo}_{layoutmode}.xml".format(
                callbackanalyzer=callbackanalyzer, aliasalgo=aliasalgo, layoutmode=layoutmode) for i in names]

        """
        Execute FlowDroid on instances and measure cost by following method:
        ----------------------------------------------------------------------------------------------------------------
        Step 1. Selection: Select configuration (e.g. cgalgo= "CHA")
        ---------------------------------------------------------------------------------------------------------------- 
        Step 2. Iteration: According to Eggensperger et al.-2019-Pitfalls and Best Practices in Algorithm Configuration:
        ---------------------------------------------------------------------------------------------------------------- 
        Run FlowDroid with this configuration on each apk-file of one subset (e.g. subsets defined by DroidBench; you 
        have to do this because according to this paper SMAC only makes sense if applied on similar instances. Because
        sense of SMAC is to find optimal configuration for these instances.)
        E.g. you have three instances i_1, i_2 and i_3 and two configurations conf_1 and conf_2.
        First iteration: run FlowDroid with first configuration conf_1 on these three instances and measure cost of each
        instance, e.g. c(conf1, i1) = 2, c(conf1, i2) = 5 and c(conf1, i3) = 4 -> sum_c = 2+5+4=11
        Second iteration: run FlowDroid with second configuration conf_2 on these three instances and measure cost of each
        instance, e.g. c(conf2, i1) = 20, c(conf2, i2) = 1 and c(conf2, i3) = 1 -> sum_c = 20+1+1 = 22

        Aim of AC according to this paper is to find configuration which minimizes the sum of costs. -> conf_1 minimizes 
        cost so optimal configuration is conf_2
        """

        # Step 1:
        # combine apk_files with expected output_files to run FlowDroid. and to compare expected leaks with found leaks:
        apk_expected_output = list(zip(apk_files, expected_files, output_files))
        all_false_positives = []  # all_false_positives contains false_positives costs of all apk-files
        all_false_negatives = []  # all_false_negatives contains costs of all apk-files
        all_f_score = []  # all_f_score contains all f_scores

        for apk, expected, output in apk_expected_output:

            # todo Eric: i've found the mistake: my output-file was always the same i.e. independent of new configurations
            #  i.e. i've compared the whole time the expected file with the same output-file
            #  -> that's why the costs were always the same
            false_positives = 0  # false_positives is false_positives of just one apk-file
            false_negatives = 0  # false_negatives is false_negatives of just one apk-file
            f_score = 0
            true_positives = 0

            app = ("java -jar /Users/ljubarah/FlowDroid-2.14.1/soot-infoflow-cmd-2.14.1-jar-with-dependencies.jar "
                   "-a {a} -p {p} -s {s} -o {o} "
                   "-ca {ca} -aa {aa} -l {l}").format(a=apk, p=path_to_sdk, s=SourcesAndSinks, o=output, ca=callbackanalyzer,
                                                aa=aliasalgo, l=layoutmode)

            os.system(app)



            # compare found leaks with expected leaks:
            # sometimes DroidBench does not contain for each apk-file an expected file
            #  so comparison is only possible if expected-file exists.
            # todo: why does DroidBench not always contain an expected file? e.g. for IntentSink2 although java file says there is one leak
            # sometimes FlowDroid does not generate output-files i.e. when no leak was found
            #   if output-file exists
            if os.path.isfile(expected):
                if os.path.isfile(output):  # here false positive or false negative or true positive
                    found_leaks = open(output).read()

                    pattern_false_positive = re.findall("&lt;(.*?)&gt;", found_leaks)
                    pattern_false_negative = re.findall("<(.*?)>", open(expected).read())
                    # todo: include in expected the name of java-files (because sometimes
                    #  leak is not in same java-files)

                    # output-file contains non sources/sinks i.e. edu.mit..... -> remove them:
                    for found in pattern_false_positive:
                        if found not in open(SourcesAndSinks).read():
                            pattern_false_positive.remove(found)

                    # output-file contains the two in sequence -> remove them:
                    pattern_false_positive = pattern_false_positive[::2]

                    # sources in expected-file begin with ={<      -> remove them
                    for i in pattern_false_negative:
                        if i[:3] == "={<":
                            pattern_false_negative.remove(i)
                            i = i[3:]
                            pattern_false_negative.append(i)

                    # expected-file contains non sources/sink i.e. edu.mit..... -> remove them: #todo: insert them again
                    for found in pattern_false_negative:
                        if found not in open(SourcesAndSinks).read():
                            pattern_false_negative.remove(found)

                    # i need copies to remove the already inspected leaks
                    # i need to remove them to keep at the end only leaks which were not inspected to calculate the true_positives
                    pattern_false_negative_less = pattern_false_negative.copy()
                    pattern_false_positive_less = pattern_false_positive.copy()

                    # check whether found_leak is in fact a leak (because the string
                    #  "&lt;edu.mit.public_api_field.MainActivity: void onCreate(android.os.Bundle)&gt;"
                    #  is also sometimes contained in the found_leaks file

                    for found in pattern_false_positive:
                        if found in open(SourcesAndSinks).read():
                            if found not in open(
                                    expected).read():  # it is a false positive -> increase the false_positives
                                false_positives += 1
                                pattern_false_positive.remove(found)
                    pattern_false_positive = pattern_false_positive_less

                    for found in pattern_false_negative:
                        if found in open(SourcesAndSinks).read():
                            if found not in open(
                                    output).read():  # it is a false negative -> increase the false_negatives
                                false_negatives += 1
                                pattern_false_negative_less.remove(found)
                    pattern_false_negative = pattern_false_negative_less

                    # check for true_positives
                    true_positives = len(set(pattern_false_positive).intersection(pattern_false_negative))
                    f_score = 2 * true_positives / (2 * true_positives + false_positives + false_negatives)

                else:  # else means here expected exists but FlowDroid does not find anything -> false negative
                    pattern_false_negative = re.findall("<(.*?)>", open(expected).read())

                    # sources in expected-file begin with ={<      -> remove these characters
                    for i in pattern_false_negative:
                        if i[:3] == "={<":
                            pattern_false_negative.remove(i)
                            i = i[3:]
                            pattern_false_negative.append(i)

                    pattern_false_negative_less = pattern_false_negative.copy()

                    for found in pattern_false_negative:
                        if found in open(
                                SourcesAndSinks).read():  # that means there are leaks expected but FlowDroid did not find any ->false negative
                            false_negatives += 1
                            pattern_false_negative_less.remove(found)
                    pattern_false_negative = pattern_false_negative_less
                    f_score = 0

            else:  # else no expected file exists
                if os.path.isfile(output):  # if output exists -> false positive
                    found_leaks = open(output).read()
                    pattern_false_positive = re.findall("&lt;(.*?)&gt;", found_leaks)

                    for found in pattern_false_positive:
                        if found not in open(SourcesAndSinks).read():
                            pattern_false_positive.remove(found)

                    # output-file contains the two in sequence -> remove them:
                    pattern_false_positive = pattern_false_positive[::2]
                    pattern_false_positive_less = pattern_false_positive.copy()
                    for found in pattern_false_positive:
                        if found in open(SourcesAndSinks).read():
                            false_positives += 1
                            pattern_false_positive_less.remove(found)
                    pattern_false_positive = pattern_false_positive_less
                    f_score = 0
                else:
                    # here no expected-file and no output-file exists i.e. here true negatives-> FlowDroid did everything correct -> f_score = 1
                    # #: is this correct for f-score (because f-score does not include true negatives)
                    f_score = 1
            print(f"apk", apk)
            print(f"false_positives", false_positives)
            print(f"false_negatives", false_negatives)
            print(f"true_positives", true_positives)
            print(f"f_score", f_score)

            all_f_score.append(f_score)
            print(f"1-statistics.mean(all_f_score) {1 - statistics.mean(all_f_score)}")
        return {"f_score": 1 - statistics.mean(all_f_score),
                "time": time.time()-start_time}

    # def plot


if __name__ == "__main__":

    # create an instance
    model = FlowDroid_configuration_SMAC()
    objectives = ["f_score", "time"]
    # scenario object specifies the environment
    scenario = Scenario(model.configspace, objectives=objectives, deterministic=True, n_trials=18 * 6,
                        #walltime_limit=10
                        )

    multi_objective_algorithm = ParEGO(scenario)

    # run SMAC to find optimal options: train the model in the set scenario
    smac = HPOFacade(  # todo: try others instead of HPOFacade
        scenario,
        model.train,
        overwrite=True, multi_objective_algorithm=multi_objective_algorithm,
    )  # define on what running smac

    incumbent = smac.optimize()  # define what to do i.e. optimize the cost
    # todo: smac.optimize() (another things i can do with smac else than smac.optimize ?)

    # print cost of default configuration and of incumbent to compare improvement
    default = model.configspace.get_default_configuration()
    default_cost = smac.validate(model.configspace.get_default_configuration())  # default configuration was with CHA
    print(f"Default configuration: {default}")
    print(f"Default cost: {default_cost}")

    # print cost of incumbent (best solution)
    incumbent_cost = smac.validate(incumbent)
    print(f"Incumbent configuration: {incumbent}")
    print(f"Optimal cost: {incumbent_cost}")

    print("")
    print("Runhistory:")

    # todo: plot the results over history:
    # Results over history
    for k, v in smac.runhistory.items():
        # print("k = {k}, v = {v}".format(k=k, v=v))
        config = smac.runhistory.get_config(k.config_id)
        print("------------------------")
        print("configuration_id= {id}".format(id=k.config_id))
        print("configuration = {config}".format(config=config))
        print("cost = {cost}".format(cost=v.cost))
        print("------------------------")

# todo: close the files (because i opened e.g. expected-flow-files
# todo: n_trials should be larger than cross product of all combinations
# todo: DroidBench 3.0 instead of DroidBench 2.0
# todo: try other subsets
# todo: generate output-file for each apk-instance and check whether the found leaks really do not change with changing configurations
# todo: compare smac results (so the leaks found by FlowDroid here in smac) with results of flowdroid in terminal
# todo: problem of expected file: there is always a source (maybe also sink?) in the expected file which starts with ={ -> i need to remove them because else python does not consider this as a source
#  because it cannot find it in the SourcesAndSinks file (or maybe i should change the in-command, so check whether expected string has a substring in SourcesAndSinks file
#  example of source:
#  ={<android.telephony.TelephonyManager: java.lang.String getDeviceId()
