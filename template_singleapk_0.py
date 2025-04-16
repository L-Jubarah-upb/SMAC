import re
import os
import statistics
def train(cgalgo, subset_apk, file, aliasalgo, pathreconstructionmode):
    #  f-measure F = 2TP / (2TP + FP +FN)
    # aim is to maximize f_score which assumes values in interval [0,1] -> SMAC minimizes cost -> i.e. minimize 1-f_score
    path_to_sdk = "/Users/ljubarah/Library/Android/sdk/platforms"
    SourcesAndSinks = "/Users/ljubarah/DroidBench-develop/SourcesAndSinks.txt"
    path = "/Users/ljubarah/DroidBench-develop"
    apk = f"/Users/ljubarah/DroidBench-develop/apk/{subset_apk}/{file}.apk".format(subset_apk=subset_apk, file=file)
    expected =  path + f"/eclipse-project/{subset_apk}/{file}/expected-info-flows.json".format(subset_apk=subset_apk, file=file)
    output = f"/Users/ljubarah/DroidBench-develop/TestOutput/{file}_{cgalgo}_{aliasalgo}_{pathreconstructionmode}.xml".format(file=file, cgalgo=cgalgo, aliasalgo=aliasalgo, pathreconstructionmode = pathreconstructionmode)
    app = ("java -jar /Users/ljubarah/FlowDroid-2.14.1/soot-infoflow-cmd-2.14.1-jar-with-dependencies.jar "
           "-a {a} -p {p} -s {s} -o {o} -cg {cg} -aa {aa}, -pr {pr}").format(a=apk, p=path_to_sdk, s=SourcesAndSinks, o=output, cg=cgalgo, aa = aliasalgo, pr=pathreconstructionmode)
    os.system(app)

    false_positives = 0
    false_negatives = 0
    all_f_score = [] # all_f_score contains all f_scores
    true_positives = 0

    if os.path.isfile(expected):
        if os.path.isfile(output): # here false positive or false negative or true positive
            found_leaks = open(output).read()
            pattern_false_positive = re.findall("&lt;(.*?)&gt;", found_leaks)
            pattern_false_negative = re.findall("<(.*?)>", open(expected).read())
            #todo: include in expected the name of java-files (because sometimes
            #  leak is not in same java-files)

            for found in pattern_false_positive:
                if found not in open(SourcesAndSinks).read():
                    pattern_false_positive.remove(found)

            # output-file contains the two in sequence -> remove them:
            pattern_false_positive = pattern_false_positive[::2]

            # sources in expected-file begin with ={<      -> remove these characters
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

            for found in pattern_false_positive:
                if found in open(SourcesAndSinks).read():
                    if found not in open(expected).read():
                        false_positives += 1
                        pattern_false_positive.remove(found)
            pattern_false_positive = pattern_false_positive_less

            for found in pattern_false_negative:
                if found in open(SourcesAndSinks).read():
                    if found not in open(output).read():
                        false_negatives += 1
                        pattern_false_negative_less.remove(found)
            pattern_false_negative = pattern_false_negative_less

            # check for true_positives
            true_positives = len(set(pattern_false_positive).intersection(pattern_false_negative))
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
            # #todo: is this correct for f-score (because f-score does not include true negatives)
            f_score = 1



    all_f_score.append(f_score)
    print(f"false positives: {false_positives}")
    print(f"false negatives: {false_negatives}")
    print(f"true positives: {true_positives}")
    print(f"f_score: {f_score}")
    #print(f"1-statistics.mean(all_f_score) {1-statistics.mean(all_f_score)}")
    return 1-statistics.mean(all_f_score)


print(train(cgalgo="SPARK", aliasalgo = "LAZY", pathreconstructionmode = "PRECISE",
      subset_apk = "ArraysAndLists",
      file="MultidimensionalArray1"))
