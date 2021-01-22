import neat
from neatrader.model import Portfolio, Security
from neatrader.trading import Simulator
from datetime import datetime
from pathlib import Path


TSLA = Security('TSLA')


def eval_genomes(genomes, config):
    for genome_id, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        portfolio = Portfolio(cash=0, securities={TSLA: 100})
        sim = Simulator(TSLA, portfolio, Path('normalized/TSLA'))

        genome.fitness = sim.simulate(net, duration=90)


def run(config_file):
    config = neat.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_file
    )

    # create population, which is the top-level object for a NEAT run
    pop = neat.Population(config)
    stats = neat.StatisticsReporter()

    # add a stdout reporter to show progress in terminal
    pop.add_reporter(neat.StdOutReporter(True))
    pop.add_reporter(neat.Checkpointer(10, 60, 'neatrader-checkpoint-'))
    pop.add_reporter(stats)

    winner = pop.run(eval_genomes, )

    # display the winning genome
    print(f"\nBest genome:\n{winner}")

    win_net = neat.nn.FeedForwardNetwork.create(winner, config)
