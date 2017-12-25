#!/usr/bin/env python
'''
Written by Michael Lam
'''

import numpy as np
import matplotlib as mpl
rc = mpl.rc
#mpl.style.use('classic')
#mpl.use('TkAgg')
import matplotlib.pyplot as plt
#import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator, FormatStrFormatter, LogLocator


import pygame
import pygame.camera
from PIL import Image
import functionfit as ffit
import sys
import time




if sys.version_info[0] < 3:
    import Tkinter as Tk
else:
    import tkinter as Tk



#rc('font',**{'family':'serif','serif':['Times New Roman'],'size':14})#,'weight':'bold'})
rc('font',family="Times New Roman",size=14)
rc('xtick',**{'labelsize':16})
rc('ytick',**{'labelsize':16})
rc('axes',**{'labelsize':18,'titlesize':18})
#rc('font',**{'family':'serif','serif':['Times']})
#rc('text', usetex=True)

SEPARATOR_COLOR="#CCCCCC"
SLEEP_TIME=1



##==================================================
## Data Processing
##==================================================

def getvalue(value,default=0):
    try:
        value = float(value)
    except ValueError:
        value = default
    return value



def record(ax,canvas, DIM=(20,20), testing=False):

    if testing:
        np.random.seed(42)
        # Generate lightcurve here
        T = 500
        dt = 1.2
        times = np.arange(T,dtype=np.float) * dt

        period = 67.4
        phase = 26.6
        width = 3.2

        lightcurve = buildpulsetrain(times,period,phase,width,amplitudes=(0.8,1.2)) + np.random.normal(15.7,0.05,T)  #some baseline
        ax.plot(times,lightcurve,'k.')


        var_pulseperiod.set('67.4')
        var_pulsewidth.set('3.2')
        return times, lightcurve

    



    pygame.camera.init()
    cameras = pygame.camera.list_cameras()
    cam = pygame.camera.Camera(cameras[0], DIM)
    cam.start()
    time.sleep(1.0)  #0.1 # You might need something higher in the beginning

    RECORD_SECONDS = getvalue(var_duration.get(),default=5)

    print("* recording")

    times = list()
    lightcurve = list()

    t0 = time.time()
    
    STEP = 10
    counter = 0

    while True:
        
        surf = cam.get_image()
        data = pygame.image.tostring(surf, 'RGBA')
        img = Image.fromstring('RGBA', DIM, data).convert('LA')
        #pixels = np.asarray(img)[0]
        #pixels = list(img.getdata())
        #print pixels
        
        intensities = map(lambda x: x[0],img.getdata())#pixels)
        nowtime = time.time() - t0
        if nowtime < 1:  #cut off first second but the time series was extended by 1 second
            continue
        times.append(nowtime-1)
        lc = np.mean(intensities)
        lightcurve.append(lc)
        if nowtime >= RECORD_SECONDS + 1:
            break
        ax.plot([nowtime],[lc],'k.')
        canvas.draw()


    cam.stop()
    
    print("* done recording")

    times = np.array(times)
    lightcurve = np.array(lightcurve)
    
    return times, lightcurve





##==================================================
## GUI 
##==================================================

    
root = Tk.Tk()
#root.geometry('+1400+100')
root.geometry('850x750+100+100') #Not sure why grid is failing
root.wm_title("Pulse Camera")






## ----------
## Build primary GUI containers
## ----------

mainframe = Tk.Frame(root)
mainframe.grid(row=0)

figframe = Tk.Frame(mainframe)#, bd = 6, bg='red')
#fig = Figure(figsize=(8.5,5), dpi=75)
fig = Figure(figsize=(11.5,7.75), dpi=75)
fig.subplots_adjust(wspace=0.5,left=0.15) #left allows enough space for the yaxis label to be read.
canvas = FigureCanvasTkAgg(fig, figframe)
canvas.get_tk_widget().grid(row=0)#,side=Tk.TOP)#,fill='x')
canvas.show()

canvas._tkcanvas.grid(row=1)#, fill=Tk.BOTH, expand=1)

figframe.grid(row=0,column=0)



## ----------
## Tkinter Variables
## ----------
var_mode = Tk.IntVar()
var_fits_on = Tk.IntVar()
var_message = Tk.StringVar()



var_phase = Tk.StringVar()
var_period = Tk.StringVar()
var_amplitude = Tk.StringVar()
var_amplitudeconv = Tk.StringVar()

var_depth = Tk.StringVar()
var_width_top = Tk.StringVar()
var_width_bottom = Tk.StringVar()



var_pulseperiod = Tk.StringVar()
var_pulsewidth = Tk.StringVar()
var_leftclicks = Tk.IntVar()
var_clickval = Tk.DoubleVar()

var_duration = Tk.StringVar()
var_clickmode = Tk.StringVar()
var_message = Tk.StringVar()

var_mode.set(-1)


## ----------
## Primary Window
## ----------



tdata = list()
ydata = list()

tfit = list()
yfit = list()


#gs = gridspec.GridSpec(2, 7)
ax_lightcurve = fig.add_subplot(211)#gs[0,:-2])
ax_residcurve = fig.add_subplot(212)#gs[1,:-2])
#ax_template = fig.add_subplot(gs[0, -2:])




def redraw_axes():
    ax_lightcurve.set_ylabel('Intensity')
    ax_residcurve.set_xlabel('Time [seconds]')
    ax_residcurve.set_ylabel('Residuals [seconds]')
    #ax_template.set_yticklabels([])
    #ax_template.set_xticks([])
    #ax_template.set_xlim(0.3,0.7)
    #ax_template.set_xticks([0.3,0.7])

    #ax_template.set_xlabel('Phase')
    #ax_template.set_title('Template')
    canvas.draw()



def update_main(rec=True,clear=False,testing=False):
    global tdata,ydata
    ax_lightcurve_xlim = ax_lightcurve.get_xlim()
    ax_lightcurve_ylim = ax_lightcurve.get_ylim()
    ax_residcurve_xlim = ax_residcurve.get_xlim()
    ax_residcurve_ylim = ax_residcurve.get_ylim()

    ax_lightcurve.cla()
    ax_residcurve.cla()

    if clear:
        ax_lightcurve.plot(tdata,ydata,'k')       
        ax_lightcurve.set_ylim(ax_lightcurve_ylim) 
        ax_lightcurve.set_xlim(ax_lightcurve_xlim)
        ax_residcurve.set_xlim(ax_lightcurve_xlim)
        var_leftclicks.set(0)
    elif rec:
        tdata,ydata = record(ax_lightcurve,canvas,testing=testing)
        ax_residcurve.set_xlim(ax_lightcurve.get_xlim())

    redraw_axes()

def update_mainclear():#mode=-1):
    update_main(clear=False)

def update_maintesting():#mode=-1):
    update_main(testing=True)




def gaussian(x,a,b,c):
    return a*np.exp(-0.5*((x-b)/c)**2)
def buildpulsetrain(times,period,phase,width,amplitudes=1.0,baseline=0.0,full_output=False):
    model = np.zeros(len(times))
    t = -1*period
    phases = list()
    counter = -1
    if type(amplitudes) == list or type(amplitudes) == np.ndarray:
        amplitudes = np.array(amplitudes)
        amplitudes = np.concatenate((amplitudes,[0.0]))
    while t < times[-1] + period:
        if type(amplitudes) == tuple:
            amp = np.random.uniform(amplitudes[0],amplitudes[1])
        elif type(amplitudes) == np.ndarray:
            amp = amplitudes[counter]
        else:
            amp = amplitudes

        model += gaussian(times,amp,phase+t,width) 
        phases.append(phase+t)
        t += period
        counter += 1
    model += baseline
    if full_output:
        return model,phases
    return model


def fit_model():
    global tdata,ydata


    ax_lightcurve.cla()
    ax_residcurve.cla()


    guessperiod = getvalue(var_pulseperiod.get())

    FWHMfac = 2*np.sqrt(2*np.log(2))
    guesswidth = getvalue(var_pulsewidth.get())#/FWHMfac # FWHM to sigma
    guessbaseline = np.mean(np.sort(ydata)[:len(ydata)/2]) #/4?

    #duration = getvalue(var_duration.get())
    ax_lightcurve.plot(tdata,ydata,'k.')


    if guessperiod == 0.0 or guesswidth == 0.0:
	redraw_axes()
        return


    
    
    
    # For the model pulse, figure out the best pulse phase
    guessphases = np.linspace(0,guessperiod,100)
    chisqs = np.zeros_like(guessphases)
    for i,guessphase in enumerate(guessphases):
        modelydata = buildpulsetrain(tdata,guessperiod,guessphase,guesswidth) + guessbaseline
        chisqs[i] = np.sum(np.power(ydata - modelydata,2))

    guessphase = guessphases[np.argmin(chisqs)]
    modellightcurve,centers = buildpulsetrain(tdata,guessperiod,guessphase,guesswidth,baseline=guessbaseline,full_output=True)

    # Get TOAs, residuals

    centers = centers[1:-1] #cut off the out-of-bounds ones
    toas = np.zeros_like(centers)
    errs = np.zeros_like(centers)
    Wefffac = 1.0/np.power(2*np.pi*np.log(2),0.25)
    amplitudes = np.zeros_like(centers)
    for i,center in enumerate(centers):
        inds = np.where(np.logical_and(tdata>center-0.5*guessperiod,tdata<center+0.5*guessperiod))[0]
        out = ffit.gaussianfit(tdata[inds],ydata[inds],guesswidth,baseline=True)
        toas[i] =  out[0][1] % guessperiod
        amplitudes[i] = out[0][0]
        s_sq = (ffit.errgaussian(out[0],tdata[inds],ydata[inds],guesswidth,baseline=True)**2).sum()/(len(inds)-len(out[0]))
        
        '''
        S = pout[0]
        N = np.std(diffs)
        SN = S/N
        Nphi = len(inds)
        FWHM = FWHMfac*guesswidth#pout[2]
        Weff = Wefffac*np.sqrt(FWHM*guessperiod) #gaussian
        errs[i] = Weff/(SN*np.sqrt(Nphi)) #more of a theoretical calculation
        '''
        errs[i] = np.sqrt(out[1][1,1]*s_sq)
    residtimes = centers
    residvals = toas - np.mean(toas)
    residerrs = errs

    ax_residcurve.errorbar(residtimes,residvals,yerr=residerrs,fmt='k.')



    # Re-adjust modelydata to account for amplitudes
    modelydata = buildpulsetrain(tdata,guessperiod,guessphase,guesswidth,amplitudes=amplitudes) + guessbaseline
    ax_lightcurve.plot(tdata,modelydata,'b')
    


    #var_message.set(str(np.sum(np.power(tprimes,2))/(len(tmaxima)-1))) #dof
    

    #ax_residcurve.plot(tmaxima,tprimes,'bo')
    #ax_residcurve.set_xlim(ax_audiocurve.get_xlim())

    #ax_residcurve.axhline(y=0,color='0.50')
        
    redraw_axes()




def refresh():
    return


redraw_axes()

#only for testing!
#NavigationToolbar2TkAgg calls pack(), must put inside separate frame to work with grid()
toolbarframe = Tk.Frame(mainframe)
toolbarframe.grid(row=2,stick=Tk.W)
toolbar = NavigationToolbar2TkAgg(canvas, toolbarframe)
toolbar.update()
toolbar.grid(row=1,sticky=Tk.W)

separator = Tk.Frame(mainframe,width=600,height=2,bg=SEPARATOR_COLOR,bd=1, relief=Tk.SUNKEN).grid(row=3,pady=2)

frame_buttons = Tk.Frame(mainframe)
frame_buttons.grid(row=4,sticky=Tk.W)




frame_record = Tk.Frame(frame_buttons)
frame_record.grid(row=0,column=0,padx=12,pady=2)



label_duration = Tk.Label(frame_record,text="Recording Duration [s]:")
label_duration.pack()#grid(row=0,column=0)#columnspan=2)#row=0,column=0,columnspan=2)
#blank = Tk.Label(frame_record,text=" ")
#blank.grid(row=0,column=1)
entry_duration = Tk.Entry(frame_record,width=7,textvariable=var_duration)
entry_duration.pack()#grid(row=1,column=0)

button_record = Tk.Button(frame_record,text="Record",command=update_main)
button_record.pack()#grid()#row=1,column=1)

#button_clear = Tk.Button(frame_record,text="Clear",command=clear_all)
#button_clear.pack()#grid()#row=1,column=1)


#blank = Tk.Label(frame_record,text=" ")
#blank.grid(row=2,column=1)


#button_redrawclear = Tk.Button(frame_period,text="Update",command=lambda: update_mainclear())
#button_redrawclear.grid(row=2,column=1)
#button_redraw = Tk.Button(frame_period,text="Redraw",command=lambda: update_main())
#button_redraw.grid(row=2,column=0)



separator = Tk.Frame(frame_buttons,width=2,height=100, bg=SEPARATOR_COLOR,bd=1, relief=Tk.SUNKEN).grid(row=0,column=1,padx=2)




frame_parameters = Tk.Frame(frame_buttons)
frame_parameters.grid(row=0,column=2)


#checkbutton_model = Tk.Checkbutton(frame_parameters,text="Fit Model",variable=var_fits_on,command=fit_model)#lambda: update_main(mode=-1))
#checkbutton_model.grid(row=0,column=0)
#checkbutton_model.toggle()

label_period = Tk.Label(frame_parameters,text="Pulse Period [s]:")
label_period.grid(row=1,column=0)
entry_period = Tk.Entry(frame_parameters,width=7,textvariable=var_pulseperiod)
entry_period.grid(row=1,column=1)

label_width = Tk.Label(frame_parameters,text="Pulse Width [s]:")
label_width.grid(row=2,column=0)
entry_width = Tk.Entry(frame_parameters,width=7,textvariable=var_pulsewidth)
entry_width.grid(row=2,column=1)

button_updatemodel = Tk.Button(frame_parameters,text="Update Model",command=fit_model)
button_updatemodel.grid(row=3,column=1)
#button_clearmaxima = Tk.Button(frame_parameters,text="Clear TOAs",command=lambda: update_main(clear=True))
#button_clearmaxima.grid(row=4,column=1)



'''
label_phase = Tk.Label(frame_parameters,text="Orbital Phase [s]:")
label_phase.grid(row=1,column=2)
entry_phase = Tk.Entry(frame_parameters,width=7,textvariable=var_phase)
entry_phase.grid(row=1,column=3)

label_period = Tk.Label(frame_parameters,text="Orbital Period [s]:")
label_period.grid(row=2,column=2)
entry_period = Tk.Entry(frame_parameters,width=7,textvariable=var_period)
entry_period.grid(row=2,column=3)


label_amplitude = Tk.Label(frame_parameters,text="Orbit Amplitude [s]:")
label_amplitude.grid(row=3,column=2)
entry_amplitude = Tk.Entry(frame_parameters,width=7,textvariable=var_amplitude)
entry_amplitude.grid(row=3,column=3)

label_amplitudeconv = Tk.Label(frame_parameters,text="Amplitude Conversion [m]:")
label_amplitudeconv.grid(row=4,column=2)
label_amplitudeconvnum = Tk.Label(frame_parameters,width=7,textvariable=var_amplitudeconv)
label_amplitudeconvnum.grid(row=4,column=3)
'''

separator = Tk.Frame(mainframe,width=600,height=2,bg=SEPARATOR_COLOR,bd=1, relief=Tk.SUNKEN).grid(row=5,pady=2)


label_message = Tk.Label(mainframe,textvariable=var_message)
label_message.grid(row=6)






## ----------
## Buttons/Menus
## ----------

def busy(msg="Working...",sleep=0):
    var_message.set(msg)
    root.config(cursor="watch")
    root.update()#_idletasks() #need to work through queued items
    if sleep!=0:
        time.sleep(sleep)
        notbusy()

def notbusy():
    var_message.set("")
    root.config(cursor="")


def popup_about():
    title="About"
    text=["West Virginia University Department of Physics and Astronomy",
          "Center for Gravitational Waves and Cosmology",
          "NANOGrav Physics Frontiers Center",
          "Python code by Michael Lam 2017"]
    d = window_popup(root,title,text,WIDTH=50)
    root.wait_window(d.top)


def popup_commands():
    title="Commands"
    text=["Record: Record your lightcurve data",
          "",
          "Fit Model: Shows the results of your fitting of the model",
          "",
          "All parameters are set to 0 by default."]
    d = window_popup(root,title,text,WIDTH=50)
    root.wait_window(d.top)





class window_popup:
    def __init__(self,parent,title,txt,WIDTH=40):
        top = self.top = Tk.Toplevel(parent)
        top.title(title)
        top.geometry('+150+250')
        top.bind("<Return>",lambda event:self.ok())
        for i in range(len(txt)):
            if txt[i][:5]=="image":
                photo = eval(txt[i])
                label=Tk.Label(top,image=photo)
                label.image = photo # keep a reference!
                label.pack()
            else:
                Tk.Label(top,anchor=Tk.W,width=WIDTH,text=txt[i]).pack()
        b = Tk.Button(top,text="OK",command=self.ok)
        b.pack()
        b.focus_set()
    def ok(self):
        self.top.destroy()



def destroy(event):
    sys.exit()



## Bindings
#root.bind("<Return>",superdo)
root.bind("<Escape>", destroy)
root.bind("<Control-q>", destroy)
root.bind("<F1>",lambda event: popup_about())
root.bind("<F2>",lambda event: popup_commands())
#root.bind("<F3>",lambda event: popup_equations())
root.bind("<F10>",destroy)
root.bind("<F11>",lambda event: update_maintesting())





menubar = Tk.Menu(root)

filemenu = Tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="Exit",accelerator="Esc", command=root.quit)
menubar.add_cascade(label="File", menu=filemenu)

helpmenu = Tk.Menu(menubar, tearoff=0)
helpmenu.add_command(label="About",accelerator="F1", command=popup_about)
helpmenu.add_command(label="Commands",accelerator="F2", command=popup_commands)
helpmenu.add_command(label="Test Data",accelerator="F11", command=update_maintesting)
menubar.add_cascade(label="Help", menu=helpmenu)

# display the menu
root.config(menu=menubar)


root.mainloop()

