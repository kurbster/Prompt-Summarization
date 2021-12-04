#!/bin/bash

. configs/training.cfg

# Read the training params into this var
args=$(<$TRAINING_PARAMS)
args="${args//$'\n'/ }"

! [[ -f "./_prepared.jsonl" ]] && openai tools fine_tunes.prepare_data -f "$TRAIN_DIR/$TRAIN_FNAME" "$PREPROCESSING_MODE"
# TRAIN_FNAME will end with .json save as jsonl
mv "./_prepared.jsonl" $TRAIN_DIR/$TRAIN_FNAME"l"

openai api fine_tunes.create -t $TRAIN_DIR/$TRAIN_FNAME"l" -m $MODEL_NAME $args | tee tmp_file

trained_model=$(awk -F"Uploaded model: " '{print $2}' tmp_file | tr -d "\n")

# Output the name of our trained model to a file
echo "Our trained model "
echo $trained_model | tee -a ".env/fine_tuned_models"
rm tmp_file
