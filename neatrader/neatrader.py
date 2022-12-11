import neat
import pandas as pd
import os
from glob import glob
import neatrader.visualize as vis
from neatrader.model import Portfolio, Security
from neatrader.trading import Simulator
from neatrader.daterange import DateRangeFactory
from neatrader.utils import from_small_date
from neatrader.reporter import TradeReporter
from pathlib import Path
from multiprocessing import Process, Manager
from importlib import resources
from time import perf_counter_ns

TSLA = Security('TSLA')


def find_normalized_directory_path():
    path = None
    with resources.path("resources.normalized", "TSLA") as fp:
        path = Path(fp)
    return path


path = find_normalized_directory_path()
training = pd.read_csv(path / "training.csv", parse_dates=['date'], date_parser=from_small_date)
validation = pd.read_csv(path / "cross_validation.csv", parse_dates=['date'], date_parser=from_small_date)
training_daterange_factory = DateRangeFactory(training)
cv_daterange_factory = DateRangeFactory(validation)
simulation_days = 90


def worker(mode, simulator, net, start, end, return_dict):
    return_dict[mode] = simulator.simulate(net, start, end)


def eval_genomes(genomes, config):
    # all genomes should be compared against using the same date range
    t_start, t_end = training_daterange_factory.random_date_range(simulation_days)
    c_start, c_end = cv_daterange_factory.random_date_range(simulation_days)
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
    try:
        config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            config_file
        )
        generations_per_iteration = 3
        days_simulated = 0
        duration_ns = 0.0

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
            pop.add_reporter(neat.Checkpointer(1))

            start = perf_counter_ns()
            winner = pop.run(eval_genomes, generations_per_iteration)
            end = perf_counter_ns()

            # display the winning genome
            print(f"\nBest genome:\n{winner}")

            win_net = neat.nn.FeedForwardNetwork.create(winner, config)

            # plot species
            view = False
            vis.plot_stats(stats, ylog=False, view=view)
            vis.plot_species(stats, view=view)

            # simulate the winning network one time for a trades plot
            portfolio = Portfolio(cash=0, securities={TSLA: 100})
            simulator = Simulator(TSLA, portfolio, path, training)
            daterange = training_daterange_factory.random_date_range(90)
            reporter = TradeReporter()
            vis.plot_trades(win_net, simulator, daterange, training, path, reporter, view=view)

            # plot the network
            node_names = {
                -1: 'cash', -2: 'shares',  -3: 'close', -4: 'macd', -5: 'macd_signal',
                -6: 'macd_diff', -7: 'bb_bbh', -8: 'bb_bbh', -9: 'bb_bbl', -10: 'rsi',
                0: 'Buy', 1: 'Sell', 2: 'Hold', 3: 'Delta', 4: 'Theta'
            }
            vis.draw_net(config, winner, view=view, node_names=node_names)

            days_simulated += len(pop.population) * simulation_days * generations_per_iteration * 2
            duration_ns += end - start
            duration_min = duration_ns / 1000 / 1000 / 1000 / 60
            sim_years = days_simulated / 365
            print(f"Simulated {days_simulated} days in {duration_min:.2f} minutes",
                  f"({sim_years / duration_min:.2f} sim years per minute)")
    finally:
        checkpoints = sorted(glob('neat-checkpoint-*'), reverse=True)
        for checkpoint in checkpoints[1:]:
            os.remove(checkpoint)
