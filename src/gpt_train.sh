#!/bin/bash

. configs/training.cfg

# Read the training params into this var
args=$(<$TRAINING_PARAMS)
args="${args//$'\n'/ }"

#! [[ -f "./_prepared.jsonl" ]] && openai tools fine_tunes.prepare_data -f $TRAIN_DATA $PREPROCESSING_MODE

openai api fine_tunes.create -t "./train_summary.jsonl" -m $MODEL_NAME $args | tee tmp_file

trained_model=$(awk -F"Uploaded model: " '{print $2}' tmp_file | tr -d "\n")

# Output the name of our trained model to a file
echo "Our trained model $trained_model" | tee -a fine_tuned_models
rm tmp_file
