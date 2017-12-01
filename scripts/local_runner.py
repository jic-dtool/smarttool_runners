"""Run all jobs locally."""

import shlex
import subprocess

import click

from analysis import Analysis


class LocalRunner(object):

    def __init__(self, analysis):

        self.analysis = analysis
        self.command_base = "python {}".format(
            self.analysis.config["smarttool"]
        )

    def construct_single_process_command(self, identifier):

        command_as_list = shlex.split(self.command_base)

        command_as_list += ['-d', self.analysis.input_dataset.uri]
        command_as_list += ['-o', self.analysis.output_dataset.uri]
        command_as_list += ['-i', identifier]

        return command_as_list

    def process_single_identifier(self, identifier):

        run_command = self.construct_single_process_command(identifier)
        subprocess.call(run_command)


@click.command()
@click.argument('analysis_fpath')
def main(analysis_fpath):

    analysis = Analysis(analysis_fpath)
    runner = LocalRunner(analysis)

    analysis.initialise()

    for identifier in runner.analysis.identifiers_to_process:
        runner.process_single_identifier(identifier)

    analysis.finalise()

    click.secho("Created: ", nl=False)
    click.secho("{}".format(analysis.output_dataset.uri), fg='green')

if __name__ == '__main__':
    main()
