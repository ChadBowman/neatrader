import os
import neat
import pandas as pd
import numpy as np
from neatrader.model import Portfolio, Security
from neatrader.trading import TradingEngine
from neatrader.preprocess import CsvImporter
from datetime import datetime


def simulate(net):
    tsla = Security('TSLA')
    # start with 100 shares
    port = Portfolio(cash=0, securities={tsla: 100})
    engine = TradingEngine([port])
    df = pd.read_csv('normalized/TSLA/ta.csv', parse_dates=['date'])
    port = engine.portfolios[0]

    for idx, row in df.iterrows():
        date = row['date'].strftime('%y%m%d')
        close = row['close']
        macd = row['macd']
        macd_signal = row['macd_signal']
        macd_diff = row['macd_diff']
        bb_bbm = row['bb_bbm']
        bb_bbh = row['bb_bbh']
        bb_bbl = row['bb_bbl']
        rsi = row['rsi']

        # TODO add held option delta/theta, maybe price?, maybe vega?
        params = (close, macd, macd_signal, macd_diff, bb_bbm, bb_bbh, bb_bbl, rsi)

        # BUY SELL HOLD
        if not np.isnan(params).any():
            chain = CsvImporter().parse_chain(row['date'], tsla, f"normalized/TSLA/chains/{date}.csv")
            buy, sell, hold, delta, theta = net.activate(params)
            #print(f"activation, buy: {buy}, sell: {sell}, hold: {hold}, delta: {delta}, theta: {theta}")
            if hold > buy and hold > sell:
                continue
            elif buy > sell and buy > hold:
                # only covered calls are supported right now so this means close the position
                if port.contracts():
                    contract = next(iter(port.contracts().keys()))
                    new_price = chain.get_price(contract)
                    try:
                        print(f"closing {contract}")
                        engine.buy_contract(port, contract, new_price)
                    except Exception as e:
                        print(e)
            else:
                if not port.contracts():
                    # sell a new contract
                    contract = chain.search(delta=delta, theta=theta)
                    try:
                        print(f"selling {contract}")
                        engine.sell_contract(port, contract, contract.price)
                    except Exception as e:
                        print(e)

        # process assignments, expirations
        engine.eval({tsla: close}, datetime.strptime(date, '%y%m%d'))

    option_cv = 0
    if port.contracts():
        option_cv = next(iter(port.contracts().keys())).price
    stock_cv = 0
    if port.stocks():
        stock_cv = close * 100
    cv = port.cash + option_cv + stock_cv
    scales = pd.read_csv('normalized/TSLA/scales.csv', index_col=0)
    mn = scales.loc['close', 'min']
    mx = scales.loc['close', 'max']
    de_norm = (cv * (mx - mn)) + mn
    print(f"FIT: {de_norm}")
    return de_norm


def eval_genomes(genomes, config):
    for genome_id, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        genome.fitness = simulate(net)


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
    pop.add_reporter(neat.Checkpointer(500, 60 * 60, 'neatrader-checkpoint-'))
    pop.add_reporter(stats)

    winner = pop.run(eval_genomes, 10000)

    # display the winning genome
    print(f"\nBest genome:\n{winner}")

    win_net = neat.nn.FeedForwardNetwork.create(winner, config)


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.ini')
    run(config_path)
