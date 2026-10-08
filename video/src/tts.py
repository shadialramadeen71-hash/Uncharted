import sys, os, subprocess, json
S=sys.argv[1]; sys.path.insert(0,S)
from script import SEGMENTS
os.makedirs(S+"/audio",exist_ok=True)
for i,(sp,text,*_) in enumerate(SEGMENTS):
    if sp=="CLIP": continue
    out=f"{S}/audio/seg{i:02d}.wav"
    if sp=="N":
        subprocess.run(["python3","-m","piper","-m",S+"/voice/ryan.onnx","-f",out+".raw.wav","--length-scale","1.05","--sentence-silence","0.35"],input=text,text=True,check=True,capture_output=True)
        subprocess.run(["ffmpeg","-y","-v","error","-i",out+".raw.wav","-af","aresample=44100,highpass=f=70,acompressor=threshold=-18dB:ratio=3,loudnorm=I=-16:TP=-1.5","-ar","44100","-ac","1",out],check=True)
    else:
        # cartoon: pitch up ~4 semitones, slightly faster
        subprocess.run(["python3","-m","piper","-m",S+"/voice/lessac.onnx","-f",out+".raw.wav","--length-scale","0.95","--sentence-silence","0.25"],input=text,text=True,check=True,capture_output=True)
        subprocess.run(["ffmpeg","-y","-v","error","-i",out+".raw.wav","-af","aresample=44100,asetrate=44100*1.26,aresample=44100,atempo=0.88,loudnorm=I=-16:TP=-1.5","-ar","44100","-ac","1",out],check=True)
    os.remove(out+".raw.wav")
    d=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",out],capture_output=True,text=True).stdout)
    print(i,sp,round(d,2),flush=True)
