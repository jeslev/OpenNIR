import onir
import sys
from pathlib import Path
import shlex
import subprocess
import os


pipeline = "jesus"
pipeline = "ewc"

output_dir = "results"
output_dir = "results_ewc"

_BERT_MODEL_PARAMS="trainer.grad_acc_batch=1 valid_pred.batch_size=4 test_pred.batch_size=4"

models_ranker = {
	"drmm" : "ranker=drmm",
	"pacrr" : "ranker=pacrr",
	"knrm" : "ranker=knrm",
	"vbert" : "config/vanilla_bert "+_BERT_MODEL_PARAMS,
	"cedr" : "config/cedr/knrm "+_BERT_MODEL_PARAMS
}

models_gpu = {
	"drmm":"0",
	"pacrr":"0",
	"knrm":"0",
	"vbert":"2",
	"cedr":"2"
}

pivot_gpu = None
pivot_gpu = "3" # to send some test to free gpu

datasets_training = {
	"msmarco":"msmarco_train_bm25_k1-0.82_b-0.68.100_mspairs",
	"cord19":"covid_trf2-rnd5-quest_bm25_k1-3.9_b-0.55.1000_2020-07-16_bs-text_2020filter_bsoverride-rnd5-query_rr-title_abs",
	"microblog":"microblog_train_bm25_k1-0.2_b-0.95.100"
}

config_dataset = {
	"msmarco":"config/msmarco",
	"cord19":"config/covidj/fold2",
	"microblog":"config/microblog"
}

config_test_dataset = {
	"msmarco":"config/msmarco/judgeddev",
	"cord19":"config/covidj/test2",
	"microblog":"config/microblog/test"
}

_config_name=""

datafolder = "/home/jlovon/workspace/data"
#datafolder = "../data"

def parse_args(arg_iter, cd=None):
	for arg in arg_iter:
	    if '=' in arg:
	        # assignment, i.e., key=value
	        key, value = arg.split('=', 1)
	        yield key, value
	    elif arg == '###':
	        # stop reading args once ### is encountered. This is useful when using argparse or
	        # similar in addition to or instead of this argument parsing mechanism.
	        break
	    else:
	        # reference to file, i.e., config/something
	        path = Path(arg if cd is None else os.path.join(cd, arg))
	        while path.is_dir():
	            path = path / '_dir'
	        global _config_name
	        _config_name = path.name
	        if not path.exists():
	            raise FileNotFoundError(f'configuraiton file not found: {path}')
	        with open(path, 'rt') as f:
	            yield from parse_args(shlex.split(f.read()), path.parent)

def main():

	params = dict()
	for key, value in parse_args(sys.argv[1:]):
		params.setdefault(key,[]).append(value)


	# We assumed dataset are init. For that, see scripts_init_dataset.sh
	datasets = params['dataset']
	models = params['model']

	modelspace=_config_name


	old_ranker = models_ranker['cedr']
	models_ranker['cedr'] = old_ranker + f" vocab.bert_weights={modelspace} "

	train_section = dict()
	test_section = dict()
	_cnt = dict()
	# output files
	for model in models:
		with open(f"scripts_evals/{modelspace}_{model}.sh","w") as f:
			f.write(f'#!/bin/bash\n# File generated by script catastrophic_forgetting.py for config {modelspace}\n\n')

	train_filename=""
	prev_ds=None
	filename=""
	for _idx,ds_train in enumerate(datasets):
		filename += f"-train_{ds_train}"
		
		fnames = dict()

		for model in models:
			script_name = f"scripts_evals/{modelspace}_{model}.sh"
			
			if model=="cedr":
				script_name = f"scripts_evals/{modelspace}_vbert.sh"

			fnames[model] = script_name
			ranker = models_ranker[model]

			# do training of model with dataset in modelspace (not testing)
			command = f"CUDA_VISIBLE_DEVICES={models_gpu[model]} python -m onir.bin.pipeline pipeline={pipeline} modelspace={modelspace} data_dir={datafolder}  vocab.source=glove vocab.variant=cc-42b-300d 	{models_ranker[model]} ranker.add_runscore=True {config_dataset[ds_train]} "
			if prev_ds is not None:
				ncommand = f"pipeline.finetune=true trainer.pipeline={datasets_training[prev_ds]} "
				command+= ncommand

			command += f">output/tr_{modelspace}_{model}.out 2>output/tr_{modelspace}_{model}.err "

			#write file
			
			if model=="cedr":
				pretrain = train_section.get("vbert","")
				train_section["vbert"] = pretrain + f"# Training {ds_train}\n{command}\nwait\n"
			else:
				pretrain = train_section.get(model,"")
				train_section[model] = pretrain + f"# Training {ds_train}\n{command}\nwait\n"
			#with open(script_name,"a+") as f:
			#	f.write(f"# Training {ds_train}\n{command}\nwait\n")

			for ds_test in datasets: 
				current_gpu = models_gpu[model]
				#if pivot_gpu is not None and ds_test=="msmarco":
				#	current_gpu = pivot_gpu
				output_f = f"{output_dir}/model_{model}{filename}-test_{ds_test}"
                #test over this dataset
				command = f"FILE='{output_f}'\nif [ -f $FILE ]; then\n\techo 'this file {output_f} exists!'\nelse\n\tCUDA_VISIBLE_DEVICES={current_gpu} python -m onir.bin.pipeline pipeline={pipeline} modelspace={modelspace} data_dir={datafolder}  vocab.source=glove vocab.variant=cc-42b-300d 	{models_ranker[model]} 	ranker.add_runscore=True {config_dataset[ds_train]} {config_test_dataset[ds_test]} pipeline.test=true 	pipeline.onlytest=true 	pipeline.finetune=true 	trainer.pipeline={datasets_training[ds_train]} 	pipeline.savefile={output_f} >output/tr_{modelspace}_{model}.ts_{ds_test}.out 2>output/tr_{modelspace}_{model}.ts_{ds_test}.err\nfi &"
				
				#write file

				_model = model
				if model =="cedr":
					_model = "vbert"
				pretest = test_section.get(_model,"")
				_cnttmp =_cnt.get(_model,0)
				if _cnttmp%2==1:
					test_section[_model] = pretest+f"# Testing {ds_test}\n{command}\nwait\n"
				else:
					test_section[_model] = pretest+f"# Testing {ds_test}\n{command}\n\n"	
				_cnt[_model] = _cnttmp + 1
				#with open(script_name,"a+") as f:
				#	f.write(f"# Testing {ds_test}\n{command}\n\n")


			#write file
			#with open(script_name,"a+") as f:
			#	f.write("wait\n\n")

			# with & to run independently
			if model=="vbert":
				n_command = f"CUDA_VISIBLE_DEVICES={models_gpu[model]} python -m onir.bin.extract_bert_weights modelspace={modelspace} pipeline.bert_weights={modelspace} {config_dataset[ds_train]} pipeline.test=true {models_ranker[model]} 	pipeline.overwrite=True ranker.add_runscore=True data_dir=../data "
				#write file
				train_section[model] = train_section[model] + f"{n_command}&\nwait\n"
				#with open(script_name,"a+") as f:
				#	f.write(f"{n_command}&\nwait\n")


		#when model finishs
		prev_ds=ds_train


		with open(f"run_{modelspace}.sh","w") as f:
			f.write(f"#!/bin/bash\n#File generated to handle {modelspace}\n")
			for model in models:
				if model!="cedr":
					f.write(f"bash scripts_evals/{modelspace}_{model}.sh &\n")

	pretrain = ""
	pretest = ""
	for model in models:
		if model =="cedr":
			continue
		with open(fnames[model],"a+") as f:
			#print(train_section[model], fnames[model])
			f.write(pretrain+train_section[model])
			f.write(pretest+test_section[model])


if __name__ == '__main__':
    main()

