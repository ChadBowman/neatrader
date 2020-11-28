import os
import neat
import csv
import visualize

tsla = []
with open("TSLA_ta.csv", "r") as file:
    for row in csv.reader(file):
        close = float(row[2])
        macd = float(row[3])
        signal = float(row[4])
        diff = float(row[5])
        tsla.append({
            "close": close, "macd": macd, "signal": signal, "diff": diff
        })


def simulate(net, initial_fitness):
    holdings = 1
    cash = 0
    for day in tsla:
        close = day["close"]
        macd = day["macd"]
        signal = day["signal"]
        diff = day["diff"]

        buy, hold, sell = net.activate((holdings, macd, signal, diff))

        print(sell)
        if buy > hold and buy > sell:
            if holdings == 0:
                cash -= close
                holdings += 1
        if sell > hold and sell > buy:
            if holdings == 1:
                cash += close
                holdings -= 1

    value = cash + (holdings * close)
    return value - initial_fitness


def eval_genomes(genomes, config):
    for genome_id, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        genome.fitness = simulate(net, 555.38)


def run(config_file):
    config = neat.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_file
    )

    # crete population, which is the top-level object for a NEAT run
    pop = neat.Population(config)
    # add a stdout reporter to show progress in terminal
    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    pop.add_reporter(neat.Checkpointer(5))

    # run for up to 500 generations
    winner = pop.run(eval_genomes, 10000)

    # display the winning genome
    print(f"\nBest genome:\n{winner}")

    win_net = neat.nn.FeedForwardNetwork.create(winner, config)
    holdings = 1
    cash = 0
    for day in tsla:
        close = day["close"]
        macd = day["macd"]
        signal = day["signal"]
        diff = day["diff"]

        buy, hold, sell = win_net.activate((holdings, macd, signal, diff))

        if buy > hold and buy > sell:
            if holdings == 0:
                cash -= close
                holdings += 1
                print(f"bought at {close}, total: {cash + (holdings * close)}")
        if sell > hold and sell > buy:
            if holdings == 1:
                cash += close
                holdings -= 1
                print(f"sold at {close}, total: {cash + (holdings * close)}")

    visualize.draw_net(config, winner, True)
    visualize.plot_stats(stats, ylog=False, view=True)
    visualize.plot_species(stats, view=True)


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.ini')
    run(config_path)
