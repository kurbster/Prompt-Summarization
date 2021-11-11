
TRAINED_MODEL_NAME=""
IS_TRAIN=""
while [[ $IS_TRAIN != "Yes" ]] && [[ $IS_TRAIN != "No" ]]
do
    echo "Do you like train a model (Yes/No) : "
    read IS_TRAIN
done

if [ $IS_TRAIN == "Yes" ]
then


    
    echo "Enter the training data file path : "
    read DATA_PATH

    echo "For data pre-processing do you like to follow optmial setting / custom settings (o/c): "
    read MODE

    if [ $MODE == "o" ]
    then
        openai tools fine_tunes.prepare_data -f $DATA_PATH -q
    else
        openai tools fine_tunes.prepare_data -f $DATA_PATH
    fi
 
    echo "Provide Model Name (curie/ada/babbage): "
    read MODEL_NAME
    MODEL=$(openai api fine_tunes.create -t ./_prepared.jsonl -m $MODEL_NAME | tee /dev/tty)
    if [[ "$MODEL" =~ (openai api completions.create -m )($val:[a-z]*-[a-z]*-[a-z0-9]*-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2})( -p) ]]
    then
        echo "TRAINED MODEL NAME: ${BASH_REMATCH[2]}"
        TRAINED_MODEL_NAME=${BASH_REMATCH[2]}
    fi

    # if [[ $MODEL =~ (.*openai api completions.create -m )($val:[a-z]*-[a-z]*-[a-z0-9]*-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2})( -p.*) ]]
    # then
    #     echo "TRAINED MODEL NAME: ${BASH_REMATCH[2]}"
    #     TRAINED_MODEL_NAME=${BASH_REMATCH[2]}
    # fi
fi


while ! [[ "$TRAINED_MODEL_NAME" =~ ([a-z]*:[a-z]*-[a-z]*-[a-z0-9]*-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2}) ]] 
do
    echo "Provide pretrained Model Name (eg : babbage:ft-user-chhc505t5ztpztvzj2qquvwn-2021-11-10-06-51-31 ): "
    read TRAINED_MODEL_NAME
done

TEST_FILE="-1_I_hope_file_like_this_dosent_exist_in_anyones_pc"
# TEST_FILE="./test.txt"

while [ ! -f $TEST_FILE ]
do
    echo "enter a valid test filepath : "
    read TEST_FILE
done

echo "where do you like to store results : "
read RESULTS_FILE

touch $RESULTS_FILE
echo "" > $RESULTS_FILE

COUNT=0
LINES=$(cat $TEST_FILE)



for PROMPT in $LINES
do

    echo -e "PROMPT$COUNT -> $PROMPT" >> $RESULTS_FILE
    RESULT=$(openai api completions.create -m $TRAINED_MODEL_NAME -p "$PROMPT ->" | tee /dev/tty)

    echo -e "RESULT$COUNT -> $RESULT\n\n" >> $RESULTS_FILE
    ((COUNT=COUNT+1))
done