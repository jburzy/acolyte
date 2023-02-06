import argparse
import yaml
import os
import sys
import glob
import logging

def get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config',  type=str, default='', help="The \
        configuration file defining the job")
    parser.add_argument('--maxEvents',  type=int, default=-1)
    parser.add_argument('--firstEvent',  type=int, default=0)
    parser.add_argument('-d','--debug', action='store_true')
    return parser.parse_args()

def main():

    # parse the arguments
    args = get_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    # parse the yaml config
    run_config = {}
    with open(args.config) as f:
        try:
            run_config = yaml.load(f.read(),Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    # get the input files
    input_files_pattern = run_config['global'].get('input_files','')
    if not input_files_pattern:
        logging.error("No input files specified. Please check your config file.")
        raise Exception()
    
    # get input files
    input_files = [sorted(glob.glob(inputpattern)) for inputpattern in input_files_pattern.split(',')]
    input_files = [item for sublist in input_files for item in sublist]

    if not input_files:
        logging.error(f"No input files found for pattern {input_files_pattern}. Please check your config file.")
        raise Exception()

    logging.info("The following input files will be processed:")
    for f in input_files:
        logging.info(f"\t{f}")

    # load ROOT and compiled libraries
    import ROOT

    output_file = ROOT.TFile(run_config["global"]["output_file"],"RECREATE")
    # build a TChain from the input
    for region in run_config['regions']:
        logging.info(f"Processing region: {region['name']}")
        output_file.mkdir(region['name'])
        output_file.cd(region['name'])
        c = ROOT.TChain()
        for f in input_files:
            c.Add(f + "/" + region['tree_name'])

        df =  ROOT.RDataFrame(c)

        for hist in region['histograms']:
            h = df.Filter(region['selection']).Histo1D(hist["definition"],hist["expression"])
        h.Write()

    output_file.Write()
    output_file.Close()

if __name__ == "__main__":
    main()
