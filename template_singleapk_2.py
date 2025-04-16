import json
import re
import os
import statistics

from six import reraise


def train(subset_apk, file, output_name, callbackanalyzer, aliasalgo, layoutmode):
    #  f-measure F = 2TP / (2TP + FP +FN)
    # aim is to maximize f_score which assumes values in interval [0,1] -> SMAC minimizes cost -> i.e. minimize 1-f_score
    path_to_sdk = "/Users/ljubarah/Library/Android/sdk/platforms"
    SourcesAndSinks = "/Users/ljubarah/DroidBench-develop/SourcesAndSinks.txt"
    path = "/Users/ljubarah/DroidBench-develop"
    apk = f"/Users/ljubarah/DroidBench-develop/apk/{subset_apk}/{file}.apk".format(subset_apk=subset_apk, file=file)
    expected = path + f"/eclipse-project/{subset_apk}/{file}/expected-info-flows.json".format(subset_apk=subset_apk,
                                                                                              file=file)
    output = f"/Users/ljubarah/Downloads/output_{output_name}.xml".format(output_name=output_name)
    # output = "/Users/ljubarah/DroidBench-develop/TestOutput/two_leaks.xml"
    app = ("java -jar /Users/ljubarah/FlowDroid-2.14.1/soot-infoflow-cmd-2.14.1-jar-with-dependencies.jar "
           "-a {a} -p {p} -s {s} -o {o} "
           "-ca {ca} -aa {aa} -l {l}").format(a=apk, p=path_to_sdk, s=SourcesAndSinks, o=output,
                                              ca=callbackanalyzer,
                                              aa=aliasalgo, l=layoutmode)
    os.system(app)
    false_positives = 0  # false_positives is false_positives of just one apk-file
    false_negatives = 0  # false_negatives is false_negatives of just one apk-file

    true_positives = 0
    all_f_score = []
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

        sink_method_pattern_found = re.findall('Sink Statement(.*?)&lt;(.*?)&gt;(.*?)&lt;(.*?)&gt;', found_leaks)
        for i in sink_method_pattern_found:
            sink_found.append(i[1])
            sink_method_found.append(i[3])


    # list to compare expected and found
    source_expected_list = list(zip(source_method_expected, source_expected))
    source_found_list = list(zip(source_method_found, source_found))

    sink_expected_list= list(zip(sink_method_expected, sink_expected))
    sink_found_list = list(zip(sink_method_found, sink_found))



    if (source_expected_list == set() and source_found_list == set()
            and sink_expected_list == set() and sink_found_list == set()):  # means nothing expected and found -> means no TP, no FP, no FN -> set f_score = 1
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
    #all_false_positives.append(false_positives)
    #all_false_negatives.append(false_negatives)
    print("Leen")
    print(apk)
    print("")
    print("TP", true_positives)
    print("FP", false_positives)
    print("FN", false_negatives)

    return f_score


print(train(
    subset_apk="GeneralJava",
    file="StringToCharArray1",
    output_name="StringToCharArray1",
    callbackanalyzer="FAST",
    aliasalgo="FLOWSENSITIVE",
    layoutmode="NONE"
))






