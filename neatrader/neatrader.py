import math
import neat
import neatrader.visualize as vis
import os
import pandas as pd
import re
from glob import glob
from importlib import resources
from neatrader.daterange import DateRangeFactory
from neatrader.model import Portfolio, Security
from neatrader.reporter import TradeReporter
from neatrader.trading import Simulator
from neatrader.utils import from_small_date
from pathlib import Path
from time import perf_counter_ns

TSLA = Security("TSLA")


def find_data_path():
    path = None
    with resources.path("resources.data", "TSLA") as fp:
        path = Path(fp)
    return path


path = find_data_path()
training = pd.read_csv(path / "training.csv", parse_dates=['date'], date_parser=from_small_date)
validation = pd.read_csv(path / "cross_validation.csv", parse_dates=['date'], date_parser=from_small_date)
training_daterange_factory = DateRangeFactory(training)
cv_daterange_factory = DateRangeFactory(validation)
simulation_days = 90


def eval_genomes(genomes, config):
    # all genomes should be compared against using the same date range
    t_start, t_end = training_daterange_factory.random_date_range(simulation_days)
    c_start, c_end = cv_daterange_factory.random_date_range(simulation_days)

    for genome_id, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        portfolio = Portfolio(cash=0.0, securities={TSLA: 100})
        training_sim = Simulator(TSLA, portfolio, path, training)

        genome.fitness = training_sim.simulate(net, t_start, t_end)
        genome.cv_fitness = 0  # TODO evaluate in a different place? Once per generation?


def find_checkpoints():
    return sorted(
        glob('neat-checkpoint-*'),
        key=lambda name: int(re.search(r"(\d+)", name).group(1)),
        reverse=True
    )


def cleanup_checkpoints():
    checkpoints = find_checkpoints()
    # keep the most recent one
    for checkpoint in checkpoints[1:]:
        os.remove(checkpoint)


def run(config_file, generations_per_iteration, iterations=math.inf):
    print(f"running with {generations_per_iteration} generations per iteration for {iterations} iterations")
    try:
        config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            config_file
        )
        days_simulated = 0
        duration_ns = 0.0

        i = 0
        while i < iterations:
            checkpoint = find_checkpoints()
            if checkpoint:
                pop = neat.Checkpointer.restore_checkpoint(checkpoint[0])
            else:
                pop = neat.Population(config)

            stats = neat.StatisticsReporter()

            # add a stdout reporter to show progress in terminal
            pop.add_reporter(neat.StdOutReporter(True))
            pop.add_reporter(stats)
            pop.add_reporter(neat.Checkpointer(generations_per_iteration))

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
            portfolio = Portfolio(cash=0.0, securities={TSLA: 100})
            reporter = TradeReporter()
            simulator = Simulator(TSLA, portfolio, path, training, reporter)
            daterange = training_daterange_factory.random_date_range(90)
            vis.plot_trades(win_net, simulator, daterange, training, path, reporter, view=view)
            print(f"\nWinner simulation:\nfitness: {reporter.fitness:.2f}")
            print(f"trades:")
            for trade in reporter.row_list:
                print(trade)
            print(f"\nending portfolio:\n{portfolio}")

            # plot the network
            node_names = {
                -1: "cash", -2: "shares", -3: "held option value", -4: "10 day iv", -5: "30 day iv", -6: "RSI",
                #-4: "close", -5: "macd", -6: "macd_signal", -7: "macd_diff",
                #-8: "bb_bbm", -9: "bb_bbh", -10: "bb_bbl", -11: "rsi", -12: "30 day IV",
                0: "open", 1: "close", 2: "hold", 3: "strike", 4: "expiration"
            }
            vis.draw_net(
                config, winner, view=view, node_names=node_names,
                filename="neural_net", prune_unused=False, show_disabled=False
            )

            days_simulated += len(pop.population) * simulation_days * generations_per_iteration * 2
            duration_ns += end - start
            duration_min = duration_ns / 1000 / 1000 / 1000 / 60
            sim_years = days_simulated / 365
            print(f"\nSimulated {days_simulated} days in {duration_min:.2f} minutes",
                  f"({sim_years / duration_min:.2f} sim years per minute)")
            i += 1
            cleanup_checkpoints()
    finally:
        cleanup_checkpoints()
