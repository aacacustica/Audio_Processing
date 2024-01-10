#!/bin/bash 

# if [ "$#" -ne 2 ]; then means if the number of arguments is not equal to 2
if [ "$#" -ne 2 ]; then
    # then, exit with error code 1, which means "general error"
    echo "Usage: $0 input_folder output_folder"
    exit 1
fi

# set input_folder to the first argument and output_folder to the second argument
input_folder="$1"
output_folder="$2"

total_files=0

# for i in "$input_folder"/*.wav; do means for each file in the input folder
for i in "$input_folder"/*.wav; do
    # increment total_files by 1
    total_files=$((total_files + 1))
done

# print "Total files: $total_files"
echo "Total files: $total_files"
sleep 2

completed_files=0

for i in "$input_folder"/*.wav; do
    # got wav file output_folder/$(basename "$i"), basename means the file name without the path
    output_file="$output_folder/$(basename "$i")"

    # ffmpeg is a tool for converting audio and video files from one format to another, 
    # -v error means only print error messages, 
    # -stats means print encoding progress, 
    # -i means input file, 
    # -ac means number of audio channels, 
    # -ar means audio sampling rate, 
    # -acodec means audio codec, 
    # pcm_s16le means PCM signed 16-bit little-endian, 
    # < /dev/null means redirect input from /dev/null, which is a special file that discards all data written to it
    ffmpeg -v error -stats -i "$i" -ac 1 -ar 16000 -acodec pcm_s16le "$output_file" < /dev/null
    
    completed_files=$((completed_files + 1))
    percentage=$((completed_files * 100 / total_files))
    
    printf "Conversion progress: [%-20s] %d%%\r" $(printf "#%.0s" $(seq 1 $((percentage/5)))) $percentage
done

echo "Conversion complete!"
