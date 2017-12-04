smarttool runners
=================

This repository contains smarttool runners - programs designed to take input
datasets and smartools and produce the scripts or directly execute commands
required to process the dataset.

Draft specification
-------------------

A smarttool runner has three main responsibilities:

1. Create the output dataset
2. Run the smarttool on the items in the input dataset
3. Freeze the output dataset once the smarttool has processed all the items in
   the input dataset

A smartool runner script takes as input a single YAML file specifying the input
dataset, the output base (the location where the output dataset will be
created), as well as any runner specific information required.

Below is an example YAML input file for the local smarttool runner.

.. code-block:: yaml

    input_dataset_uri: "data/todo_lists"
    output_dataset_base: "output"
    local_smarttool_fpath: "scripts/smarttool_runner.py"

Below is an example YAML input file for the SLURM smarttool runner, which
generates SLURM batch scripts for submitting jobs to the cluster.

.. code-block:: yaml

    input_dataset_uri: "irods:///jic_raw_data/rg-matthew-hartley/910d75a1-46f3-4772-8c9d-608f5a266a7f"
    output_dataset_base: "irods:///jic_overflow/rg-matthew-hartley"
    input_overlay_filter: "is_read1"
    slurm_run_template: |
      #!/bin/bash -e
      #SBATCH --partition=nbi-short
      #SBATCH --mem=2000
      #SBATCH --job-name={name}
      #SBATCH -o {stdout}
      #SBATCH -e {stderr}

      export BOWTIE2_REFERENCE=/nbi/Research-Groups/JIC/Matthew-Hartley/data_raw/irwin_bait_sequencing/bravo_exome_reference/data/bravo_v2
      singularity exec /jic/software/testing/align_seqs_bowtie2/0.1.0/align_seqs_bowtie2 python /scripts/smarttool_runner.py
    slurm_freeze_template: |
      #!/bin/bash -e
      #SBATCH --partition=nbi-short
      #SBATCH --mem=2000
      #SBATCH --job-name={name}
      #SBATCH -o {stdout}
      #SBATCH -e {stderr}

      /jic/software/testing/dtool/2.3.2/dtool freeze {output_dataset_uri}

The smarttool runner is also responsible for only running the smarttool on the
dataset items specified by the ``input_overlay_filter``. If the
``input_overlay_filter`` specified does not exist in the input dataset then the
smarttool runner will raise a ``RuntimeError``. However, initially this may be
the default ``KeyError`` raised by ``dtoolcore``.

The smarttool runner is also responsible for determining if the items from the
input dataset were processed successfully or not. If any data item failed to
process correctly the smarttool runner should not freeze the output dataset.
The smarttool runner should also provide an option for identify which item(s)
failed to process correctly and an option for re-processing the failed items.
Implementing this is non-trivial and these features will not be available in
the initial releases of these smarttool runners.
