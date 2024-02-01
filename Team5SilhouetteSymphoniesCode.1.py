#Some adjustments have to made to use this code on your device. These adjustmensts are explained next to it as well. I have marked all spots where adjustments have to made with "ADJUSTMENTFLAG"
#Use Ctrl + F --> ADJUSTMENTFLAG to make all adjustments.

#Developed By Luc Koster, TU Delft 2024

print()
print("Initialising")
print()
import numpy as np #These are needed to play .wav files
import wave

##Voice to Voice Neccesities
from openai import OpenAI
from pathlib import Path
from pydub import AudioSegment
from pydub.utils import mediainfo
import keyboard 

import serial #These are for connecting to the Itsybitsy
import time
import serial.tools.list_ports

from ctypes import cast, POINTER #We need these for lowering volume in Windows
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

import os #Needed to automatically record 
import sounddevice as sd
import wavio

from moviepy.editor import VideoFileClip #To play mp4

from requests.exceptions import ConnectionError #To recognise errors
from httpcore import RemoteProtocolError

import threading #To make a thread

import shutil #to save wav files

##INPUT VALID AI KEY
api_key = 'OPENAI KEY'  #Get an open AI key that is valid by creating an professional account on OpenAI, follow the steps given there. ADJUSTMENTFLAG
client = OpenAI(api_key=api_key)


# Set the maximum number of tokens in the response
max_tokens = 200 #Couldnt be used in Text_Enhancer or seperate_speakers due to the system failing to output nice lines



#Used variables
MaxRetiesOPENAI = 10 #Amount of retries for an OPENAI request if it fails

Global_Echo_Text = "" #Needed for integration of Echo into conversation generation

#To make sure we get the output we want, the environment is created. This is done with giving a prompt to the 'system'. The 'user'
#gets its prompt in this environment and works in it. 
System_Design_Text_enhancer = """Given a dialogue between two people, A and B, create a new dialogue that meets the following criteria:
The new dialogue should be between 100 and 150 words.
Each person's line should start with 'A: ' or 'B: ' to maintain the format.
The new dialogue should preserve the essence and tone of the original dialogue.
No inappropiate content is given as an output. Make sure it is PG in european standards.
Your input is a text representing the original dialogue. Please use this as inspiration to craft the new dialogue.
"""
#This prompt is given to the 'user' in front of the transcript that is being sent with it (and will be moderated)
prompt_Text_enhancer = "The input text: "

#We want the text to end with an open question. That is being created with these prompt and the function "Question_maker"
System_Design_Question_maker = """Given a dialogue between two people, A and B, create an open question that is 
PG for european standards, and allows for a conversation about the topic. The question should be about a topic discussed in the text given.
"""
prompt_Question_maker = "Output just the generated question. The input text: "

Text_Echo_Prompt_Setup = "You will write a short response that is first person and based on a transcript given to you. This response must feel personal and short. Use a maximum of 2 sentences"

# INPUT TEXTS (EXAMPLES)
user_text = "Hey! You won't believe what I just learned about cognitive robotics at TU Delft. It's mind-blowing! Oh, really? Tell me more. What's going on there?So, TU Delft is at the forefront of developing robots with serious brains. They're not just automated machines; they're working on cognitive systems that can adapt and make decisions on their own. No way! That sounds like something out of a sci-fi movie. How are they doing that? It's all about integrating machine learning into robotics. They're teaching robots to learn from experience, so they can improve their decision-making over time. Imagine robots that get better at their job the more they do it. That's wild! But, isn't there a risk with this kind of advanced technology? Absolutely, and that's what's so cool about it. TU Delft is not just focused on the tech; they're also deep into the ethics of it. They're actively thinking about how to make sure these robots are used responsibly and don't cause any unintended issues. That's a relief. It's crucial to think about the ethical side of things. Any specific breakthroughs they're working on? They're tackling challenges like making robots more transparent and accountable. And guess what? They're exploring interdisciplinary approaches, bringing in knowledge from computer science, neuroscience, and engineering. It's a real mix of brains working on these projects. That's impressive. I had no idea TU Delft was doing all of this. It sounds like they're shaping the future of robotics. Totally! It's not just about robots doing tasks; it's about making them an integral part of our lives. They want these robots to be not just efficient but seamlessly integrated into our daily routines.I'm blown away. Next time I hear about robots, I'm going to picture these cognitive ones from TU Delft. Thanks for sharing, it's fascinating!No problem! I knew you'd find it as cool as I did. Imagine the possibilities!"#input("Enter your text: ")
transcript1 = "A: Hey! I am Luc, who are you? B: I am Mats, nice to meet you. A: What are you doing? B: I am making a programn."
transcript2 = "What are they talking about? I don't know, I think it is something that has to do with coding. Pretty ironic that it is talking about that, since they are probably using a code to create that conversation. Do you think so? "

#Recording audio variables


#For the following file paths I suggest to create a main folder for this installation, and put other folders in there that will be mentioned down here. The main folder should have a file path
#that resembles: "C:\Users\Downloads\CodingSilhouetteSymphonies\". When inserting a designated folder, for example for initial recordings, you will need to insert something like: 
#"C:\Users\Downloads\CodingSilhouetteSymphonies\InitialRecordings". Here \CodingSilhouetteSymphonies is the main folder, \InitialRecordings is the specific folder inside there. You can select
#the folder in the windows explorer and right mouse click --> Copy as path, this gives you the path

#Filepath creation for the initial recording
folder_path_recorded_audio = r"MainPathTo\InitialRecordings" #ADJUSTMENTFLAG
file_name_recorded_audio = "recorded_audio.wav"
full_path_recorded_audio = os.path.join(folder_path_recorded_audio, file_name_recorded_audio)

file_name_Echo_audio = "Echo_input.wav"
full_path_recorded_Echo_Input = os.path.join(folder_path_recorded_audio, file_name_Echo_audio)

#Filepath for all intermediate files created to make the final audiofiles
File_Path_Intermediate_Files = r"MainPathTo\ProcessingRecordings" #ADJUSTMENTFLAG

#Filepath for all finalized audiofiles
File_Path_Final_AudioFiles = r"MainPathTo\OutputRecordings" #ADJUSTMENTFLAG

##This is the location on the computer of the input .mp3 file 
mp3File = full_path_recorded_audio #mp3 to input
video_file_path_Host = r"MainPathTo\Hostvideo.mp4" #The location of the video of the Host #ADJUSTMENTFLAG
Introduction_Of_Echo_audio = r"MainPathTo\EchoExplanation2.wav" #This explains the echo thing (int16) #ADJUSTMENTFLAG
Beep_Record = r"MainPathTos\BeepRecord3.wav" #ADJUSTMENTFLAG
Beep_Stop_Record = r"MainPathTo\BeepStopRecord2.wav" #ADJUSTMENTFLAG
Processing_announcement = r"MainPathTo\ProcessingAnnouncement.wav" #ADJUSTMENTFLAG
Old_Audio_announcement = r"MainPathTo\OldAudioAnnouncement.wav" #ADJUSTMENTFLAG
Start_Of_VTVLoop_announcement = r"MainPathTo\StartOfVTVLoopAnnouncement.wav" #ADJUSTMENTFLAG

Var_key_Q = False #This creates the option to manually start the process of creating an echo et cetera. This is mainly for if the sensor doesn't work
Var_key_Z = False
def play_audio(file_path):
    # Read the audio file
    wave_file = wave.open(file_path, 'rb')
    samplerate = wave_file.getframerate()
    frames = wave_file.readframes(-1)

    # Convert frames to NumPy array
    audio_data = np.frombuffer(frames, dtype=np.int16)

    # Play the audio
    sd.play(audio_data, samplerate)
    sd.wait()

    # Close the wave file
    wave_file.close()

def VoiceToText(audiofile, max_retries=MaxRetiesOPENAI):
    for attempt in range(1, max_retries + 1):
        try:
            audio_file= open(audiofile, "rb") 

            transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file, 
            response_format="text"
            )
            VoiceToText_text = transcript

            return VoiceToText_text
        except Exception as e:
            print(f"Unexpected error during attempt {attempt}/{max_retries} VoiceToText: {e}")
            if attempt < max_retries:
                print("Retrying...")
                time.sleep(1)  # Adding a small delay before retrying to avoid rate limits
            else:
                print("Max retries reached. Exiting.")
                # You might want to raise an exception or handle this situation as needed.
                raise

def Question_maker(text, max_retries=MaxRetiesOPENAI): #Create an open question with OpenAI API 
    for attempt in range(1, max_retries + 1):
        try:
            Question_maker = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": System_Design_Question_maker}, #defining the system for the 'user' to work in
                    {"role": "user", "content": f"{prompt_Text_enhancer} {text}"} #giving the prompt and the text
                ],
            #max_tokens=max_tokens  # Limit the number of tokens in the response
            )
            answer = Question_maker.choices[0].message.content
            answer = answer.replace('Open question: ','') #Removing the text it often puts in front, or the "" that it creates with it sometimes
            answer = answer.replace('"','')
            return answer
        except Exception as e:
            print(f"Unexpected error during attempt {attempt}/{max_retries} Question_maker: {e}")
            if attempt < max_retries:
                print("Retrying...")
                time.sleep(1)  # Adding a small delay before retrying to avoid rate limits
            else:
                print("Max retries reached. Exiting.")
                # You might want to raise an exception or handle this situation as needed.
                raise

def Text_enhancer(text,Global_Echo_Text, max_retries=MaxRetiesOPENAI): #Enhance the text transcribed with OpenAI API
    for attempt in range(1, max_retries + 1):
        try:

            Enhancer = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"{System_Design_Text_enhancer} and in the style of {Global_Echo_Text}"}, #defining the system for the 'user' to work in
                    {"role": "user", "content": f"{prompt_Text_enhancer} {text}"} #giving the prompt and the text
                ],
            #max_tokens=max_tokens  # Limit the number of tokens in the response
            )
            return Enhancer.choices[0].message.content
        except Exception as e:
            print(f"Unexpected error during attempt {attempt}/{max_retries} Text_enhancer: {e}")
            if attempt < max_retries:
                print("Retrying...")
                time.sleep(1)  # Adding a small delay before retrying to avoid rate limits
            else:
                print("Max retries reached. Exiting.")
                # You might want to raise an exception or handle this situation as needed.
                raise

def Text_Echo_Response(Prompt, max_retries=MaxRetiesOPENAI): #Enhance the text transcribed with OpenAI API
    for attempt in range(1, max_retries + 1):
        try:
            Enhancer = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"{Text_Echo_Prompt_Setup}"}, #defining the system for the 'user' to work in
                    {"role": "user", "content": f"Someone is talking to you and gives their wish. The wish is: {Prompt}"} #giving the prompt and the text
                ],
            #max_tokens=max_tokens  # Limit the number of tokens in the response
            )
            Text_Echo = Enhancer.choices[0].message.content
            Text_Echo_ASCII = ''.join(char for char in Text_Echo if ord(char) < 128) #Remove nonASCII characters
            return Text_Echo_ASCII
        except Exception as e:
            print(f"Unexpected error during attempt {attempt}/{max_retries} Text_Echo_Response: {e}")
            if attempt < max_retries:
                print("Retrying...")
                time.sleep(1)  # Adding a small delay before retrying to avoid rate limits
            else:
                print("Max retries reached. Exiting.")
                # You might want to raise an exception or handle this situation as needed.
                raise

def Echo_maker(wavfile, max_retries=MaxRetiesOPENAI**2):
    for attempt in range(1, max_retries + 1):
        try:
            global Global_Echo_Text #Get the global variable in the function

            #VoiceToText
            audio_file= open(wavfile, "rb") 

            transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file, 
            response_format="text"
            )

            #TextToText
            Echo_Text = Text_Echo_Response(transcript)
            print(Echo_Text)
            Global_Echo_Text = Echo_Text

            #TextToVoice
            if Echo_Text: #If the string is not empty...
                    Echo_Path_Extra_Piece = r"Echo.wav" #the r makes it raw so the text is read correctly, the f makes it
                    #possible for me to create unique filenames with the index in there
                    Full_Path_Echo = os.path.join(File_Path_Final_AudioFiles, Echo_Path_Extra_Piece)
            
                    response = client.audio.speech.create(
                    model="tts-1",
                    voice="onyx", #This voice can be changed of course
                    input=Echo_Text
                    )
                    


                    response.stream_to_file (Full_Path_Echo) #I redirect the response to the created file
                    audio_segment = AudioSegment.from_file(Full_Path_Echo, format="mp3")
                    audio_segment.export(Full_Path_Echo, format="wav")
                    print("AUDIOFILE SHOULD BE UPDATED FOR ECHO")
            
            return Echo_Text
        except Exception as e:
            print(f"Unexpected error during attempt {attempt}/{max_retries**2} Echo_maker: {e}")
            if attempt < max_retries:
                print("Retrying...")
                time.sleep(1)  # Adding a small delay before retrying to avoid rate limits
            else:
                print("Max retries reached. Exiting.")
                # You might want to raise an exception or handle this situation as needed.
                raise

def separate_speakers(text, max_retries=MaxRetiesOPENAI**2): #Create separate lists of what is said by A and what is said by B
    for attempt in range(1, max_retries + 1):
        try:
            # Define prompts for Speaker A and Speaker B
            prompt_speaker_a = "Recognise what lines are written by A and only output those lines of text exactly as given: "
            prompt_speaker_b = "Recognise what lines are written by B and only output those lines of text exactly as given: "
            
            # Combine each speaker's prompts with the input text
            input_text_a = f"{prompt_speaker_a} {text}"
            input_text_b = f"{prompt_speaker_b} {text}"
            
            # Request completions for Speaker A and Speaker B
            response_a = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "A text is given between two people. Split the text between what belongs to A and what belongs to B. Output all text that belongs to A"},
                    {"role": "user", "content": input_text_a}
                ],
            #max_tokens=max_tokens  # Limit the number of tokens in the response
            )
            
            response_b = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "A text is given between two people. Split the text between what belongs to A and what belongs to B. Output all text that belongs to B"},
                    {"role": "user", "content": input_text_b}
                ]
            )

            return response_a.choices[0].message.content, response_b.choices[0].message.content
        except Exception as e:
            print(f"Unexpected error during attempt {attempt}/{max_retries**2} separate_speakers: {e}")
            if attempt < max_retries:
                print("Retrying...")
                time.sleep(1)  # Adding a small delay before retrying to avoid rate limits
            else:
                print("Max retries reached. Exiting.")
                # You might want to raise an exception or handle this situation as needed.
                raise

def separate_A_from_B(text): #Does the same as separate_speakers, but better and without AI
    ASCIItext = ''.join(char for char in text if ord(char) < 128) #Remove nonASCII characters
    lines = ASCIItext.split('\n') #Split the text into the lines
    #print("ORIGINAL TEXT:")
    #print(ASCIItext)
    # Initialize lists to store A and B lines
    listA = []
    listB = []

    # Iterate through the lines
    for line in lines:
        # Check if the line starts with 'A:' or 'B:'
        if line.startswith('A:'):
            listA.append(line[2:].strip())  # Remove 'A:' and leading/trailing whitespaces
        elif line.startswith('B:'):
            listB.append(line[2:].strip())  # Remove 'B:' and leading/trailing whitespaces
    #Developed By Luc Koster, TU Delft 2024
    return listA,listB

def split_sentences(text): #This one seperates both on new lines and on dots, and connects broken off sentences over new lines
    # Split the string by newlines to get potential sentence groups
    modified_string = text.replace('. ', '.. ') #If '. ' is found, an extra dot is placed to make sure that there will be one dot left when it gets splitted
    potential_sentences = modified_string.split('. ') #The sentences get splitted on '. ' and this gets removed, leaving the one extra dot

    separated_sentences = [] #An empty body for the new strings that get created by splitting on '\n' (new line)

    for i in range(len(potential_sentences)): #For every string in the splitted-on-dot-space-sentences-list:
        
        splitted_sentences = potential_sentences[i].split('\n') #split on '\n'
        
        
        separated_sentences.extend(splitted_sentences) #Put these splitted strings into the new variable

    for j in range(len(separated_sentences)-1): #For every string in the splitted-on-both-dots-and-newlines-sentences-list:
            
            if separated_sentences[j].islower(): #if the last case is a lowercase instead of a dot: (recognising a sentence that is split over multiple lines)
                
                separated_sentences[j-1] += ' ' #Add a space in between
                separated_sentences[j-1] += separated_sentences[j] #put them together and put it on the name of the first part
                separated_sentences.pop(j) #remove the second part from the list

    return separated_sentences

def split_sentences2(text): #This one works worse technically but it is better in our case. It onlyy seperates on new lines and connects broken sentences
    New_line_splitted = text.split('\n')

    for i in range(len(New_line_splitted)-1): 
         if New_line_splitted[i] and New_line_splitted[i][-1].islower(): #if the last case is a lowercase instead of a dot: (recognising a sentence that is split over multiple lines)
            New_line_splitted[i] += ' ' #Add a space in between
            New_line_splitted[i] += New_line_splitted[i+1] #put them together and put it on the name of the first part
            New_line_splitted.pop(i+1) #remove the second part from the list

    return New_line_splitted

def get_audio_length(file_path): #FUNCTION FOR TEXT TO VOICE
    # Use mediainfo function to get information about the audio file
    audio_info = mediainfo(file_path)
    
    # Extract duration in milliseconds from the audio file information
    duration_s = float(audio_info['duration'])

    return duration_s

def set_volume(volume): #Function for setting the volume of the windows computer
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
    volume_interface.SetMasterVolumeLevelScalar(volume, None)

def record_audio(filename, duration=60, samplerate=44100): #Recording audio function
    print("Recording...")
    audio_data = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=2, dtype='int16')
    sd.wait()

    print("Saving to", filename)
    wavio.write(filename, audio_data, samplerate, sampwidth=2)

def on_key_event(e):
    global Var_key_Z
    global Var_key_Q
    if e.name == 'q' and e.event_type == keyboard.KEY_DOWN:
        Var_key_Q = True
        print("Key 'Q' pressed. Variable set to True.")
    elif e.name == 'z' and e.event_type == keyboard.KEY_DOWN:
        Var_key_Z = True
        print("Key 'Z' pressed. The Q is set")
    

def play_video(video_path, screen=1):
    os.environ['SDL_VIDEO_WINDOW_POS'] = f"{1920 * screen},0"  # Assuming the laptop screen resolution is 1920x1080
    clip = VideoFileClip(video_path)
    
    clip.preview(fullscreen=True)
    time.sleep(clip.duration)  # Add a delay to allow the video to play
    clip.close()

def save_wav_file(source_file_path, output_directory):
    # Ensure the output directory exists
    os.makedirs(output_directory, exist_ok=True)
    
    # Extract the filename from the source file path
    filename = os.path.basename(source_file_path)
    
    # Generate a unique timestamp for the filename
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Construct the destination file path with a unique filename
    destination_file_path = os.path.join(output_directory, f"{timestamp}_{filename}")
    
    # Copy the source file to the destination
    shutil.copyfile(source_file_path, destination_file_path)
    
    print(f"File copied to: {destination_file_path}")
#Flags to communicate between threads
PersonWalkedIN_Flag = False #When someone walks in, it is True, if walks out, it's False
RecordAudio_Flag = False #This runs the echo thread once
Echo_and_video_Flag = False #This makes sure the echo thread can be run and will be cut off when someone walks out
OlympicTorch = False #This keeps the main thread going, used so code blocks down the line don't run too early
Checkpoint_1 = False #This is to keep the order right
Main_Conversation_Flag = False #This is the flag needed for initiating the loop for the long recording and playback
Full_VTV_Flag = False #This is to initiate the VTV thread
Full_VTV_Running_Flag = False #This is to avoid the Echo starting up if second person walks in while other person is still inside NOT USED YET
Play_Host_video_Flag = False #This is to play the host video
#Developed By Luc Koster, TU Delft 2024

#Thread functions
def read_serial(): #Reading the serial of the Itsybitsy
    global received_value
    while True:
        if ser.in_waiting > 0:
            received_value = ser.readline().decode()
            print("The Itsybitsy sent the following: ", received_value)

def Echo_thread(duration):
    global RecordAudio_Flag
    global OlympicTorch
    global Echo_and_video_Flag

    while True:
        while RecordAudio_Flag == True:
            time.sleep(76) #waiting for the video to finish
            print("starting echo thread")
            

            play_audio(Introduction_Of_Echo_audio)
            time.sleep(2)
            play_audio(Beep_Record)

            record_audio(full_path_recorded_Echo_Input, duration=duration)

            play_audio(Beep_Stop_Record)
            #ECHO Processing
            wavEchoInput = full_path_recorded_Echo_Input
            Echo_maker(wavEchoInput)
            
            #ECHO Output
            audio_echo = r"PathTo\OutputRecordings\Echo.wav" #ADJUSTMENTFLAG
            play_audio(audio_echo)

            source_file_path = audio_echo
            output_directory = r"PathToTheFolderWithTheArchive" #ADJUSTMENTFLAG, this folder is for the old audio

            save_wav_file(source_file_path, output_directory)


            time.sleep(3) #Wait 3 seconds for the person to walk into the center
            play_audio(Old_Audio_announcement)
            time.sleep(1)
            audio_old_conversation = r"PATHTO\OutputRecordings\output_MONO.wav" #ADJUSTMENTFLAG
            play_audio(audio_old_conversation) 
            print("DONE PLAYING PREVIOUS AUDIO")
            time.sleep(3)

            OlympicTorch = True
            RecordAudio_Flag = False
            Echo_and_video_Flag = False
            break
            
            time.sleep(1)
        time.sleep(1)

def Host_video_play():
    global Play_Host_video_Flag
    global Echo_and_video_Flag

    while True:
        while Play_Host_video_Flag == True:
            Echo_and_video_Flag = True
            play_video(video_file_path_Host)
            
            Play_Host_video_Flag = False
            time.sleep(1)
            
            break


        time.sleep(1)

def VTV_thread():
    global Full_VTV_Flag
    global Main_Conversation_Flag

    while True:
        while Full_VTV_Flag == True:
            print("(re)starting VTV thread")
            print("Recording for the main conversation")
            play_audio(Beep_Record)
            record_audio(full_path_recorded_audio, duration=20) #Duration is amount of seconds it records
            play_audio(Beep_Stop_Record)
            print(f"Recording complete. Audio saved to {full_path_recorded_audio}")

            play_audio(Processing_announcement)
            wavFile = full_path_recorded_audio #wav to input
            print(VoiceToVoice(wavFile,Global_Echo_Text)) #Create the new audio

            audio_VTV = r"PATHTO\OutputRecordings\output_MONO.wav" #ADJUSTMENTFLAG
            play_audio(audio_VTV)

            source_file_path = audio_VTV
            output_directory = r"PathTo\OldAudio" #ADJUSTMENTFLAG

            save_wav_file(source_file_path, output_directory)
            
            time.sleep(5)
            
            time.sleep(1)

        time.sleep(1)
################################################################################################################################
################################################################################################################################
################################################################################################################################

#Voice To Voice function is the full pipeline in which an audiofile gets used to create a new audiofile (.mp3)
def VoiceToVoice(mp3file,Global_Echo_Text):
    ##VARS
    # Initialize an empty AudioSegment object to store the concatenated audio
    concatenated_audio_A = AudioSegment.empty()
    concatenated_audio_B = AudioSegment.empty()
    concatenated_audio_MONO = AudioSegment.empty()

    idx_a=0 #I need a separate index for the concatanation
    idx_b=0
    idx_mono = 0
    idx_mono_A = 0
    idx_mono_B = 0
    ################
    #audio_file= open(mp3file, "rb") 
    transcript = VoiceToText(mp3file)

    #print(type(transcript), "TRANSCRIPT: ",transcript)
    # PROCESSING
    open_question = Question_maker(transcript) #Create the open question 

    print("OPEN QUESTION: ", open_question)
    enhanced_text = Text_enhancer(transcript, Global_Echo_Text) #Connecting VoiceToText and TextToText and Echo Input
    enhanced_text += " \nA: " + open_question #Adding the open question with correct notation so the following code understands it
    print("ENHANCED TEXT: ", enhanced_text)
    print()

    print("PROCESSING CHATGPT ANSWER")
    print()
    Separate_texts = separate_A_from_B(enhanced_text) #separating the transciptions 
    print("SEPERATE TEXTS: ",Separate_texts)

    print()
    print("SENTENCE PREPARATION FOR TEXT TO VOICE")
    print()

    Sentences_split_A = Separate_texts[0] #separating the transcripts into separate strings
    Sentences_split_B = Separate_texts[1]
    
    #Creating a variable that resembles the length of the longest list
    Length_Longest_List = 1 #Extra variable to assign the longest length to
    if len(Sentences_split_A) >= len(Sentences_split_B):
        Length_Longest_List = len(Sentences_split_A)
    else:
        Length_Longest_List = len(Sentences_split_B)

    Index_Sentence_of_A = 0 #Getting some extra indexes to work through the strings 
    Index_Sentence_of_B = 0

    for i in range(Length_Longest_List):
        if Index_Sentence_of_A < len(Sentences_split_A):
            print(Sentences_split_A[Index_Sentence_of_A])
            print()
            Index_Sentence_of_A += 1
        
        if Index_Sentence_of_B < len(Sentences_split_B):
            print(Sentences_split_B[Index_Sentence_of_B])
            print()
            Index_Sentence_of_B += 1
    print()
    print("STARTING TEXT TO VOICE CODE")
    print()

    Finished_text_A = Sentences_split_A #To make my life a bit easier
    Finished_text_B = Sentences_split_B

    #Creating separate mp3 files for each string and person
    for idx, text_a in enumerate(Finished_text_A): #idx = index, text_a = one string within the list
    # Convert text for person A to MP3
        transcript_a = text_a  # Assuming text_a is the transcript for person A
        if transcript_a: #If the string is not empty...
            Indexed_Part_Of_A = rf"person_a_{idx}.mp3" #the r makes it raw so the text is read correctly, the f makes it
            #possible for me to create unique filenames with the index in there
            Full_Path_A_Indexed = os.path.join(File_Path_Intermediate_Files, Indexed_Part_Of_A)
    
            response_a = client.audio.speech.create(
            model="tts-1",
            voice="onyx", #This voice can be changed of course
            input=transcript_a
            )

            response_a.stream_to_file (Full_Path_A_Indexed) #I redirect the response to the created file

    

    for idx, text_b in enumerate(Finished_text_B): #idx = index, text_b = one string within the list
        # Convert text for person B to MP3
        transcript_b = text_b  # Assuming text_b is the transcript for person B
        if transcript_b:
            Indexed_Part_Of_B = rf"person_b_{idx}.mp3"
            Full_Path_B_Indexed = os.path.join(File_Path_Intermediate_Files, Indexed_Part_Of_B)

            response_b = client.audio.speech.create(
            model="tts-1",
            voice="alloy", #This voice can be changed of course
            input=transcript_b
            )
            response_b.stream_to_file (Full_Path_B_Indexed) #I redirect the response to the created file 

        # Concatenate the audio segments in the desired order
    for i in range(max(len(Finished_text_A),len(Finished_text_B))):
        Mono_Indexed_Part_Of_A = rf"person_a_{idx_mono_A}.mp3"
        Full_Path_A_Mono_Indexed = os.path.join(File_Path_Intermediate_Files, Mono_Indexed_Part_Of_A)

        Mono_Indexed_Part_Of_B = rf"person_b_{idx_mono_B}.mp3"
        Full_Path_B_Mono_Indexed = os.path.join(File_Path_Intermediate_Files, Mono_Indexed_Part_Of_B)
        
        max_A = len(Finished_text_A)
        max_B = len(Finished_text_B)
        print(f"The amount of sentences for A: {max_A} and for B: {max_B}")

        if Path(Full_Path_A_Mono_Indexed).is_file():
            
            if Path(Full_Path_B_Mono_Indexed).is_file():
                if idx_mono_A < max_A:
                    audio_segment_a = AudioSegment.from_file(Full_Path_A_Mono_Indexed, format="mp3")
                    concatenated_audio_MONO += audio_segment_a + AudioSegment.silent(duration=1000)
                    print(f"MONO: Concatinated person_a_{idx_mono_A}.mp3")
                    idx_mono_A += 1
                if idx_mono_B < max_B:
                    audio_segment_b = AudioSegment.from_file(Full_Path_B_Mono_Indexed, format="mp3")
                    concatenated_audio_MONO += audio_segment_b + AudioSegment.silent(duration=1000)
                    print(f"MONO: Concatinated person_b_{idx_mono_B}.mp3")
                    idx_mono_B += 1

    for i in range(max(len(Finished_text_A),len(Finished_text_B))):

        Indexed_Part_Of_A_idxA = rf"person_a_{idx_a}.mp3"
        Indexed_Part_Of_A_idxB = rf"person_a_{idx_b}.mp3"
        Indexed_Part_Of_B_idxA = rf"person_b_{idx_a}.mp3"
        Indexed_Part_Of_B_idxB = rf"person_b_{idx_b}.mp3"

        Full_Path_A_Indexed_idxA = os.path.join(File_Path_Intermediate_Files, Indexed_Part_Of_A_idxA)
        Full_Path_A_Indexed_idxB = os.path.join(File_Path_Intermediate_Files, Indexed_Part_Of_A_idxB)
        Full_Path_B_Indexed_idxA = os.path.join(File_Path_Intermediate_Files, Indexed_Part_Of_B_idxA)
        Full_Path_B_Indexed_idxB = os.path.join(File_Path_Intermediate_Files, Indexed_Part_Of_B_idxB)

        if Path(Full_Path_A_Indexed_idxA).is_file():
            #print(f"Concatinating person_a_{idx_a}")#,"THAT FILE IS: ", Full_Path_A_Indexed_idxA)
            audio_segment_a = AudioSegment.from_file(Full_Path_A_Indexed_idxA, format="mp3")
        
            concatenated_audio_A += audio_segment_a + AudioSegment.silent(duration=1000) #Concatenate the prepared audiosegment with a second delay (1000ms)
            if Path(Full_Path_B_Indexed_idxA).is_file(): #Adding silence from B
                Silence_for_B = get_audio_length(Full_Path_B_Indexed_idxA)
                concatenated_audio_A += AudioSegment.silent(duration=Silence_for_B*1000) + AudioSegment.silent(duration=1000)
            idx_a += 1
            
        if Path(Full_Path_B_Indexed_idxB).is_file():
            #print(f"Concatinating person_b_{idx_b}")
            audio_segment_b = AudioSegment.from_file(Full_Path_B_Indexed_idxB, format="mp3")
        
            if Path(Full_Path_A_Indexed_idxB).is_file(): #Adding silence from A
                Silence_for_A = get_audio_length(Full_Path_A_Indexed_idxB)
                concatenated_audio_B += AudioSegment.silent(duration=Silence_for_A*1000) + AudioSegment.silent(duration=1000)

                concatenated_audio_B += audio_segment_b + AudioSegment.silent(duration=1000) #Concatenate the prepared audiosegment with a second delay (1000ms)
        
            idx_b += 1
    # Export the concatenated audio to a new file
    
    output_file_name_of_A = r"output_a.wav"
    output_file_path_a = os.path.join(File_Path_Final_AudioFiles, output_file_name_of_A)

    output_file_name_of_B = r"output_b.wav"
    output_file_path_b = os.path.join(File_Path_Final_AudioFiles, output_file_name_of_B)

    output_file_name_of_MONO = r"output_MONO.wav"
    output_file_path_MONO = os.path.join(File_Path_Final_AudioFiles, output_file_name_of_MONO)

    concatenated_audio_A.export(output_file_path_a, format="wav")
    concatenated_audio_B.export(output_file_path_b, format="wav")
    concatenated_audio_MONO.export(output_file_path_MONO, format="wav")
    print("AUDIOFILE SHOULD BE UPDATED")
    A = "It worked"
    #########################################################################################################
    return A


ports = serial.tools.list_ports.comports()

for port, desc, hwid in sorted(ports): #Giving some info on what ports are used
    print(f"{port}: {desc} [{hwid}]")

# Replace COM3 with appropiate COM, Turn off the serial in Mu editor to get this one to work
ser = serial.Serial('COM3', 9600) #ADJUSTMENTFLAG


keyboard.hook(on_key_event)
#keyboard.wait('esc')


#Starting up threads

#serial communication
serial_thread = threading.Thread(target=read_serial)
serial_thread.start()
#Echo
thread_record_audio_Echo = threading.Thread(target=Echo_thread, args=(10,))
thread_record_audio_Echo.start()
#Playing host video
Hostvid_thread = threading.Thread(target=Host_video_play)
Hostvid_thread.start()
#Main loop (conversation and VTV)
VTV_loop_thread = threading.Thread(target=VTV_thread)
VTV_loop_thread.start()

received_value = "" #I need this variable to be blank to have a working code while no value is being sent by the ItsyBitsyqzz

while True:
    if Var_key_Z == True: #Press Z when someone walks out while people are still in it (it is a bug that i cannot fix)
        PersonWalkedIN_Flag = True  
        Full_VTV_Flag = True 
        Main_Conversation_Flag = True 
        Full_VTV_Running_Flag = True 
        Var_key_Z = False

    if Var_key_Q == True or received_value.startswith("Person went IN"):
        received_value = ""
        print("SOMEONE WALKED IN")
        PersonWalkedIN_Flag = True
        
        Play_Host_video_Flag = True
        #Volume at which audio will be played
        target_volume = 1  # 100%
        set_volume(target_volume)

        Var_key_Q = False
    
    while Echo_and_video_Flag == True and Full_VTV_Running_Flag == False:
        
        #ECHO Input
        RecordAudio_Flag = True #Sending this to the record audio thread will give us a recording and a True torchqz

        if received_value.startswith("Person went OUT"):
            print("SOMEONE WALKED OUT")
            PersonWalkedIN_Flag = False  # Reset the flag to exit the loop
            Echo_and_video_Flag = False
            break
        
        time.sleep(1)
    

    #Checkpoint 1:
    if OlympicTorch == True and PersonWalkedIN_Flag == True: #makes sure this following part is only run if the previous has been done and no one walked out
        Checkpoint_1 = True
        print("TORCH WAS PASSED FROM ECHO TO MAIN")
        OlympicTorch = False
        Main_Conversation_Flag = True
        play_audio(Start_Of_VTVLoop_announcement)
    
    while Main_Conversation_Flag == True and PersonWalkedIN_Flag == True:
        Full_VTV_Flag = True
        Full_VTV_Running_Flag = True

        if received_value.startswith("Person went OUT"):
            print("SOMEONE WALKED OUT")
            PersonWalkedIN_Flag = False  # Reset the flag to exit the loop
            Full_VTV_Flag = False #stop the VTV thread
            Main_Conversation_Flag = False #resetting this one
            Full_VTV_Running_Flag = False #To open up the echo again

            break

        time.sleep(1)

    time.sleep(1)

