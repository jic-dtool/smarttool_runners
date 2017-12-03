all: test_local_runner test_slurm_runner
test_local_runner:
	. ../env/bin/activate
	python ../scripts/local_runner.py analysis.yml
test_slurm_runner:
	. ../env/bin/activate
	mkdir -p output/slurm_runner
	dtool create -q test_slurm_runner output/slurm_runner
	python ../scripts/slurm_runner.py analysis.yml output/slurm_runner
clean:
	rm -rf output/*
