import pyaudio
import wave
import audioop
from collections import deque 
import os
import urllib2
import urllib
import time


def listen_for_speech():
    """
    Does speech recognition using Google's speech  recognition service.
    Records sound from microphone until silence is found and save it as WAV and then converts it to FLAC. Finally, the file is sent to Google and the result is returned.
    """

    #config
    chunk = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    THRESHOLD = 180 #The threshold intensity that defines silence signal (lower than).
    SILENCE_LIMIT = 2 #Silence limit in seconds. The max ammount of seconds where only silence is recorded. When this time passes the recording finishes and the file is delivered.

    #open stream
    p = pyaudio.PyAudio()

    stream = p.open(format = FORMAT,
                    channels = CHANNELS,
                    rate = RATE,
                    input = True,
                    frames_per_buffer = chunk)

    print "* listening. CTRL+C to finish."
    all_m = []
    data = ''
    SILENCE_LIMIT = 2
    rel = RATE/chunk
    slid_win = deque(maxlen=SILENCE_LIMIT*rel)
    started = False
    
    while (True):
        data = stream.read(chunk)
        slid_win.append (abs(audioop.avg(data, 2)))

        if(True in [ x>THRESHOLD for x in slid_win]):
            if(not started):
                print "starting record"
            started = True
            all_m.append(data)
        elif (started==True):
            print "finished"
            #the limit was reached, finish capture and deliver
            filename = save_speech(all_m,p)
            stt_google_wav(filename)
            #reset all
            started = False
            slid_win = deque(maxlen=SILENCE_LIMIT*rel)
            all_m= []
            print "listening ..."

    print "* done recording"
    stream.close()
    p.terminate()


def save_speech(data, p):
    filename = 'output_'+str(int(time.time()))
    # write data to WAVE file
    data = ''.join(data)
    wf = wave.open(filename+'.wav', 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)
    wf.writeframes(data)
    wf.close()
    return filename


def stt_google_wav(filename):
    #Convert to flac
    os.system(FLAC_CONV+ filename+'.wav')
    f = open(filename+'.flac','rb')
    flac_cont = f.read()
    f.close()

    #post it
    lang_code='en-US'
    googl_speech_url = 'https://www.google.com/speech-api/v1/recognize?xjerr=1&client=chromium&pfilter=2&lang=%s&maxresults=6'%(lang_code)
    hrs = {"User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7",'Content-type': 'audio/x-flac; rate=16000'}
    req = urllib2.Request(googl_speech_url, data=flac_cont, headers=hrs)
    p = urllib2.urlopen(req)

    res = eval(p.read())['hypotheses']
    print res
    map(os.remove, (filename+'.flac', filename+'.wav'))
    return res

FLAC_CONV = 'flac -f ' # We need a WAV to FLAC converter.
if(__name__ == '__main__'):
    listen_for_speech()
