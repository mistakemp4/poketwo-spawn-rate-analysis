# Pokétwo Spawn Rates

This project analyzes the public data behind the Pokétwo Discord bot to show how wild spawns are chosen. Spawns are a weighted random draw, so the goal is to break those weights down and find what makes a species common or rare.

---

## Project highlights

* Derived evolution stage and rarity class for 1,322 catchable species from raw evolution links
* Broke down spawn share by class, region, type, and weight tier
* Estimated how many spawns (and messages) it takes to see a Legendary, Mythical, or Ultra Beast
* Fit linear and Lasso regression on log2 weight, validation R² of about 0.82
* Built a logistic regression rare spawn classifier with threshold analysis
* Compared a decision tree and a random forest against the linear models with 5-fold cross-validation
* Used permutation importance to see which attributes the forest relies on

## Files

* `poketwo_spawn_rate_analysis.ipynb`: the analysis notebook
* `data/pokemon.csv`: from https://github.com/poketwo/data (`csv/pokemon.csv`)
* `data/spawn_lookup.json`: per-species export written by the notebook, for a lookup tool
* `assets/`: chart font, see Credits
* `export_site.py`: copies the notebook, figures and lookup data into my website repo

## Note

The live bot loads its data from a private repository, so production weights may differ from the public CSV used here.

## Credits

* Chart font is VT323, under the SIL Open Font License, see `assets/VT323-OFL.txt`
