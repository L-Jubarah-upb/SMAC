"""
Aim: search for optimal configuration of cgalgo to minimize
    the difference between found-leaks and expected-leaks
    (this is the target function in train function)
cgalgo: Callgraph algorithm to use
    (AUTO, CHA, VTA, RTA, SPARK, GEOM)
use APK-file of DroidBench:
/Users/ljubarah/DroidBench-develop/apk/GeneralJava/FlowSensitivity1.apk
contains one leak with:
<android.util.Log: int i(java.lang.String,java.lang.String)> -> _SINK_
<android.telephony.TelephonyManager: java.lang.String getDeviceId()> -> _SOURCE_

this file is based on the example of the SMAC3-website:
https://automl.github.io/SMAC3/v2.3.0/examples/1%20Basics/1_quadratic_function/
"""

"""
Configuration is a class of package ConfigSpace and contains only one configuration
ConfigurationSpace is also a class and contains multiple configurations, 
i.e. configurations can be sampled from the ConfigurationSpace
Categorical creates a CategoricalHyperparameter
"""
import re
from ConfigSpace import Configuration, ConfigurationSpace, Categorical
import time
import statistics

#timeout = time.time() + 60 * 1  # 1 minutes

# from matplotlib import pyplot as plt
# from smac.facade.algorithm_configuration_facade import AlgorithmConfigurationFacade as ACFacade
from smac.facade.hyperparameter_optimization_facade import HyperparameterOptimizationFacade as HPOFacade  # todo: change smac.facade?

"""
RunHistory: contains information of evaluated/running trials and calculates the cost
(SMAC automatically generates an output file -> have a look into that)
Scenario: contains variables of the environment: configuration space, number of trials, time limit etc.
"""
from smac import Scenario  # ,RunHistory

"""os to execute FlowDroid from this python-script"""
import os

import json
import re



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

        cgalgo = Categorical("cgalgo", ["AUTO", "CHA", "VTA", "RTA", "SPARK", "GEOM"], default="CHA")  # -cg
        cs.add([cgalgo])
        aliasalgo = Categorical("aliasalgo", ["NONE", "FLOWSENSITIVE", "PTSBASED", "LAZY"])
        cs.add([aliasalgo])  # -aa
        pathreconstructionmode = Categorical("pathreconstructionmode",   ["NONE", "FAST", "PRECISE"])
        cs.add([pathreconstructionmode])
        #pathalgo = Categorical("pathalgo",                        ["CONTEXTSENSITIVE", "CONTEXTINSENSITIVE", "SOURCESONLY"])
        #cs.add([pathalgo])

        #codeelimination = Categorical("codeelimination", ["NONE", "PROPAGATECONSTS", "REMOVECODE"])
       # cs.add([codeelimination])



        #taintwrapper = Categorical("taintwrapper", ["NONE", "EASY", "STUBDROID", "MULTI"])
        #cs.add([taintwrapper])
        ################################################################
        """



        ################################################################

        ################################################################
        

        layoutmode = Categorical("layoutmode", ["NONE", "PWD", "ALL"])
        cs.add([layoutmode])

        callbackanalyzer = Categorical("callbackanalyzer",
                                       ["DEFAULT", "FAST"])
        cs.add([callbackanalyzer])
        
        """
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
        
        ################################################################

        ################################################################
        staticmode = Categorical("staticmode",
                                 ["CONTEXTFLOWSENSITIVE", "CONTEXTFLOWINSENSITIVE", "NONE"])
        cs.add([staticmode])
        ################################################################
        
        ################################################################
        callbacksourcemode = Categorical("callbacksourcemode", ["NONE", "ALL", "SOURCELIST"])
        cs.add([callbacksourcemode])
"""
        return cs

    def train(self, config: Configuration, seed: int = 0):
        #  f_score F = 2TP / (2TP + FP +FN)
        # aim is to maximize f_score which assumes values in interval [0,1] -> SMAC minimizes cost -> i.e. minimize 1-f_score

        # todo: remove seed
        """
        run train method on each apk-file of one subset of DroidBench with configuration.
        at the end you should have an optimal configuration for this subset of DroidBench.

        optimal configuration is which minimizes the costs.


        :param
        expected_leaks: expected leaks from expected file
        found_leaks: leaks found by FlowDroid saved in output file
        :return


        """
        aliasalgo = config["aliasalgo"]  # -aa
        #callbackanalyzer = config["callbackanalyzer"]  # -ca
        #layoutmode = config["layoutmode"]  # -l
        cgalgo = config["cgalgo"]  # -cg
        #pathalgo = config["pathalgo"]  # -pa
        #codeelimination = config["codeelimination"] # -ce
        pathreconstructionmode = config["pathreconstructionmode"]  # -pr
        #taintwrapper = config["taintwrapper"] # -tw

        # callbacksourcemode = config["callbacksourcemode"] # -cs
        # dataflowsolver = config["dataflowsolver"] # -ds
        # implicit = config["implicit"] # -i
        #

        # staticmode = config["staticmode"] # -sf

        # now FlowDroid is executed with selected cgalgo by SMAC:
        path_to_sdk = "/Users/ljubarah/Library/Android/sdk/platforms"  # sdk platform (always same)
        SourcesAndSinks = "/Users/ljubarah/DroidBench-develop/SourcesAndSinks.txt"  # sources and sinks file (always same)

        # ------------------------------------------------------------------
        # define apk-files by their path
        # ------------------------------------------------------------------
        path = "/Users/ljubarah/DroidBench-develop"
        list_of_all_apk_files = os.listdir(path + "/apk/GeneralJava")
        # list_of_all_apk_files = ["FlowSensitivity1.apk"]

        apk_files = []
        for file in list_of_all_apk_files:
            file = "/Users/ljubarah/DroidBench-develop/apk/GeneralJava/" + file
            apk_files.append(file)
        # apk_files = ["/Users/ljubarah/DroidBench-develop/apk/GeneralJava/FlowSensitivity1.apk"]

        names = []
        for i in list_of_all_apk_files:
            i = i[:-4]
            names.append(i)
        # names = ["FlowSensitivity1"]

        # ------------------------------------------------------------------
        # define expected-files by their path
        # ------------------------------------------------------------------
        expected_files = [path + "/eclipse-project/GeneralJava/" + i + "/expected-info-flows.json" for i
                          in names]

        # ------------------------------------------------------------------
        # define output-files by their path and by their configuration
        # ------------------------------------------------------------------
        # output_files = [path + "/eclipse-project/GeneralJava/" + i + f"/OutputOfSMAC_three/output_{aliasalgo}_{cgalgo}_{pathreconstructionmode}.xml" for i in names]
        # output_files = [path + f"/eclipse-project/GeneralJava/OutputSMAC/{i}_output_{aliasalgo}_{cgalgo}_{pathreconstructionmode}.xml" for i in names]

        # output_files = [f"/Users/ljubarah/Downloads/{i}_output_{aliasalgo}_{cgalgo}_{pathreconstructionmode}.xml" for i in names]
        # output_files = [f"/Users/ljubarah/Downloads/{i}_output_{cgalgo}_{aliasalgo}.xml" for i in names]
        output_files = [
            path + "/eclipse-project/GeneralJava/Output/17_04_2025_cg_aa_pr/" + i + f"_{cgalgo}_{aliasalgo}_{pathreconstructionmode}.xml".format(
                 cgalgo=cgalgo, aliasalgo = aliasalgo, pathreconstructionmode = pathreconstructionmode) for i in names]

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

            # change directory to run FlowDroid
            os.chdir("/Users/ljubarah/FlowDroid-2.14.1")
            app = ((
                       "java -jar soot-infoflow-cmd-2.14.1-jar-with-dependencies.jar \\-a {a} \\-p {p} \\-s {s} \\-o {o} \\ -cg {cg} \\ -aa {aa} \\ -pr {pr}")
                   .format(a=apk, p=path_to_sdk, s=SourcesAndSinks, o=output,

                            cg=cgalgo, aa = aliasalgo, pr = pathreconstructionmode))

            os.system(app)
            os.chdir("/Users/ljubarah/SMAC3/benchmark/src/models")
            #if time.time() > timeout:
             #   break

            # compare found leaks with expected leaks:
            # sometimes DroidBench does not contain for each apk-file an expected file
            #  so comparison is only possible if expected-file exists.
            # sometimes FlowDroid does not generate output-files i.e. when no leak was found
            false_positives = 0  # false_positives is false_positives of just one apk-file
            false_negatives = 0  # false_negatives is false_negatives of just one apk-file

            true_positives = 0

            source_expected = []
            sink_expected = []
            sink_method_expected = []
            source_method_expected = []

            source_found = []
            sink_found = []
            sink_method_found = []
            source_method_found = []

            if os.path.isfile(expected):
                with open(expected) as expected:
                    expected = expected.read()
                    expected = json.loads(expected)
                    for key in expected["expected-info-flows"]:
                        if "Sink" in key:
                            sink_expected.append(key["Sink"])
                        if "Source" in key:
                            source_expected.append(key["Source"])
                        if "Sink" in key and "Method" in key:
                            sink_method_expected.append(key["Method"])
                        if "Source" in key and "Method" in key:
                            source_method_expected.append(key["Method"])

            if os.path.isfile(output):
                found_leaks = open(output).read()
                source_method_pattern_found = re.findall('Source Statement(.*?)&lt;(.*?)&gt;(.*?)&lt;(.*?)&gt;',
                                                         found_leaks)
                for i in source_method_pattern_found:
                    source_method_found.append(i[3])
                    source_found.append(i[1])

                sink_method_pattern_found = re.findall('Sink Statement(.*?)&lt;(.*?)&gt;(.*?)&lt;(.*?)&gt;',
                                                       found_leaks)
                for i in sink_method_pattern_found:
                    sink_found.append(i[1])
                    sink_method_found.append(i[3])

            # list to compare expected and found
            source_expected_list = list(zip(source_method_expected, source_expected))
            source_found_list = list(zip(source_method_found, source_found))

            sink_expected_list = list(zip(sink_method_expected, sink_expected))
            sink_found_list = list(zip(sink_method_found, sink_found))

            if (source_expected_list == [] and source_found_list == []
                    and sink_expected_list == [] and sink_found_list == []):  # means nothing expected and found -> means no TP, no FP, no FN -> set f_score = 1
                f_score = 1

            else:
                # first for sources:
                source_expected_list_copy = source_expected_list.copy()
                source_found_list_copy = source_found_list.copy()
                source_intersection = []
                for i in source_expected_list:
                    if i in source_found_list_copy:
                        source_intersection.append(i)
                        source_expected_list_copy.remove(i)
                        source_found_list_copy.remove(i)
                true_positives += len(source_intersection)
                false_negatives += len(source_expected_list_copy)
                false_positives += len(source_found_list_copy)

                # now same for sinks:
                sink_expected_list_copy = sink_expected_list.copy()
                sink_found_list_copy = sink_found_list.copy()
                sink_intersection = []
                for i in sink_expected_list:
                    if i in sink_found_list_copy:
                        sink_intersection.append(i)
                        sink_expected_list_copy.remove(i)
                        sink_found_list_copy.remove(i)
                true_positives += len(sink_intersection)
                false_negatives += len(sink_expected_list_copy)
                false_positives += len(sink_found_list_copy)

                f_score = 2 * true_positives / (2 * true_positives + false_positives + false_negatives)
            all_f_score.append(f_score)
            all_false_positives.append(false_positives)
            all_false_negatives.append(false_negatives)
            print("Leen")
            print(apk)

            print("")
            print("TP", true_positives)
            print("FP", false_positives)
            print("FN", false_negatives)
            print(f_score)
        print("jetz fertig")
        return 1 - statistics.mean(all_f_score)



    # def plot


if __name__ == "__main__":

    # create an instance
    model = FlowDroid_configuration_SMAC()

    # scenario object specifies the environment
    scenario = Scenario(model.configspace, deterministic=True, n_trials=18 * 6)

    # run SMAC to find optimal options: train the model in the set scenario
    smac = HPOFacade(  # todo: try others instead of HPOFacade
        scenario,
        model.train,
        overwrite=True
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
