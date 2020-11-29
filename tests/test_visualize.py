import os
import unittest
import neat
import random
import neatrader.visualize as vis


def eval_genomes(genomes, config):
    for gnome_id, genome in genomes:
        genome.fitness = random.random() / 2
        genome.cv_fitness = random.random() / 2


class TestVisualize(unittest.TestCase):

    def load_pop(self):
        local_dir = os.path.dirname(__file__)
        config_path = os.path.join(local_dir, 'test_configuration.ini')
        config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            config_path
        )
        return neat.Population(config)

    def test_plot_without_crossover(self):
        def eval_genomes(genomes, config):
            for gnome_id, genome in genomes:
                genome.fitness = random.random() / 2
        pop = self.load_pop()
        stats = neat.StatisticsReporter()
        pop.add_reporter(stats)
        pop.run(eval_genomes, 10)
        vis.plot_stats(stats, view=False)

    def test_plot_with_crossover(self):
        pop = self.load_pop()
        stats = neat.StatisticsReporter()
        pop.add_reporter(stats)
        pop.run(eval_genomes, 10)
        vis.plot_stats(stats, view=False)
