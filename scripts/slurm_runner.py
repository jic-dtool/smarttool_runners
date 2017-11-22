"""Run all jobs locally."""

import os
import shlex
import subprocess

import click
import dtoolcore

from analysis import Analysis

SLURM_TEMPLATE = """#!/bin/bash
#SBATCH --partition=nbi-short
#SBATCH --mem=2000
#SBATCH --job-name={name}
#SBATCH -o {stdout}
#SBATCH -e {stderr}

export BOWTIE2_REFERENCE={bowtie2_reference}
{command}
"""

TOOL_COMMAND_BASE = 'singularity exec /jic/software/testing/align_seqs_bowtie2/0.1.0/align_seqs_bowtie2 python /scripts/smarttool_runner.py'
BOWTIE2_REFERENCE = '/nbi/Research-Groups/JIC/Matthew-Hartley/data_raw/irwin_bait_sequencing/bravo_exome_reference/data/bravo_v2'

class SlurmRunner(object):

    def __init__(self, analysis, base_output_path):

        self.analysis = analysis
        self.command_base = TOOL_COMMAND_BASE

        base_output_path = os.path.abspath(base_output_path)
        self.base_output_path = base_output_path

        self.scripts_path = os.path.join(base_output_path, "scripts")
        dtoolcore.utils.mkdir_parents(self.scripts_path)

        self.logs_path = os.path.join(base_output_path, "logs")
        self.logs_relpath = os.path.relpath(self.logs_path, self.base_output_path)
        dtoolcore.utils.mkdir_parents(self.logs_path)

        self.master_script = ""

    def construct_single_process_command_list(self, identifier):

        command_as_list = shlex.split(TOOL_COMMAND_BASE)

        command_as_list += ['-d', self.analysis.input_dataset.uri]
        command_as_list += ['-o', self.analysis.output_dataset.uri]
        command_as_list += ['-i', identifier]

        return command_as_list

    def construct_single_process_template(self, identifier):

        command_as_list = self.construct_single_process_command_list(identifier)
        command_as_string = ' '.join(command_as_list)

        variables = {
            "name": "autotest",
            "bowtie2_reference" : BOWTIE2_REFERENCE,
            "command" : command_as_string,
            "stdout" : os.path.join(self.logs_relpath, "{}.out".format(identifier)),
            "stderr" : os.path.join(self.logs_relpath, "{}.err".format(identifier)),
        }

        return SLURM_TEMPLATE.format(**variables)


    def process_single_identifier(self, identifier):

        script_contents = self.construct_single_process_template(identifier)
        script_name = "process_{}.slurm".format(identifier)
        script_fpath = os.path.join(self.scripts_path, script_name)
        script_relpath = os.path.relpath(script_fpath, self.base_output_path)

        with open(script_fpath, "w") as fh:
            fh.write(script_contents)

        master_script_line = "sbatch {}\n".format(script_relpath)
        self.master_script += master_script_line

    def finalise(self):
        freeze_command = "dtool freeze {}".format(self.analysis.output_dataset.uri)

        variables = {
            "name": "autotest",
            "bowtie2_reference" : BOWTIE2_REFERENCE,
            "command" : freeze_command,
            "stdout" : os.path.join(self.logs_relpath, "freeze.out"),
            "stderr" : os.path.join(self.logs_relpath, "freeze.err"),
        }

        script_contents = SLURM_TEMPLATE.format(**variables)
        script_name = "freeze_dataset.slurm"
        script_fpath = os.path.join(self.scripts_path, script_name)
        script_relpath = os.path.relpath(script_fpath, self.base_output_path)

        with open(script_fpath, "w") as fh:
            fh.write(script_contents)

        master_script_line = "sbatch --dependency=singleton {}\n".format(script_relpath)
        self.master_script += master_script_line

        master_script_fpath = os.path.join(self.base_output_path, "runme.sh")
        with open(master_script_fpath, "w") as fh:
            fh.write(self.master_script)


@click.command()
@click.argument('analysis_fpath')
@click.argument('output_path')
def main(analysis_fpath, output_path):

    analysis = Analysis(analysis_fpath)
    runner = SlurmRunner(analysis, output_path)

    # analysis.initialise()

    for identifier in runner.analysis.identifiers_to_process:
        runner.process_single_identifier(identifier)

    runner.finalise()
    # analysis.finalise()

    # click.secho("Created: ", nl=False)
    # click.secho("{}".format(analysis.output_dataset.uri), fg='green')


if __name__ == '__main__':
    main()
