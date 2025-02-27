#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 The WfCommons Team.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import ast
import json
import logging
import pathlib
import argparse
from typing import Union, Optional
from collections import defaultdict, deque
from wfcommons.common import Workflow
from wfcommons.wfinstances import Instance
from abstract_translator import Translator

this_dir = pathlib.Path(__file__).resolve().parent


class ParslTranslator(Translator):
    """
    A WfFormat parser for creating Parsl workflow benchmarks.

    :param workflow: Workflow benchmark object or path to the workflow benchmark JSON instance.
    :type workflow: Union[Workflow, pathlib.Path],
    :param logger: The logger where to log information/warning or errors (optional).
    :type logger: Logger
    """
    def __init__(self,
                 workflow: Union[Workflow, pathlib.Path],
                 logger: Optional[logging.Logger] = None) -> None:
        super().__init__(workflow, logger)
        self.parsl_script = []
        self.task_level_map = defaultdict(lambda: [])

        indegree = {}

        for task in self.tasks.values():
            indegree[task.task_id] = len(self.task_parents[task.task_id])
        queue = deque(self.root_task_names)
        top_sort = []

        while queue:
            task_name = queue.popleft()
            top_sort.append(task_name)

            for child in self.task_children[task_name]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)

        assert (len(top_sort) == len(self.tasks)), "Error: The workflow contains a cycle"

        levels = {task_name: 0 for task_name in top_sort}

        for task_name in top_sort:
            for child in self.task_children[task_name]:
                levels[child] = max(levels[child], levels[task_name] + 1)

        for task_name, level in levels.items():
            self.task_level_map[level].append(task_name)

        bottom_level = {task_name: 0 for task_name in top_sort}

        for task_name in reversed(top_sort):
            for child in self.task_children[task_name]:
                bottom_level[task_name] = max(bottom_level[task_name], bottom_level[child] + 1)

        self.bottom_level = bottom_level

    def translate(self, output_folder: pathlib.Path) -> None:
        """
        Translate a workflow benchmark description (WfFormat) into an actual workflow application.

        :param output_folder: The path to the folder in which the workflow benchmark will be generated.
        :type output_folder: pathlib.Path
        """
        # Parsing each of the WfFormat Tasks as bash apps in Parsl
        codelines = self._parsl_wftasks_codelines()

        wf_codelines = "\n".join(codelines)

        # Opening the parsl template file
        with open(this_dir.joinpath("templates/parsl_template.py"), encoding="utf-8") as fp:
            run_workflow_code = fp.read()
        run_workflow_code = run_workflow_code.replace("# Generated code goes here", wf_codelines)

         # Writing the generated parsl code to a file
        output_folder.mkdir(parents=True)
        with open(output_folder.joinpath("parsl_workflow.py"), "w", encoding="utf-8") as fp:
            fp.write(run_workflow_code)

        # Additional files
        self._copy_binary_files(output_folder)
        self._generate_input_files(output_folder)

    def _parsl_wftasks_codelines(self) -> None:
        codelines = ["task_arr = []\n"]

        # Parsing each steps by Workflow levels
        for level in sorted(self.task_level_map.keys()):
            # Parsing each task within a Workflow level
            for task_name in self.task_level_map[level]:
                # Getting the task object
                task = self.tasks[task_name]

                percent_cpu = 0
                cpu_work = 0

                args = []
                for a in task.args:
                    if a.startswith("--percent-cpu"):
                        percent_cpu = float(a.split(" ")[1])
                    if a.startswith("--cpu-work"):
                        cpu_work = int(a.split(" ")[1])
                    if a.startswith("--output-files"):
                        flag, output_files_dict = a.split(" ", 1)
                        output_files_dict = ast.literal_eval(output_files_dict)
                        a = f"{flag} '{json.dumps(output_files_dict).replace('"', '\\"')}'"

                    if a.startswith("--input-files"):
                        flag, input_files_arr = a.split(" ", 1)
                        input_files_arr = ast.literal_eval(input_files_arr)
                        a = f"{flag} '{json.dumps(input_files_arr).replace('"', '\\"')}'"
                    args.append(a)

                args = " ".join(args)

                # if hasattr(task, "files"):
                #     input_files = [f"{i.file_id}" for i in task.files if i.link == FileLink.INPUT]
                #     output_files = [f"{o.file_id}" for o in task.files if o.link == FileLink.OUTPUT]
                # else:
                input_files = [f"{i.file_id}" for i in task.input_files]
                dependency = [f"{p}.outputs" for p in self.task_parents[task.task_id]]
                if len(dependency) == 0:
                    dependency.append(f"get_parsl_files({input_files})")
                dependency = " + ".join(dependency)

                output_files = [f"{o.file_id}" for o in task.output_files]

                data_size = sum([int(f.size) for f in task.input_files] + [int(f.size) for f in task.output_files])

                computation = task.runtime

                if task.runtime == 0:
                    computation = cpu_work * percent_cpu

                resource_spec = {
                    "data_size": data_size,
                    "num_children": len(self.task_children[task.task_id]),
                    "computation": computation,
                    "bottom_level": self.bottom_level[task.task_id],
                    "task_name": task.task_id,
                }

                code = [
                    f"{task.task_id} = generic_shell_app(\"bin/{task.program} {args}\",",
                    f"                                 inputs={dependency},",
                    f"                                 outputs=get_parsl_files({output_files},",
                     "                                                         True),",
                    f"                                 stdout=\"logs/{task.task_id}_stdout.txt\",",
                    f"                                 stderr=\"logs/{task.task_id}_stderr.txt\",",
                    f"                                 parsl_resource_specification={resource_spec})",
                    f"task_arr.append({task.task_id})\n",
                ]

                codelines.extend(code)

        cleanup_code = [
            "print('Starting workflow...'",
            "start_time = time.perf_counter()",
            "barrier()",
            "",
            "try:",
            "    for task in task_arr:",
            "        task.result()",
            "except Exception as e:",
            "    print(f'A task failed to complete: {e}')",
            "    print(f'Find more details in {task.stdout} and {task.stderr}')",
            "    raise e",
            "else:",
            "    print('Workflow completed successfully')",
            "    print('Time Taken: ', time.perf_counter() - start_time)",
            "finally:",
            "    # Releasing all resources, and shutting down all executors and workers",
            "    parsl.dfk().cleanup()",
            "    parsl.clear()",
        ]

        codelines.extend(cleanup_code)

        return codelines


## NOTE: remove this in the end
def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "wfformat_file", help="path to WfFormat JSON input file")
    parser.add_argument("--outdir", default=pathlib.Path.cwd().joinpath("parsl_script"),
                        help="Output directory in which to store the translated files")

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    wf_input = args.wfformat_file
    outdir_path = args.outdir

    if not isinstance(outdir_path, pathlib.Path):
        outdir_path = pathlib.Path(outdir_path)

    try:
        instance = Instance(wf_input)
    except Exception as e:
        raise e

    workflow_obj = instance.workflow
    workflow_obj = instance.workflow

    translator = ParslTranslator(workflow_obj)

    translator.translate(output_folder=outdir_path)

    return 0


if __name__ == "__main__":
    main()
