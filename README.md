# OpenNIR - Lifelong Learning

This is an adaptation of OpenNIR to work in a Lifelong Learning framework, to analyze the presence of the 
Catastrophic Forgetting phenomenon in a neural ad-hoc ranking


## Quickstart

To install OpenNIR and download/setup the datasets please refer to the [source](https://github.com/Georgetown-IR-Lab/OpenNIR).

Setup a configuration (models + dataset sequence). Under `config/catastrophic_forgetting/configX`.

For example, to setup a dataset sequence CORD19 + MSMarco, working with 3 models (DRMM, VBERT, and CEDR),
we create the following file:

```bash
dataset=cord19
dataset=msmarco
model=drmm
model=vbert
model=cedr
```

We must create the `script_evals` and `output` folders, then, we execute the command:
```bash
python -m onir.bin.catfog config/catastrophic_forgetting/file
```


This will generate the script files to work in the `script_evals` folder. 

Parameters can be changed in the `onir/bin/catfog.py` file and the generated scripts.

### The catfog.py file

We can choose whether we can work with the classical pipeline (called `catfog`) or applying an EWC strategy.

In the first lines, we choose which pipeline we want to use.

Please note that, if we are using the `catfog` pipeline, we must select the default `pairwise` trainer in the `trainers/base.py` file, and `pairwise_ewc` if we are using the `EWC` pipeline.



Models, datasets, and vocabularies will be saved in `~/data/onir/`. This can be overridden by
setting `data_dir=~/some/other/place/` as a command-line argument, in a configuration file, or in
the `ONIR_ARGS` environment variable.


## Features

### Datasets

In addition of the default datasets from OpenNIR, we added the following ones:
 - CORD19: `config/cord19`
 - Microblog `config/microblog`

Moreoften, we included classes to work with mixed datasets (in this case MSMarco, CORD19 and Microblog)
 - MSMarco + CORD19: `config/mixmscord`
 - MSMarco + Microblog: `config/mixmsmb`
 - MSMarco + CORD19 + Microblog: `config/mixmsmbcord`



## Citing

For further details of this setup, please refer to the paper:

```
@InProceedings{lovon:ecir2021-catfog,
  author = {Jesús Lovón-Melgarejo, Laure Soulier, Karen Pinel-Sauvagnat and Lynda Tamine},
  title = {Studying the Catastrophic Forgetting Problem in Neural Ranking Models},
  year = {2021},
  booktitle = {Advances in  Information Retrieval},
  pages={375--390}
}
```
 
## Acknowledgements
We would like to thank projects ANR COST (ANR-18-CE23-0016) and ANR JCJC SESAMS (ANR-18- CE23-0001) for supporting this work
