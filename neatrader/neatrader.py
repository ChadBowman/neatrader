import neat
import pandas as pd
from glob import glob
import neatrader.visualize as vis
from neatrader.model import Portfolio, Security
from neatrader.trading import Simulator
from neatrader.daterange import DateRangeFactory
from neatrader.utils import from_small_date
from neatrader.reporter import TradeReporter
from pathlib import Path
from multiprocessing import Process, Manager


TSLA = Security('TSLA')
path = Path('normalized') / TSLA.symbol
training = pd.read_csv(path / 'training.csv', parse_dates=['date'], date_parser=from_small_date)
validation = pd.read_csv(path / 'cross_validation.csv', parse_dates=['date'], date_parser=from_small_date)
training_daterange_factory = DateRangeFactory(training)
cv_daterange_factory = DateRangeFactory(validation)


def worker(mode, simulator, net, start, end, return_dict):
    return_dict[mode] = simulator.simulate(net, start, end)


def eval_genomes(genomes, config):
    # all genomes should be compared against using the same date range
    t_start, t_end = training_daterange_factory.random_date_range(90)
    c_start, c_end = cv_daterange_factory.random_date_range(90)
    return_dict = Manager().dict()

    for genome_id, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        portfolio = Portfolio(cash=0, securities={TSLA: 100})
        t_sim = Simulator(TSLA, portfolio, path, training)
        c_sim = Simulator(TSLA, portfolio, path, validation)

        train_p = Process(target=worker, args=('training', t_sim, net, t_start, t_end, return_dict))
        validation_p = Process(target=worker, args=('validation', c_sim, net, c_start, c_end, return_dict))
        train_p.start()
        validation_p.start()
        train_p.join()
        validation_p.join()

        genome.fitness = return_dict['training']
        genome.cv_fitness = return_dict['validation']


def run(config_file):
    config = neat.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_file
    )

    while True:
        checkpoint = sorted(glob('neat-checkpoint-*'), reverse=True)
        if checkpoint:
            pop = neat.Checkpointer.restore_checkpoint(checkpoint[0])
        else:
            pop = neat.Population(config)

        stats = neat.StatisticsReporter()

        # add a stdout reporter to show progress in terminal
        pop.add_reporter(neat.StdOutReporter(True))
        pop.add_reporter(stats)
        pop.add_reporter(neat.Checkpointer(50))

        winner = pop.run(eval_genomes, 50)

        # display the winning genome
        print(f"\nBest genome:\n{winner}")

        win_net = neat.nn.FeedForwardNetwork.create(winner, config)

        view = False
        vis.plot_stats(stats, ylog=False, view=view)
        vis.plot_species(stats, view=view)

        portfolio = Portfolio(cash=0, securities={TSLA: 100})
        simulator = Simulator(TSLA, portfolio, path, training)
        daterange = training_daterange_factory.random_date_range(90)
        reporter = TradeReporter()
        vis.plot_trades(win_net, simulator, daterange, training, path, reporter, view=view)

        node_names = {0: 'Buy', 1: 'Sell', 2: 'Hold', 3: 'Delta', 4: 'Theta'}
        vis.draw_net(config, winner, view=view, node_names=node_names)
