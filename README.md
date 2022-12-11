# Neatrader 💸

Autonomous stock options trader powered by NEAT (Neuroevolution of Augmented Topologies)

**This repo is no longer actively developed or maintained.** It was a way for me to experiment with my favorite machine learning algorithm and get some experience building a larger python project. I still think the underlying hypothesis is plausible in the limit of time and compute, but due to performance reasons I would rather use a modern machine learning framework, multiple neural networks for separate distinct tasks, and better high-level design.

## Hypothesis
Instead of trying to predict the direction of the market like most traders, we can take a different approach by providing traders with opportunities to place bets. By using machine learning to manage risk, we can essentially become the "casino" and aim to outperform the market through many small, contra-bets. Paradoxically, if markets are efficient enough, we should not expect to do any better so a positive result would be surprising.

Stock options are the perfect instrument for this experiment due to the market being two-sided and zero-sum. There is also a very distinct trade-off between probability of profit and payout, depending on what strikes and expirations are chosen.

## Fitness
Fitness is determined by calculating the total portfolio value vs the value of a buy-and-hold strategy at the end of the simulation period.

## Network
By default, networks are not initially connected. Connections and new nodes must arise via mutations over time. The probabilities of forming new connections and nodes are greater than the probability of their removal.

The current inputs and outputs are present:
Inputs:
 - portfolio cash
 - portfolio shares,
 - closing (end of day) price of security
 - MACD (moving average convergence/divergence)
 - MACD signal
 - MACD difference
 - Bollinger Bands mid
 - Bollinger Bands high
 - Bollinger Bands low
 - RSI (relative strength index)

Outputs:
 - Buy (currently means buyback/close short options position)
 - Hold (do nothing)
 - Sell (currently means open new short options position)
 - Delta (only used when opening new option to determine strike)
 - Theta (only used when opening new option to determine expiration)

## Simulation
Each agent (12 in each population) is given 100 shares of TSLA to start and ran through a random, 90 day period from the training set. Concurrently, a completely separate dataset is used to run a cross-validation simulation. The cross-validation fitness has no impact on NEAT and is used to gauge overfitting.

An agent can only open and close a single covered-call. A covered-call is when one sells to open an options contract using their owned shares as collateral.

Only the closing prices are considered so agents may only place one trade per day. Low-frequency trading is the goal.

## Data processing
Data was sourced using [Thomas Yeng's etrade cache](https://drive.google.com/drive/folders/1a7afPF3k-I0kjA3aybJWR1-rIQTNK_ef?usp=share_link). The `neatrader.preprocess` module was created for importing and normalizing these data into csv files, which are then exported to the `resources` module.

## Installation
### Docker
soon

### Local
First, clone `neatrader` and `neat-python`:
```
git clone git@github.com:ChadBowman/neatrader.git ~/neatrader
git clone git@github.com:ChadBowman/neat-python.git ~/neat-python
```

Create a virtual environment and install `neat-python`:
```
python3 -m venv ~/neatrader/env && source ~/neatrader/env/bin/activate
python3 -m pip install --upgrade pip ~/neat-python
```

Install `neatrader`:
```
python3 -m pip install -e ~/neatrader
```

## Execution

### Docker
soon

### Local
```
python3 -m neatrader
```

## Results
Generational performance is continually printed to the output. After every 3 generations, plots are created which give visual representation to the winning network, population species, average/best fitness, and the winning agent's simulated trades for a new random, 90 day period. Unfortunately, the species and fitness graphs are not that interesting due to only having 3 generations per iteration. Increase this number if you want to see this improved and leverage other functionalities from NEAT.

Here are some examples:

![network plot](https://github.com/ChadBowman/neatrader/blob/master/imgs/Digraph.gv.svg.png?raw=true)

![average/best fitness](https://github.com/ChadBowman/neatrader/blob/master/imgs/avg_fitness.svg?raw=true)

![speciation](https://github.com/ChadBowman/neatrader/blob/master/imgs/speciation.svg?raw=true)

![trades](https://github.com/ChadBowman/neatrader/blob/master/imgs/trades.svg?raw=true)
