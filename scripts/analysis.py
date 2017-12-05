try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import click
import yaml
import dtoolcore

from dtool_cli.cli import (
    CONFIG_PATH
)


def create_derived_dataset(
    parent_dataset,
    dest_location_uri,
    name_template
):

    parsed_location_uri = urlparse(dest_location_uri)
    prefix = parsed_location_uri.path
    storage = parsed_location_uri.scheme
    if storage == "":
        storage = "file"

    dest_dataset_name = name_template.format(parent_dataset.name)

    admin_metadata = dtoolcore.generate_admin_metadata(dest_dataset_name)
    dest_dataset = dtoolcore.generate_proto_dataset(
        admin_metadata=admin_metadata,
        prefix=prefix,
        storage=storage,
        config_path=CONFIG_PATH)
    try:
        dest_dataset.create()
    except dtoolcore.storagebroker.StorageBrokerOSError as err:
        raise click.UsageError(str(err))

    return dest_dataset


def identifiers_where_overlay_is_true(dataset, overlay_name):

    overlay = dataset.get_overlay(overlay_name)

    selected = [identifier
                for identifier in dataset.identifiers
                if overlay[identifier]]

    return selected


class Analysis(object):

    def __init__(self, analysis_file='analysis.yml'):

        with open(analysis_file) as fh:
            self.config = yaml.load(fh)

        self._input_dataset = None
        self._output_dataset = None
        self._resource_dataset = None

    @property
    def input_dataset(self):
        if self._input_dataset is None:
            self._input_dataset = dtoolcore.DataSet.from_uri(
                self.config['input_dataset_uri']
            )
        return self._input_dataset

    @property
    def output_dataset(self):
        if self._output_dataset is None:
            self._output_dataset = dtoolcore.ProtoDataSet.from_uri(
                self.config['output_dataset_uri']
            )
        return self._output_dataset

    @property
    def identifiers_to_process(self):

        if 'input_filter' in self.config:
            id_filter = self.config['input_filter']
            return identifiers_where_overlay_is_true(
                self.input_dataset,
                id_filter
            )
        else:
            return self.input_dataset.identifiers

    def initialise(self):

        output_uri_base = self.config['output_dataset_base']

        output_ds = create_derived_dataset(
            self.input_dataset,
            output_uri_base,
            "{}_alignments"
        )

        self._output_dataset = output_ds

    def finalise(self):

        readme_content = self.input_dataset.get_readme_content()
        readme_content += "\nderived_from_UUID: {}".format(
            self.input_dataset.uuid
        )
        readme_content += "\nderived_from_URI: '{}'".format(
            self.input_dataset.uri
        )

        self.output_dataset.put_readme(readme_content)

        self.output_dataset.freeze()
