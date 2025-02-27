import pathlib

from wfcommons import BlastRecipe, MontageRecipe, SoykbRecipe
from wfcommons.wfbench import WorkflowBenchmark, DaskTranslator, CWLTranslator, ParslTranslator
from wfcommons.wfinstances import Instance
from wfcommons import WorkflowGenerator


import argparse
import json


def main():
    parser = argparse.ArgumentParser(description="Process a workflow JSON file.")
    parser.add_argument("--workflow", type=str, help="Path to the workflow JSON file.")
    parser.add_argument("--test", action="store_true", help="Create a test benchmark")
    
    args = parser.parse_args()

    if args.test:
    
        # create a workflow benchmark object to generate specifications based on a Montage recipe (small benchmark for testing)
        benchmark = WorkflowBenchmark(recipe=MontageRecipe, num_tasks=60)
        # generate a specification based on performance characteristics
        path = benchmark.create_benchmark(pathlib.Path("./benchmarks/montage"), cpu_work=100, data=10, percent_cpu=0.6)
    if args.workflow:
        # create a workflow benchmark from a synthetic workflow (workflow used in the fgcs paper)
        workflow_instance = Instance(args.workflow)
        benchmark = WorkflowBenchmark(recipe=SoykbRecipe, num_tasks=156)
        output_path = pathlib.Path(f"./benchmarks/{workflow_instance.name}")
        path = benchmark.create_benchmark_from_synthetic_workflow(output_path, workflow_instance.workflow)
    

if __name__ == "__main__":
    main()

