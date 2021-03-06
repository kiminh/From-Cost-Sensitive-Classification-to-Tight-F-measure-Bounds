"""
    Manage FIAFMO experiences
"""

import os
import sys
import argparse
import logging as log

import numpy as np

import cone
import baselines
import parambath
import bisection

def experiment(argv):
    """ Hanlde exeperience corresponding to options """

    dataset = np.load(argv.dataset)['dataset'].item()
    dataset_name = os.path.basename(argv.dataset).replace(".npz", "")

    algo = get_algo(argv)

    results_path = os.path.join(argv.log_dir, dataset_name)

    try:
        os.makedirs(results_path)
    except FileExistsError:
        pass

    for fold_i in argv.fold_grid:
        log.info("Algo %s, Dataset %s fold #%d", argv.algo, dataset_name, fold_i)

        results = {}

        if argv.classif == "random_forest":
            grid_hparam = argv.depth_grid
        else:
            grid_hparam = argv.C_grid

        for hparam in grid_hparam:
            log.info("\t HP=%f", hparam)


            if argv.save_states:
                states_path = results_path+"/states_fold%d/hp%f"%(fold_i, hparam)
                try:
                    os.makedirs(states_path)
                except FileExistsError:
                    pass
                argv.save_states = states_path

            results[hparam] = algo.run_algo(dataset["fold%d"%fold_i], dataset["nb_class"],
                                            hparam, argv)

            if not argv.save_predictions:
                del results[hparam]["predictions"]

            log.debug(results[hparam])

        np.save(results_path+"/%s_%s_%s_fold%d.npy"%(argv.algo, argv.classif, dataset_name, fold_i),
                results)

def get_algo(argv):
    """ get algorithm module """

    if argv.algo.lower() == "cone":
        return cone

    if argv.algo.lower() == "parambath":
        return parambath

    if argv.algo.lower() == "bisection":
        return bisection

    if argv.algo.lower() == "baseline" or argv.algo.lower() == "ir":
        return baselines

    log.error("Unknown algorithm %s. Algo available: cone, parambath, bisection, baseline, ir", argv.algo)
    sys.exit(0)

if __name__ == "__main__":
    log.basicConfig(stream=sys.stdout, level=log.DEBUG)
    PARSER = argparse.ArgumentParser()

    PARSER.add_argument("--dataset", help="Dataset file", type=str, required=True)
    PARSER.add_argument("--log_dir", help="Logs directory", type=str, required=True)
    PARSER.add_argument("--algo", help="(cone|parambath|baseline|ir)", type=str, required=True)

    # not required options
    PARSER.add_argument("--C_grid", help="Grid over values of C", metavar="C",
                        type=float, nargs="+", default=[2**exp for exp in range(-6, 7)])
    PARSER.add_argument("--fold_grid", help="Tested folds", metavar="FOLD",
                        type=int, nargs="+", default=list(range(5)))
    PARSER.add_argument("--max_step", help="Maximum number of trained classifiers",
                        type=int, default=19)
    PARSER.add_argument("--classif", help="Classifier (logi_reg|linear_svm|SVC_(linear|poly|rbf|sigmoid)|random_forest)",
                        type=str, default="linear_svm")
    PARSER.add_argument("--save_predictions", action='store_true',
                        help="Enable saving all predictions (required for thresholding, warning: results from large dataset can be heavy)")

    # algo-specific options
    PARSER.add_argument("--tmin", help="if algo is cone or parambath: inf bound of t space",
                        type=float, default=0)
    PARSER.add_argument("--tmax", help="if algo is cone or parambath: sup bound of t space",
                        type=float, default=1)
    PARSER.add_argument("--beta", help="if algo is cone or parambath: beta used in class weight computation",
                        type=float, default=1.0)
    PARSER.add_argument("--strategy", type=str, default="middle_cones",
                        help="if algo is cone: strategy for cone selection (left|right|middle_space|middle_cones)")
    PARSER.add_argument("--save_states", help="if algo is cone: Save all intermediate states as png",
                        action='store_true')
    PARSER.add_argument("--cone_with_state", help="if algo is cone: use implementation with discretised (t, fm) space",
                        action='store_true')
    PARSER.add_argument("--state_size", help="if algo is cone: size of the discretised (t, fm) space",
                        type=int, default=10000)
    PARSER.add_argument("--kappa", help="if algo is bisection: number of tuning iterations",
                        type=int, default=100)
    PARSER.add_argument("--depth_grid", help="random forest max depth (replace C grid)",
                        type=int, nargs="+", default=[2**exp for exp in range(0, 7)])

    # classifier-specific options
    PARSER.add_argument("--nb_features", help="if classif is DCA_ERSVM or H_ERSVM: number of features in dataset",
                        type=int, default=0)

    experiment(PARSER.parse_args())
