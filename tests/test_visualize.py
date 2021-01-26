import os
import unittest
import neat
import random
import pandas as pd
import neatrader.visualize as vis
from neatrader.reporter import TradeReporter
from neatrader.model import Portfolio
from neatrader.utils import from_small_date
from neatrader.trading import Simulator
from neatrader.daterange import DateRangeFactory
from pathlib import Path
from utils import RandomNet, TSLA


def eval_genomes(genomes, config):
    for gnome_id, genome in genomes:
        genome.fitness = random.random() / 2
        genome.cv_fitness = random.random() / 3


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

    def test_plot_trades(self):
        net = RandomNet(5)
        reporter = TradeReporter()
        path = Path('tests') / 'test_data' / 'normalized' / TSLA.symbol
        portfolio = Portfolio(cash=0, securities={TSLA: 100})
        training = pd.read_csv(path / 'training.csv', parse_dates=['date'], date_parser=from_small_date)
        sim = Simulator(TSLA, portfolio, path, training, reporter)
        dr = DateRangeFactory(training).random_date_range(90)

        vis.plot_trades(net, sim, dr, training, path, reporter, False)
