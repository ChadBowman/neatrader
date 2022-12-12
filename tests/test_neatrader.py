import unittest
import os
from os.path import exists, join
from neatrader import neatrader
import shutil

local_dir = os.path.dirname(__file__)


def fake_eval_genomes(genomes, config):
    for genome_id, genome in genomes:
        genome.fitness = 1
        genome.cv_fitness = 1


class TestNeatrader(unittest.TestCase):
    def _get_checkpoint_path(self, number):
        return join(local_dir, "test_data", "checkpoints", f"neat-checkpoint-{number}")

    def test_checkpoint_removal(self):
        try:
            cwd = os.getcwd()
            shutil.copy(self._get_checkpoint_path(9), cwd)
            shutil.copy(self._get_checkpoint_path(10), cwd)
            shutil.copy(self._get_checkpoint_path(8), cwd)
            self.assertTrue(exists(join(cwd, "neat-checkpoint-8")))
            self.assertTrue(exists(join(cwd, "neat-checkpoint-9")))
            self.assertTrue(exists(join(cwd, "neat-checkpoint-10")))

            config_path = join(local_dir, 'test_configuration.ini')
            neatrader.eval_genomes = fake_eval_genomes
            neatrader.run(config_path, generations_per_iteration=1, iterations=1)

            self.assertFalse(exists(join(cwd, "neat-checkpoint-8")))
            self.assertFalse(exists(join(cwd, "neat-checkpoint-9")))
            self.assertTrue(exists(join(cwd, "neat-checkpoint-10")))
        finally:
            os.remove(join(cwd, "neat-checkpoint-10"))
