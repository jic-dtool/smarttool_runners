"""Run all jobs locally."""

import os
import shlex
import subprocess

import click
import dtoolcore

from analysis import Analysis


class SlurmRunner(object):

    def __init__(self, analysis, base_output_path):

        self.analysis = analysis
        self.command_base = analysis.config["tool_command_base"]

        base_output_path = os.path.abspath(base_output_path)
        self.base_output_path = base_output_path

        self.scripts_path = os.path.join(base_output_path, "scripts")
        dtoolcore.utils.mkdir_parents(self.scripts_path)

        self.logs_path = os.path.join(base_output_path, "logs")
        self.logs_relpath = os.path.relpath(self.logs_path, self.base_output_path)
        dtoolcore.utils.mkdir_parents(self.logs_path)

        self.master_script = ""

    def construct_single_process_command_list(self, identifier):

        command_as_list = shlex.split(self.tool_command_base)

        command_as_list += ['-d', self.analysis.input_dataset.uri]
        command_as_list += ['-o', self.analysis.output_dataset.uri]
        command_as_list += ['-i', identifier]

        return command_as_list

    def construct_single_process_template(self, identifier):

        command_as_list = self.construct_single_process_command_list(identifier)
        command_as_string = ' '.join(command_as_list)

        variables = {
            "name": "autotest",
            "command" : command_as_string,
            "stdout" : os.path.join(self.logs_relpath, "{}.out".format(identifier)),
            "stderr" : os.path.join(self.logs_relpath, "{}.err".format(identifier)),
        }

        slurm_template = self.analysis.config["slurm_template"]
        return slurm_template.format(**variables)


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
            "command" : freeze_command,
            "stdout" : os.path.join(self.logs_relpath, "freeze.out"),
            "stderr" : os.path.join(self.logs_relpath, "freeze.err"),
        }

        slurm_template = self.analysis.config["slurm_template"]
        script_contents = slurm_template.format(**variables)
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
