"""Run all jobs locally."""

import os
import shlex

import click
import dtoolcore

from analysis import Analysis


class SlurmRunner(object):

    def __init__(self, analysis, base_output_path):

        self.analysis = analysis

        base_output_path = os.path.abspath(base_output_path)
        self.base_output_path = base_output_path

        self.scripts_path = os.path.join(base_output_path, "scripts")
        dtoolcore.utils.mkdir_parents(self.scripts_path)

        self.logs_path = os.path.join(base_output_path, "logs")
        self.logs_relpath = os.path.relpath(
            self.logs_path,
            self.base_output_path
        )
        dtoolcore.utils.mkdir_parents(self.logs_path)

        self.master_script = ""

    def construct_single_process_template(self, identifier):

        variables = {
            "name": "autotest",
            "stdout": os.path.join(
                self.logs_relpath,
                "{}.out".format(identifier)
            ),
            "stderr": os.path.join(
                self.logs_relpath,
                "{}.err".format(identifier)
            ),
            "input_dataset_uri": self.analysis.input_dataset.uri,
            "output_dataset_uri": self.analysis.output_dataset.uri,
            "identifier": identifier,
        }

        slurm_template = self.analysis.config["slurm_run_template"]
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

        variables = {
            "name": "autotest",
            "stdout": os.path.join(self.logs_relpath, "freeze.out"),
            "stderr": os.path.join(self.logs_relpath, "freeze.err"),
            "output_dataset_uri": self.analysis.output_dataset.uri,
        }

        slurm_template = self.analysis.config["slurm_freeze_template"]
        script_contents = slurm_template.format(**variables)
        script_name = "freeze_dataset.slurm"
        script_fpath = os.path.join(self.scripts_path, script_name)
        script_relpath = os.path.relpath(script_fpath, self.base_output_path)

        with open(script_fpath, "w") as fh:
            fh.write(script_contents)

        master_script_line = "sbatch --dependency=singleton {}\n".format(
            script_relpath
        )
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

    analysis.initialise()

    for identifier in runner.analysis.identifiers_to_process:
        runner.process_single_identifier(identifier)

    runner.finalise()
    # analysis.finalise()

    # click.secho("Created: ", nl=False)
    # click.secho("{}".format(analysis.output_dataset.uri), fg='green')


if __name__ == '__main__':
    main()
