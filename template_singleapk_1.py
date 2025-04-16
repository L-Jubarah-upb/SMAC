import json
import re
import os
import statistics

from six import reraise


def train(subset_apk, file, output_name):
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
           "-a {a} -p {p} -s {s} -o {o} -cg {cg} -aa {aa} -pr {pr} ").format(a=apk, p=path_to_sdk, s=SourcesAndSinks,
                                                                             o=output, cg="VTA", aa="LAZY",
                                                                             pr="PRECISE")
    os.system(app)

    false_positives = 0
    false_negatives = 0
    true_positives = 0
    all_f_score = []  # all_f_score contains all f_scores

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

    if os.path.isfile(output):  # here false positive or false negative or true positive
        found_leaks = open(output).read()
        source_method_pattern_found = re.findall('Source Statement(.*?)&lt;(.*?)&gt;(.*?)&lt;(.*?)&gt;', found_leaks)
        for i in source_method_pattern_found:
            source_method_found.append(i[3])
            source_found.append(i[1])

        sink_method_pattern_found = re.findall('Sink Statement(.*?)&lt;(.*?)&gt;(.*?)&lt;(.*?)&gt;', found_leaks)
        for i in sink_method_pattern_found:
            sink_found.append(i[1])
            sink_method_found.append(i[3])

        print("")

        print(f"source_expected\n{source_expected}".format(source_expected=source_expected))
        print(f"source_found\n{source_found}".format(source_found=source_found))
        print("")

        print(f"sink_expected\n{sink_expected}".format(sink_expected=sink_expected))
        print(f"sink_found\n{sink_found}".format(sink_found=sink_found))
        print("")

        print(f"source_method_expected\n{source_method_expected}".format(source_method_expected=source_method_expected))
        print(f"source_method_found\n{source_method_found}".format(source_method_found=source_method_found))
        print("")

        print(f"sink_method_expected\n{sink_method_expected}".format(sink_method_expected=sink_method_expected))
        print(f"sink_method_found\n{sink_method_found}".format(sink_method_found=sink_method_found))
        print("")

        print(set(source_expected) == set(source_found))
        # todo: do not consider the order so that is why i took the set-command but now i have to consider the number of elements in the set!!
        #
        print(set(sink_expected) == set(sink_found))
        print(set(source_method_expected) == set(source_method_found))
        print(set(sink_method_expected) == set(sink_method_found))

        # case 1: expected = output -> only true_positives -> f_score = 1

        # todo: when i compare sources and sinks i have to do sets:
        #  1. make set of source and sink of output-file (i.e. found_leak = (sink[i], source[i]) and expected-leak = (sink[i], source[i])
        #  and then compare all sets for accordance
        #  because at beginning i wanted to check whether first expected source is equal to first found source but imagine this:
        #  expected_sinks = [a, b]
        #  found_sinks = [b, a]
        #  expected_sources = [x, y]
        #  found_sources = [y, x]
        #  -> FlowDroid did everything correct -> so i should not consider the order
        #  -> make sets: expected {a,x}, {b,y} and found: {b,y}, {a,x}  ->  consider also the zugehörige methods!!!!!!!!!
        """

        # i need copies to remove the already inspected leaks
        # i need to remove them to keep at the end only leaks which were not inspected to calculate the true_positives
        pattern_false_negative_less = pattern_false_negative.copy()
        pattern_false_positive_less = sink_found_pattern.copy()

        for found in sink_found_pattern:
            if found in open(SourcesAndSinks).read():
                if found not in open(expected).read():
                    false_positives += 1
                    sink_found_pattern.remove(found)
        sink_found_pattern = pattern_false_positive_less

        for found in pattern_false_negative:
            if found in open(SourcesAndSinks).read():
                if found not in open(output).read():
                    false_negatives += 1
                    pattern_false_negative_less.remove(found)
        pattern_false_negative = pattern_false_negative_less

        # check for true_positives
        true_positives = len(set(sink_found_pattern).intersection(pattern_false_negative))
        f_score = 2 * true_positives / (2 * true_positives + false_positives + false_negatives)
    else: # else means here expected exists but FlowDroid does not find anything -> false negative

        pattern_false_negative = re.findall("<(.*?)>", open(expected).read())

        # sources in expected-file begin with ={<      -> remove these characters
        for i in pattern_false_negative:
            if i[:3] == "={<":
                pattern_false_negative.remove(i)
                i = i[3:]
                pattern_false_negative.append(i)

        pattern_false_negative_less = pattern_false_negative.copy()


        for found in pattern_false_negative:
            if found in open(SourcesAndSinks).read():
                false_negatives += 1
                pattern_false_negative_less.remove(found)
        pattern_false_negative = pattern_false_negative_less
        f_score = 0

else: # else no expected file exists
    if os.path.isfile(output): # if output exists -> false positive
        found_leaks = open(output).read()
        sink_found_pattern = re.findall("&lt;(.*?)&gt;", found_leaks)

        for found in sink_found_pattern:
            if found not in open(SourcesAndSinks).read():
                sink_found_pattern.remove(found)

        # output-file contains the two in sequence -> remove them:
        sink_found_pattern = sink_found_pattern[::2]
        pattern_false_positive_less = sink_found_pattern.copy()
        for found in sink_found_pattern:
            if found in open(SourcesAndSinks).read():
                false_positives += 1
                pattern_false_positive_less.remove(found)
        sink_found_pattern = pattern_false_positive_less
        f_score = 0
    else:
        # here no expected-file and no output-file exists i.e. here true negatives-> FlowDroid did everything correct -> f_score = 1
        # #todo: is this correct for f-score (because f-score does not include true negatives)
        f_score = 1



all_f_score.append(f_score)
print(f"false positives: {false_positives}")
print(f"false negatives: {false_negatives}")
print(f"true positives: {true_positives}")
print(f"f_score: {f_score}")
#print(f"1-statistics.mean(all_f_score) {1-statistics.mean(all_f_score)}")
return 1-statistics.mean(all_f_score)"""
    return 1


print(train(
    subset_apk="GeneralJava",
    file="VirtualDispatch2",
    output_name="1"
))






