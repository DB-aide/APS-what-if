"""
Version 1.0.1 14-01-2026 Made the dialog async (so the GUI doesn't freeze during long emulations)
Version 1.0.0 12-01-2026 Error handling for the Manage Inputs and Outputs for Emulating AAPS Settings dialog. 
                         If there are no *.zip files yet, a message will be displayed to the user.
                         Dialog updated and folders are correct for all OS versions.
                         The config.py file now contains the folder variables.
                         And a new file i18n.py with error messages in it.

"""
import  os, sys
import  glob
import  traceback
from datetime import datetime
import subprocess

from tkinter import Tk, StringVar, Text, VERTICAL, HORIZONTAL, W, E, S, N
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

from emulator_core import parameters_known
from emulator_core import set_tty
from emulator_core import sub_issue

from emulator_core import get_version_core
from determine_basal import get_version_determine_basal
from config import DEFAULT_WDIR, AAPS_LOGS_DIR, DEFAULT_AAPS_ZIP_PATTERN, DEFAULT_ROOT
from i18n import _ # Error handling for the multilingual dialog.
import threading
import queue
import time

gui_queue = queue.Queue()
emul_thread = None
# select the optional start and end date/time     -----------------------------
ENABLED = '!disabled'
noStart = '2000-01-01T00:00:00Z'
noStopp = '2099-12-31T23:59:59Z'
# bovenin (of net vóór GUI-opbouw)
logfil_entry = None

def gui_log(msg, tag=None):
    gui_queue.put((msg, tag))

def process_gui_queue():
    try:
        while True:
            msg, tag = gui_queue.get_nowait()
            lfd.configure(state='normal')
            if tag:
                lfd.insert('end', msg + '\n', tag)
            else:
                lfd.insert('end', msg + '\n')
            lfd.configure(state='disabled')
            lfd.see('end')
    except queue.Empty:
        pass

    root.after(100, process_gui_queue)   # blijf pollen

def emulation_worker():
    try:
        gui_log("Starting emulation...")
        time.sleep(1)

        # === HIER jouw echte emulatie ===
        for i in range(5):
            gui_log(f"Processing step {i+1}/5")
            time.sleep(1)

        gui_log("Emulation finished successfully")
        runState.set("DONE")
    except Exception as e:
        gui_log(f"ERROR: {e}", tag="issue")
        runState.set("ERROR")

def clear_msg():
    lfd.configure(state='normal')
    lfd.delete("1.0", "end")
    lfd.configure(state='disabled')

def check_aaps_logs_present():
    if not list(AAPS_LOGS_DIR.glob("*.zip")):
        messagebox.showerror(
            _("no_logs_title"),
            _("no_logs_msg", path=AAPS_LOGS_DIR)
        )
        return False
    return True

def focus_widget(widget, delay=0):
    """
    Safely give keyboard focus to a widget after GUI updates.
    """
    if delay == 0:
        root.after_idle(widget.focus_set)
    else:
        root.after(delay, widget.focus_set)

def select_tab_and_focus(tab, widget):
    """
    Select a notebook tab and focus a widget inside it.
    """
    book.select(tab)
    focus_widget(widget)

def add_file_selector(
    parent,
    row,
    label_text,
    text_var,
    browse_cmd,
    show_cmd=None,
    entry_width=None,
    pady=(10, 2)
):
    """
    Adds a standardized file selector row:
    Label
    Entry
    Browse button
    Optional Show/Edit button
    """

    # Label
    ttk.Label(parent, text=label_text)\
        .grid(column=0, row=row, columnspan=2, sticky="W", padx=5, pady=pady)

    # Entry
    ttk.Entry(parent, textvariable=text_var, width=entry_width)\
        .grid(column=0, row=row + 1, columnspan=2, sticky="EW", padx=5)

    # Browse button
    ttk.Button(parent, text="Browse", command=browse_cmd)\
        .grid(column=2, row=row + 1, sticky="EW", padx=5)

    # Optional Show/Edit button
    if show_cmd:
        ttk.Button(parent, text="Show", command=show_cmd)\
            .grid(column=3, row=row + 1, sticky="EW", padx=5)

    return row + 2

def get_version_GUI(echo_msg):
    echo_msg['emulator_GUI.py'] = '2026-01-12 11:40'        # Dialog updated. And folders are correct for all OS versions. The config.py file now contains the folder variables.
    #echo_msg['emulator_GUI.py'] = '2025-07-20 17:04'       # align camelPrint of bestSlope with bestParabola
    #cho_msg['emulator_GUI.py'] = '2024-04-25 16:24'
    return echo_msg

def get_wdir():
    # always start the directory browser in the default working directory
    default_wdir = str(DEFAULT_WDIR)
    wdir.set(default_wdir)

    newwd = filedialog.askdirectory(initialdir=default_wdir)
    if newwd != "":
        wdir.set(newwd)

def reset_all():
    # input frame
    default_wdir = str(DEFAULT_WDIR)
    wdir.set(default_wdir)

    stmpStart.set('yes')
    tstart_entry.state(['!disabled'])
    tstart.set(noStart)

    stmpStopp.set('yes')
    tstopp.set(noStopp)
    tstopp_entry.state(['!disabled'])
    chkStopp.state(['!disabled'])

    # variant frame
    radioMost()

    # run frame
    runState.set(notRunning)
    clear_msg()

    # result frame – everything back to DEFAULT_WDIR
    logfil.set(str(DEFAULT_WDIR))
    tabfil.set(str(DEFAULT_WDIR))
    deltafil.set(str(DEFAULT_WDIR))
    txtorig.set(str(DEFAULT_WDIR))
    txtemul.set(str(DEFAULT_WDIR))
    pdffil.set(str(DEFAULT_WDIR))
    vfil = StringVar()
    try:
        demo_path = DEFAULT_ROOT
    except Exception:
        demo_path = DEFAULT_ROOT + os.sep + 'Demo_Sports_Adaptations.vdf'
    if os.path.exists(demo_path):
        demo_path = os.path.join(os.getcwd(), 'Demo_Sports_Adaptations.vdf')
        vfil.set(demo_path)

    
def gui_quit():
    really = messagebox.askyesno(
        message='Are you sure you want to quit this GUI?', icon='question', title='Quit ?', default='no')
    if really:
        root.destroy()
        exit()                                                                  # from tkinter
        sys.exit                                                                # from python

def get_vfil():
    newvf = filedialog.askopenfilename(filetypes={'Variation {.vdf .dat}'}, initialdir=DEFAULT_ROOT)
    if newvf != "":
        vfil.set(newvf)

def edit_vfil():
    oldvf = vfil.get()
    open_file(oldvf)

#   select the AAPS logfile(s)  -------------------------------------------------
def get_afil():
    loglist = {'logs {.zip .0 .1 .2 .3 .4 .5 .6 .7 .8 .9 .10 .11 .12 .13 .14 .15 .16}'}  # my own max was 11 !!
    # start in the aapsLogs folder (fallback to default_wdir)
    startdir = aaps_logs_dir if os.path.exists(aaps_logs_dir) else default_wdir
    initialfile = os.path.basename(default_afil) if default_afil else '*.zip'
    newaf = filedialog.askopenfilename(filetypes=loglist, initialdir=startdir, initialfile=initialfile)
    if newaf != "":
        afil.set(newaf)

def show_afil():
    newaf = afil.get()
    if newaf.find("*")<0 and newaf.find("?")<0:    
        msg = "No wild card match specified.\nInsert '*' or '?' at the appropriate position"
    else:
        msg = ""
        log_liste = glob.glob(newaf, recursive=False)                            # the wild card match
        filecount = 0
        for fn in log_liste:
            ftype = fn[len(fn)-3:]
            if ftype=='zip' or ftype.find(".")>=0:
                msg += os.path.basename(fn) + "\n"
                filecount += 1
        msg +="\nTotal match count: " + str(filecount)
    messagebox.showinfo(message=msg, title="List matching logfiles", icon="info")

def stmpStartChanged():
    if stmpStart.get() == 'yes':
        tstart_entry.state([ENABLED])
        chkStopp.state([ENABLED])
    else:
        tstart_entry.state(['disabled'])
        tstopp_entry.state(['disabled'])
        chkStopp.state(['disabled'])

def stmpStoppChanged():
    if stmpStopp.get() == 'yes':
        tstopp_entry.state([ENABLED])
    else:
        tstopp_entry.state(['disabled'])

#################################################################################
#   overall layout                                                              #
#                                                                               #
#   +----------------------------------------------------------------------+    #
#   |   ROW 0 / COL 0:  frame for WD definition                            |    #
#   +----------------------------------------------------------------------+    #
#   |   ROW 1 / COL 0:  Notebook tabs                                      |    #
#   |   +-----------------------------------------------------------+      |    #
#   |   |  Tab1: Inputs     | tab2: Graphics    | tab3: Results     |      |    #
#   |                                                                      |    #
#   |                                                                      |    #
#   |                                                                      |    #
#   +----------------------------------------------------------------------+    #
#################################################################################
root = Tk()
root.title('Manage Inputs and Outputs for Emulating AAPS Settings')
root.columnconfigure(0, weight=1)
root.rowconfigure(2, weight=1)
ttk.Sizegrip(root).grid(column=999, row=999, sticky=(S,E))

book = ttk.Notebook(root)
book.columnconfigure(0, weight=1)
book.rowconfigure(0, weight=1)
tStyle = ttk.Style()
tStyle.configure(
    'Bold.TNotebook.Tab',
    font=('TkDefaultFont', 10, 'bold'),
    padding=[5, 5]
)

book['style'] = 'Bold.TNotebook'
book.grid(column=0, row=2, columnspan=4, sticky='NSEW', padx=10, pady=20)
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(2, weight=1)

inpframe = ttk.Frame(book, relief='raised')
outframe = ttk.Frame(book, relief='raised')
resframe = ttk.Frame(book, relief='raised')
runframe = ttk.Frame(book, relief='raised')

for frame in (inpframe, outframe, runframe, resframe):
    frame.grid_columnconfigure(0, weight=1)

book.add(inpframe, text='Select Inputs')
book.add(outframe, text='Select Graphics Options')
book.add(runframe, text='Execute the Analysis')
book.add(resframe, text='Inspect Results')
process_gui_queue()

#################################################################################
#   wdframe:                                                                    #
#################################################################################
#   select the working directory    ---------------------------------------------

wdframe = ttk.Frame(root, padding="3 3 3 12", relief='raised')
wdframe.grid(column=0, row=0, columnspan=4, sticky='WENS')
wdir = StringVar()
        
ttk.Label(wdframe, text="Your working directory").grid(column=0, columnspan=3, row=0, sticky=(W,E), padx=5)
default_wdir = str(DEFAULT_WDIR)
wdir.set(default_wdir)
aaps_logs_dir = str(AAPS_LOGS_DIR)
default_afil = str(DEFAULT_AAPS_ZIP_PATTERN)
wdir_entry = ttk.Entry(wdframe, width=100, textvariable=wdir)
wdir_entry.grid(column=0, columnspan=3, row=1, sticky=(W, E), padx=5)

ttk.Button(wdframe, text="Browse", command=get_wdir).grid(column=3, row=1, sticky=(W,E), padx=10)
ttk.Button(wdframe, text="Reset All", command=reset_all).grid(column=4, row=1, sticky=(W,E), padx=5)
tStyle.configure('Exit.TButton', foreground='red')
ttk.Button(wdframe, text="Quit",   command=gui_quit, style='Exit.TButton').grid(column=5, row=1, sticky=(W,E), padx=10)
# same as QUIT button so matplotlib is closed, too:
root.protocol("WM_DELETE_WINDOW", gui_quit)

#################################################################################
#   inpframe:                                                                   #
#################################################################################
#   select the variant definition file  -----------------------------------------

# -------------------------------------------------
# Grid setup (1x!)
# -------------------------------------------------
for c in range(4):
    inpframe.columnconfigure(c, weight=1)

row = 0

# -------------------------------------------------
# Variant definition file
# -------------------------------------------------
vfil = StringVar()
demo_path = os.path.join(DEFAULT_ROOT, 'Demo_Sports_Adaptations.vdf')
if os.path.exists(demo_path):
    vfil.set(demo_path)

row = add_file_selector(
    parent=inpframe,
    row=row,
    label_text="Your variant definition file",
    text_var=vfil,
    browse_cmd=get_vfil,
    show_cmd=edit_vfil
)

# -------------------------------------------------
# AAPS logfile(s)
# -------------------------------------------------
afil = StringVar()
if 'default_afil' in globals() and default_afil:
    afil.set(default_afil)

row = add_file_selector(
    parent=inpframe,
    row=row,
    label_text="Your AAPS logfile(s)",
    text_var=afil,
    browse_cmd=get_afil,
    show_cmd=show_afil
)

# -------------------------------------------------
# Start / Stop time selection
# -------------------------------------------------
ttk.Label(
    inpframe,
    text="example date/time format ...   2019-11-06T12:30:00Z"
).grid(column=1, row=row, sticky="E", padx=5, pady=(15, 2))

row += 1

stmpStart = StringVar(value='yes')
chkStart = ttk.Checkbutton(
    inpframe,
    text='Use start time by entering UTC date/time',
    command=stmpStartChanged,
    variable=stmpStart,
    onvalue='yes',
    offvalue='no'
)
chkStart.grid(column=0, row=row, sticky="W", padx=5)

tstart = StringVar(value=noStart)
tstart_entry = ttk.Entry(inpframe, width=20, textvariable=tstart)
tstart_entry.grid(column=1, row=row, sticky="E", padx=5)

row += 1

stmpStopp = StringVar(value='yes')
chkStopp = ttk.Checkbutton(
    inpframe,
    text='Use final time by entering UTC date/time',
    command=stmpStoppChanged,
    variable=stmpStopp,
    onvalue='yes',
    offvalue='no'
)
chkStopp.grid(column=0, row=row, sticky="W", padx=5)

tstopp = StringVar(value=noStopp)
tstopp_entry = ttk.Entry(inpframe, width=20, textvariable=tstopp)
tstopp_entry.grid(column=1, row=row, sticky="E", padx=5)

# initial states
stmpStartChanged()
stmpStoppChanged()

# -------------------------------------------------
# Keep everything at the top
# -------------------------------------------------
inpframe.grid_rowconfigure(row + 1, weight=1)


#################################################################################
#   outframe:   select the graphics options                                     #
#################################################################################
def clearchecks():
    global useinsReq
    
    useinsReq.set('off')
    usemaxBolus.set('off')
    useSMB.set('off')
    usebasal.set('off')
    useinsReq.set('off')
    usebg.set('off')
    usetarget.set('off')
    usecob.set('off')
    useiob.set('off')
    useactivity.set('off')
    useas_ratio.set('off')
    useai_ratio.set('off')
    userange.set('off')
    usebestslope.set('off')
    usefitsslope.set('off')
    usebestparabola.set('off')
    usefitsparabola.set('off')
    useISF.set('off')
    if raw.get() == 'most':
        usepred.set('on')
        useflow.set('on')
    else:
        usepred.set('off')
        useflow.set('off')
    
def optionLabels(show):
    chkinsReq['text']   = show + ' insulin required'
    chkmaxBolus['text'] = show + ' max bolus limit'
    chkSMB['text']      = show + ' SMB'
    chkbasal['text']    = show + ' basal rate'
    
    chkbg['text']       = show + ' glucose'
    chktarget['text']   = show + ' targets'
    chkcob['text']      = show + ' COB'
    chkiob['text']      = show + ' IOB'
    chkactivity['text'] = show + ' insulin activity'
    chkas_ratio['text'] = show + ' autosense ratio'
    chkai_ratio['text'] = show + ' autoISF ratio'
    chkrange['text']    = show + ' range parameters'
    chkbestslope['text']    = show + ' best slope'
    chkfitsslope['text']    = show + ' other slopes'
    chkbestparabola['text'] = show + ' best parabola'
    chkfitsparabola['text'] = show + ' other parabolas'
    chkISF['text']      = show + ' ISF'
    chkpred['text']     = show + ' predictions'
    
    chkflow['text']     = show + ' flowchart'

def act(using, thisOpt):
    global doit
    txt = doit.get('1.0', 'end')[:-1]
    addornot = raw.get()
    if addornot == 'most':
        what = '-' + thisOpt                                                    # suppress option flag
    else:
        what = thisOpt                                                          # use option flag
    wo = txt.find(what)
    if wo>=0:
        if using == 'off':
            txt = txt[:wo] + txt[wo+len(what):]                                 # deleted the option from list
        # final clean ups
        txt = txt.replace('//', '/')
        if len(txt)>0:
            if '/' == txt[0]:             txt = txt[1:]
            if '/' == txt[len(txt)-1]:    txt = txt[:-1]
    elif using == 'on':
        if len(txt) > 0:    txt += '/'
        txt += what
    doit.delete('1.0', 'end')
    doit.insert('end', txt)                                                     # update displayed content
    pass
    
def radioAll():
    optHeader.set("\n                                                                                       ")                
    raw.set('All')
    doit.delete('1.0', 'end')
    doit.insert('end', 'All/'+useLIST.get())
    flowframe.grid_remove()
    glucframe.grid_remove()
    isf_frame.grid_remove()
    insuframe.grid_remove()
    noframe.grid()
    clearchecks()
    
def radioMost():
    optHeader.set("\nFine grained selection of items to be excluded")                
    raw.set('most')
    doit.delete('1.0', 'end')
    clearchecks()
    insuframe.grid()
    glucframe.grid()
    isf_frame.grid()
    flowframe.grid()
    noframe.grid_remove()
    doit.insert('end', 'All/-pred/-flowchart/'+useLIST.get())
    optionLabels('Hide')

def radioSome():
    optHeader.set("\nFine grained selection of items to be included")                
    raw.set('some')
    doit.delete('1.0', 'end')
    doit.insert('end', useLIST.get())
    clearchecks()
    insuframe.grid()
    glucframe.grid()
    isf_frame.grid()
    flowframe.grid()
    noframe.grid_remove()
    optionLabels('Show')

def radioComma():
    decim.set(',')
    
def radioPeriod():
    decim.set('.')

outframe.columnconfigure(1, weight=1)
outframe.columnconfigure(2, weight=1)
outframe.columnconfigure(3, weight=1)
ttk.Label(outframe, text="\nThe resulting graphics request string").grid(column=1, row=0, columnspan=3, padx=5, sticky=(W))
doit = Text(outframe, state='normal', width=76, height=1)                       # w=77 equals w=80 for Entry
doit.grid(column=1, row=1, columnspan=3, padx=5, sticky='w')

tStyle.configure('Blau.TLabelframe.Label', foreground='blue')
optHeader = StringVar()
ttk.Label(outframe, textvariable=optHeader).grid(column=2, row=19, columnspan=3, padx=5, sticky=(W))
insuframe = ttk.Labelframe(outframe, width=250, height=400, text="Insulin chart content", style='Blau.TLabelframe')
insuframe.grid(row= 20, column=2, padx=20, pady=5, sticky=(W,N))
glucframe = ttk.Labelframe(outframe, width=250, height=400, style='Blau.TLabelframe', text='Glucose chart content          ') # same width as autoISF frame
glucframe.grid(row= 20, column=3, padx=20, pady=5, sticky=(W,N))
isf_frame = ttk.Labelframe(outframe, width=250, height=400, style='Blau.TLabelframe', text='specials, e.g. autoISF')
isf_frame.grid(row= 30, column=3, padx=20, pady=5, sticky=(W,N))
flowframe = ttk.Labelframe(outframe, width=250, height=400, style='Blau.TLabelframe', text="Flowchart ON/OFF")
flowframe.grid(row= 20, column=4, padx=20, pady=0, sticky=(W,N))
noframe = ttk.Labelframe(outframe, width=510, height=100, text='')
noframe.grid(row=20, column=2, columnspan=3, padx=20, pady=5, sticky=(W,N))

#   insulin chart options     --------------------------------------------------
def useinsReqChanged():     act(useinsReq.get(), "insReq")
useinsReq = StringVar()
chkinsReq = ttk.Checkbutton(insuframe, text='Show insulin required', \
            command=useinsReqChanged, variable=useinsReq, onvalue='on', offvalue='off')
chkinsReq.grid(column=0, row=1, columnspan=2, sticky=(W), padx=5)

def usemaxBolusChanged():   act(usemaxBolus.get(), "maxBolus")
usemaxBolus = StringVar()
chkmaxBolus = ttk.Checkbutton(insuframe, text='Show max bolus limit', \
            command=usemaxBolusChanged, variable=usemaxBolus, onvalue='on', offvalue='off')
chkmaxBolus.grid(column=0, row=2, columnspan=2, sticky=(W), padx=5)

def useSMBChanged():        act(useSMB.get(), "SMB")
useSMB = StringVar()
chkSMB = ttk.Checkbutton(insuframe, text='Show SMB', \
            command=useSMBChanged, variable=useSMB, onvalue='on', offvalue='off')
chkSMB.grid(column=0, row=3, columnspan=2, sticky=(W), padx=5)

def usebasalChanged():      act(usebasal.get(), "basal")
usebasal = StringVar()
chkbasal = ttk.Checkbutton(insuframe, text='Show basal rate', \
            command=usebasalChanged, variable=usebasal, onvalue='on', offvalue='off')
chkbasal.grid(column=0, row=4, columnspan=2, sticky=(W), padx=5)

#   glucose chart options   --------------------------------------------------
def usepredChanged():       act(usepred.get(), "pred")
usepred = StringVar()
chkpred = ttk.Checkbutton(glucframe, text='Show predictions', \
            command=usepredChanged, variable=usepred, onvalue='on', offvalue='off')
chkpred.grid(column=0, row=1, columnspan=2, sticky=(W), padx=5)

def usebgChanged():         act(usebg.get(), "bg")
usebg = StringVar()
chkbg = ttk.Checkbutton(glucframe, text='Show glucose', \
            command=usebgChanged, variable=usebg, onvalue='on', offvalue='off')
chkbg.grid(column=0, row=2, columnspan=2, sticky=(W), padx=5)

def usetargetChanged():     act(usetarget.get(), "target")
usetarget = StringVar()
chktarget = ttk.Checkbutton(glucframe, text='Show targets', \
            command=usetargetChanged, variable=usetarget, onvalue='on', offvalue='off')
chktarget.grid(column=0, row=3, columnspan=2, sticky=(W), padx=5)

def usecobChanged():        act(usecob.get(), "cob")
usecob = StringVar()
chkcob = ttk.Checkbutton(glucframe, text='Show COB', \
            command=usecobChanged, variable=usecob, onvalue='on', offvalue='off')
chkcob.grid(column=0, row=4, columnspan=2, sticky=(W), padx=5)

def useiobChanged():        act(useiob.get(), "iob")
useiob = StringVar()
chkiob = ttk.Checkbutton(glucframe, text='Show IOB', \
            command=useiobChanged, variable=useiob, onvalue='on', offvalue='off')
chkiob.grid(column=0, row=5, columnspan=2, sticky=(W), padx=5)

def useactivityChanged():   act(useactivity.get(), "activity")
useactivity = StringVar()
chkactivity = ttk.Checkbutton(glucframe, text='Show insulin activity', \
            command=useactivityChanged, variable=useactivity, onvalue='on', offvalue='off')
chkactivity.grid(column=0, row=6, columnspan=2, sticky=(W), padx=5)

def useas_ratioChanged():   act(useas_ratio.get(), "as_ratio")
useas_ratio = StringVar()
chkas_ratio = ttk.Checkbutton(glucframe, text='Show autosense ratio', \
            command=useas_ratioChanged, variable=useas_ratio, onvalue='on', offvalue='off')
chkas_ratio.grid(column=0, row=7, columnspan=2, sticky=(W), padx=5)

#   glucose chart, subchart autoISF options   --------------------------------------------------
def useai_ratioChanged():   act(useai_ratio.get(), "autoISF")
useai_ratio = StringVar()
chkai_ratio = ttk.Checkbutton(isf_frame, text='Show autoISF ratio', \
            command=useai_ratioChanged, variable=useai_ratio, onvalue='on', offvalue='off')
chkai_ratio.grid(column=0, row=7, columnspan=2, sticky=(W), padx=5)

def userangeChanged():   act(userange.get(), "range")
userange = StringVar()
chkrange = ttk.Checkbutton(isf_frame, text='Show range', \
            command=userangeChanged, variable=userange, onvalue='on', offvalue='off')
chkrange.grid(column=0, row=8, columnspan=2, sticky=(W), padx=5)

def usebestslopeChanged():   act(usebestslope.get(), "bestSlope")
usebestslope = StringVar()
chkbestslope = ttk.Checkbutton(isf_frame, text='Show best slope', \
            command=usebestslopeChanged, variable=usebestslope, onvalue='on', offvalue='off')
chkbestslope.grid(column=0, row=9, columnspan=2, sticky=(W), padx=5)

def usefitsslopeChanged():   act(usefitsslope.get(), "fitsSlope")
usefitsslope = StringVar()
chkfitsslope = ttk.Checkbutton(isf_frame, text='Show other slopes', \
            command=usefitsslopeChanged, variable=usefitsslope, onvalue='on', offvalue='off')
chkfitsslope.grid(column=0, row=10, columnspan=2, sticky=(W), padx=5)

def usebestparabolaChanged():   act(usebestparabola.get(), "bestParabola")
usebestparabola = StringVar()
chkbestparabola = ttk.Checkbutton(isf_frame, text='Show best parabola', \
            command=usebestparabolaChanged, variable=usebestparabola, onvalue='on', offvalue='off')
chkbestparabola.grid(column=0, row=11, columnspan=2, sticky=(W), padx=5)

def usefitsparabolaChanged():   act(usefitsparabola.get(), "fitsParabola")
usefitsparabola = StringVar()
chkfitsparabola = ttk.Checkbutton(isf_frame, text='Show other parabolas', \
            command=usefitsparabolaChanged, variable=usefitsparabola, onvalue='on', offvalue='off')
chkfitsparabola.grid(column=0, row=12, columnspan=2, sticky=(W), padx=5)

def useISFChanged():   act(useISF.get(), "ISF")
useISF = StringVar()
chkISF = ttk.Checkbutton(isf_frame, text='Show ISF', \
            command=useISFChanged, variable=useISF, onvalue='on', offvalue='off')
chkISF.grid(column=0, row=13, columnspan=2, sticky=(W), padx=5)

#   flowchart options     ------------------------------------------------------
def useflowChanged():       act(useflow.get(), "flowchart")
useflow = StringVar()
chkflow = ttk.Checkbutton(flowframe, text='Create flowchart', \
            command=useflowChanged, variable=useflow, onvalue='on', offvalue='off')
chkflow.grid(column=0, row=1, columnspan=2, sticky=(W), padx=5)

#   suppress interactive listing     ---------------------------------------------

def actLIST(what):
    global doit
    txt = doit.get('1.0', 'end')[:-1]
    #addornot = raw.get()
    wo = txt.find(what[1:])                                                     # w/o potential "-" sign
    if wo>=0:
        if what[0] == '-':
            txt = txt[:wo] + '-' + txt[wo:]                                     # inserted the "-" sign
        else:
            txt = txt[:wo-2]     + txt[wo-1:]                                   # take out the "-" sign
    else:
        if len(txt) > 0:    txt += '/'
        txt += what
    doit.delete('1.0', 'end')
    doit.insert('end', txt)                                                     # update displayed content
    pass
    
def useLISTChanged():       actLIST(useLIST.get())
useLIST = StringVar()
chkLIST = ttk.Checkbutton(outframe, text='show interactive result listing', \
            command=useLISTChanged, variable=useLIST, onvalue='LIST', offvalue='-LIST')
chkLIST.grid(column=3, row=11, columnspan=1, sticky=(W), padx=25)
useLIST.set('LIST')

#   this selects the decimal symbol
ttk.Label(outframe, text="\nSelect the decimal symbol for output tables").grid(column=1, row=2, columnspan=1, padx=5, sticky=(W))
decim = StringVar()
comma = ttk.Radiobutton(outframe, variable=decim, value=',', command=radioComma,  text='use ","')
period= ttk.Radiobutton(outframe, variable=decim, value='.', command=radioPeriod, text='use "."')
radioComma()                                                                     # initial default
comma.grid(column=1,  row=11, padx=20, sticky=W)
period.grid(column=1, row=12, padx=20, sticky=W)

#   this is placed last because their commands refer to above defs
ttk.Label(outframe, text="\nCoarse grained selection of graphics output").grid(column=2, row=2, columnspan=3, padx=5, sticky=(W))
raw  = StringVar()
some = ttk.Radiobutton(outframe, variable=raw, value='some', command=radioSome, text='just a few')
most = ttk.Radiobutton(outframe, variable=raw, value='most', command=radioMost, text='most (i.e.  All but a few)')
all  = ttk.Radiobutton(outframe, variable=raw, value='All',  command=radioAll,  text='All')
radioMost()                                                                     # initial default
some.grid(column=2, row=11, columnspan=3, padx=20, sticky=W)
most.grid(column=2, row=12, columnspan=3, padx=20, sticky=W)
all.grid( column=2, row=13, columnspan=3, padx=20, sticky=W)


#################################################################################
#   resframe                                                                    #
#################################################################################
#   inspect the results     -----------------------------------------------------

def get_logfil():
    oldaf = logfil.get()
    loglist = {'logfile {.log}'}  
    newaf = filedialog.askopenfilename(filetypes=loglist, initialdir=default_wdir, initialfile=oldaf)
    if newaf != "":
        logfil.set(newaf)

def open_file(path):
    if not path:
        messagebox.showerror(message='No file specified to open', title='Open file')
        return
    if not os.path.exists(path):
        messagebox.showerror(message=f'File not found:\n{path}', title='Open file')
        return
    try:
        if sys.platform.startswith('win'):
            os.startfile(path)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path])
    except Exception:
        tb = sys.exc_info()[2]
        sub_issue('Problem opening file')
        for ele in traceback.format_tb(tb):
            sub_issue(ele[:-1])
        sub_issue(str(sys.exc_info()[1]))
        messagebox.showerror(message=f'Unable to open file:\n{path}', title='Open file')

def get_deltafil():
    oldaf = deltafil.get()
    loglist = {'deltafile {.delta}'}  
    newaf = filedialog.askopenfilename(filetypes=loglist, initialdir=default_wdir, initialfile=oldaf)
    if newaf != "":
        deltafil.set(newaf)

def get_tabfil():
    oldaf = tabfil.get()
    loglist = {'table {.csv .tab}'}  
    newaf = filedialog.askopenfilename(filetypes=loglist, initialdir=default_wdir, initialfile=oldaf)
    if newaf != "":
        tabfil.set(newaf)

def get_txtorig():
    oldaf = txtorig.get()
    loglist = {'orig_log {.orig.txt}'}  
    newaf = filedialog.askopenfilename(filetypes=loglist, initialdir=default_wdir, initialfile=oldaf)
    if newaf != "":
        txtorig.set(newaf)

def get_txtemul():
    oldaf = txtemul.get()
    loglist = {'emul_log {.txt}'}  
    newaf = filedialog.askopenfilename(filetypes=loglist, initialdir=default_wdir, initialfile=oldaf)
    if newaf != "":
        txtemul.set(newaf)

def get_pdffil():
    oldaf = pdffil.get()
    loglist = {'graphics {.pdf .jpg}'}  
    newaf = filedialog.askopenfilename(filetypes=loglist, initialdir=default_wdir, initialfile=oldaf)
    if newaf != "":
        pdffil.set(newaf)

def edit_logfil():
    oldvf = logfil.get()
    try:
        open_file(oldvf)
    except:                                                                     # catch *all* exceptions
        book.select(4)                                                          # activate result tab
        tb = sys.exc_info()[2]
        sub_issue("Problem in vary_GUI.py")
        for ele in traceback.format_tb(tb):
            sub_issue(ele[:-1])                                                 # sub appends <CR>
        sub_issue(str(sys.exc_info()[1]))

def edit_deltafil():
    oldvf = deltafil.get()
    try:
        open_file(oldvf)
    except:                                                                     # catch *all* exceptions
        book.select(4)                                                          # activate result tab
        tb = sys.exc_info()[2]
        sub_issue("Problem in vary_GUI.py")
        for ele in traceback.format_tb(tb):
            sub_issue(ele[:-1])                                                 # sub appends <CR>
        sub_issue(str(sys.exc_info()[1]))

def edit_tabfil():
    oldvf = tabfil.get()
    try:
        open_file(oldvf)
    except:                                                                     # catch *all* exceptions
        book.select(4)                                                          # activate result tab
        tb = sys.exc_info()[2]
        sub_issue("Problem in vary_GUI.py")
        for ele in traceback.format_tb(tb):
            sub_issue(ele[:-1])                                                 # sub appends <CR>
        sub_issue(str(sys.exc_info()[1]))

def edit_txtorig():
    oldvf = txtorig.get()
    try:
        open_file(oldvf)
    except:                                                                     # catch *all* exceptions
        book.select(4)                                                          # activate result tab
        tb = sys.exc_info()[2]
        sub_issue("Problem in vary_GUI.py")
        for ele in traceback.format_tb(tb):
            sub_issue(ele[:-1])                                                 # sub appends <CR>
        sub_issue(str(sys.exc_info()[1]))

def edit_txtemul():
    oldvf = txtemul.get()
    try:
        open_file(oldvf)
    except:                                                                     # catch *all* exceptions
        book.select(4)                                                          # activate result tab
        tb = sys.exc_info()[2]
        sub_issue("Problem in vary_GUI.py")
        for ele in traceback.format_tb(tb):
            sub_issue(ele[:-1])                                                 # sub appends <CR>
        sub_issue(str(sys.exc_info()[1]))

def edit_pdffil():
    oldvf = pdffil.get()
    try:
        open_file(oldvf)
    except:                                                                     # catch *all* exceptions
        book.select(4)                                                          # activate result tab
        tb = sys.exc_info()[2]
        sub_issue("Problem in vary_GUI.py")
        for ele in traceback.format_tb(tb):
            sub_issue(ele[:-1])                                                 # sub appends <CR>
        sub_issue(str(sys.exc_info()[1]))

book.grid(column=0, row=2, columnspan=4, sticky="NSEW", padx=10, pady=20)
root.grid_rowconfigure(2, weight=1)
root.grid_columnconfigure(0, weight=1)

row =0

def add_file_row(frame, label_text, var, browse_cmd, show_cmd, row):
    ttk.Label(frame, text=label_text).grid(
        column=0, columnspan=2, row=row, sticky=W, padx=5, pady=(10, 2)
    )
    ttk.Entry(frame, width=130, textvariable=var).grid(
        column=0, columnspan=3, row=row+1, sticky=(W, E), padx=5
    )
    ttk.Button(frame, text="Browse", command=browse_cmd).grid(
        column=3, row=row+1, sticky=W, padx=10
    )
    ttk.Button(frame, text="Show", command=show_cmd).grid(
        column=4, row=row+1, sticky=W, padx=10
    )
    return row + 2


logfil = StringVar()
row = add_file_row(
    resframe,
    "*.log - Your file showing edits from the variant assignments",
    logfil, get_logfil, edit_logfil, row
)

tabfil = StringVar()
row = add_file_row(
    resframe,
    "*.csv - Your table comparing key values of original vs emulation",
    tabfil, get_tabfil, edit_tabfil, row
)

deltafil = StringVar()
row = add_file_row(
    resframe,
    "*.delta - Your table comparing bg deltas of original vs emulation",
    deltafil, get_deltafil, edit_deltafil, row
)

txtorig = StringVar()
row = add_file_row(
    resframe,
    "*.orig.txt - Your short log of original analysis",
    txtorig, get_txtorig, edit_txtorig, row
)

txtemul = StringVar()
row = add_file_row(
    resframe,
    "*.txt - Your short log of emulated analysis",
    txtemul, get_txtemul, edit_txtemul, row
)

pdffil = StringVar()
row = add_file_row(
    resframe,
    "*.pdf etc. - Your graphic file comparing key values of original vs emulation",
    pdffil, get_pdffil, edit_pdffil, row
)

# all rows without weight
for r in range(row):
    resframe.grid_rowconfigure(r, weight=0)

# one empty row UNDER everything
resframe.grid_rowconfigure(row, weight=1)


#################################################################################
#   runframe: execute the emulation                                             #
#################################################################################

def clear_msg():
    lfd['state'] = 'normal'
    lfd.delete(1.0, 'end')
    lfd['state'] = 'disabled'
    
def echo_version(mdl):
    global echo_msg
    #mdl= 'vary_settings_batch.py'
    stamp = os.stat(varyHome + mdl)
    stposx= datetime.fromtimestamp(stamp.st_mtime)
    ststr = datetime.strftime(stposx, "%Y-%m-%d %H:%M:%S")
    echo_msg[ststr] = mdl
    return 

def sub_emul():
    global runState, varyHome
    global emul_thread
    global echo_msg

    if emul_thread and emul_thread.is_alive():
        messagebox.showinfo("Emulation running", "Emulation is already running.")
        return
    
    if not check_aaps_logs_present():
        return
    
    runState.set('Checking inputs ...   ')
    varyHome = DEFAULT_ROOT + os.sep
    gui_log("=" * 60)
    gui_log("Starting new emulation run")

    emul_thread = threading.Thread(
        target=emulation_worker,
        daemon=True
    )
    emul_thread.start()
    
    m  = '='*66+'\nEcho of software versions used\n'+'-'*66
    m +='\n vary_settings home directory  ' + varyHome
    
    echo_msg = {}
    echo_msg = get_version_GUI(echo_msg)
    echo_msg = get_version_core(echo_msg)
    echo_msg = get_version_determine_basal(echo_msg)
    for ele in echo_msg:
        m += '\n dated: '+echo_msg[ele] + '       module name: '+ele
    #m += '\n' + '='*66 + '\n'
    m += '\n'+'-'*66+'\nEcho of execution parameters used\n'+'-'*66
    m += '\nLogfile(s) to scan    ' + afil.get()

    ttk.Label(runframe, textvariable=runState, style='TLabel').grid(column=2, row=runRow, sticky=(W), padx=20, pady=10)
    incomplete = False                                              # update frame display
    variant = os.path.basename(vfil.get())                          # Get the file name for example: *.vdf
    if variant == '':
        sub_issue('variant definition file is missing')
        incomplete = True
    gopt = doit.get('1.0', 'end')[:-1]
    if gopt == '':
        sub_issue('graphics output options are missing')
        incomplete = True
    m += '\nOutput options        ' + gopt
    gopt = sys.platform + os.sep + gopt                                        # i.e. not in Android
    #m_default = ''
    #if gopt.find('.') >= 0 :
    #    my_decimal = '.'
    #elif gopt.find(',') >= 0 :
    #    my_decimal = ',' 
    #else:
    #    my_decimal = ','
    #    m_default = ' (default)'                   # the default
    my_decimal = decim.get()
    m += '\nDecimal symbol        ' + my_decimal
    if afil.get() == '':
        sub_issue('AndroidAPS logfile is missing')
        incomplete = True
    if stmpStart.get() == 'no':
        useStart = noStart
        m_default = ' (default)'
    else:
        useStart = tstart.get()
        if useStart == '':
            sub_issue('start time ticked but missing')
            incomplete = True
        m_default = ''
    m += '\nStart of time window  ' + useStart + m_default
    if stmpStopp.get() == 'no':
        useStopp = noStopp
        m_default = ' (default)'
    else:
        useStopp = tstopp.get()
        if useStopp == '':
            sub_issue('stop time ticked but missing')
            incomplete = True
        m_default = ''
    m += '\nEnd of time window    ' + useStopp + m_default
    m += '\n' + '='*66 + '\n'
    if incomplete:
        runState.set(notRunning)
        lfd['state'] = 'disabled'
        return                                                                  # no execution

    try:
        if not check_aaps_logs_present():
            return
        runState.set('Emulation started ...')
        # runframe.update()                                                       # update frame display
        select_tab_and_focus(runframe, lfd)

        #kick_off(afil.get(), gopt, variant, useStart, useStopp)
        entries = {}
        # _, thisTime, extraSMB, CarbReqGram, CarbReqTime, lastCOB, fn_first = parameters_known(afil.get(), gopt, vfil.get(), useStart, useStopp, entries, m, my_decimal)
        _raw = parameters_known(afil.get(), gopt, vfil.get(), useStart, useStopp, entries, m, my_decimal)

        if not isinstance(_raw, (list, tuple)):
            sub_issue(f"parameters_known returned non-iterable: {_raw}")
            _raw = [_raw]

        _expected = 7
        _defaults = [0, 'Z', 0, '', '', 0, '']

        if len(_raw) < _expected:
            sub_issue(f"parameters_known returned {len(_raw)} values, expected 7. Filling with defaults.")
            _raw = list(_raw) + _defaults[len(_raw):]

        if len(_raw) > _expected:
            sub_issue(f"parameters_known returned {len(_raw)} values, ignoring extra values.")

        _raw = _raw[:_expected]

        _, thisTime, extraSMB, CarbReqGram, CarbReqTime, lastCOB, fn_first = _raw

        if thisTime == 'SYNTAX':
            runState.set('Emulation halted ... ')
            ttk.Label(runframe, textvariable=runState, style='Error.TLabel').grid(column=2, row=runRow, sticky=(W), padx=20, pady=10)
            #sub_issue('Problem in VDF file. For details, see file "*.'+variant[:-4]+'.log"')
        elif thisTime == 'UTF8':
            runState.set('Emulation aborted ... ')
            ttk.Label(runframe, textvariable=runState, style='Error.TLabel').grid(column=2, row=runRow, sticky=(W), padx=20, pady=10)
        else:   
            runState.set('Emulation finished ..')
            ttk.Label(runframe, textvariable=runState, style='Done.TLabel').grid(column=2, row=runRow, sticky=(W), padx=20, pady=10)

            # load result filenames into resframe
            newaf = afil.get()
            log_liste = glob.glob(newaf, recursive=False)                        # the wild card match

            for fn in log_liste:
                ftype = fn[len(fn)-3:]

        for fn in log_liste:
            ftype = fn[-3:]

            if ftype == 'zip' or '.' in ftype:
                logfil.set(fn_first + '.' + variant[:-4] + '.log')
                tabfil.set(fn_first + '.' + variant[:-4] + '.csv')
                deltafil.set(fn_first + '.' + variant[:-4] + '.delta')
                txtorig.set(fn_first + '.orig.txt')
                txtemul.set(fn_first + '.' + variant[:-4] + '.txt')
                pdffil.set(fn_first + '.' + variant[:-4] + '.pdf')
                root.after(0, lambda: select_tab_and_focus(resframe, logfil_entry))
                break

    except:                                                                     # catch *all* exceptions
        tb = sys.exc_info()[2]
        sub_issue("Problem in emulator_core.py")
        for ele in traceback.format_tb(tb):
            sub_issue(ele[:-1])                                                 # sub appends <CR>
        sub_issue(str(sys.exc_info()[1]))
        runState.set('Emulation broken ...  ')
        ttk.Label(runframe, textvariable=runState, style='Error.TLabel').grid(column=2, row=runRow, sticky=(W), padx=20, pady=10)
    # runframe.update()                                                           # update frame display
        select_tab_and_focus(runframe, lfd)

    #log_msg("End of sub_emul reached")
    pass

runRow = 1

# --- Grid config ---
for c in range(3):
    runframe.columnconfigure(c, weight=1)

runframe.rowconfigure(runRow + 1, weight=1)   # Text groeit verticaal

# --- Header row ---
ttk.Label(
    runframe,
    text="Messages from Emulation"
).grid(column=0, row=runRow, sticky="W", padx=5, pady=10)

ttk.Button(
    runframe,
    text="Run Emulation",
    command=sub_emul
).grid(column=1, row=runRow, sticky="E", padx=20, pady=5)

runState = StringVar()
runState.set("")

tStyle.configure('Done.TLabel', foreground='green')
tStyle.configure('Error.TLabel', foreground='red')

ttk.Label(
    runframe,
    textvariable=runState
).grid(column=2, row=runRow, sticky="W", padx=20)

# --- Text output (dynamic) ---
lfd = Text(
    runframe,
    state='disabled',
    wrap='none'
)

lfd.grid(
    column=0,
    row=runRow + 1,
    columnspan=3,
    sticky="NSEW",
    padx=5,
    pady=5
)

lfd.tag_configure('issue', foreground='red')

# --- Scrollbars ---
scrly = ttk.Scrollbar(runframe, orient=VERTICAL, command=lfd.yview)
scrly.grid(column=3, row=runRow + 1, sticky="NS")

lfd['yscrollcommand'] = scrly.set

scrlx = ttk.Scrollbar(runframe, orient=HORIZONTAL, command=lfd.xview)
scrlx.grid(column=0, columnspan=3, row=runRow + 2, sticky="EW")

lfd['xscrollcommand'] = scrlx.set

# --- Clear button ---
ttk.Button(
    runframe,
    text="Clear Messages",
    command=clear_msg
).grid(column=0, row=runRow, sticky="E", padx=20)


ttk.Progressbar(runframe, mode='indeterminate').start(10)

how_to_print = 'GUI'
#how_to_print = 'print'                                                         # goes to DOS window; for debugging
set_tty(runframe, lfd, how_to_print)                                            # export print settings to main routine

wdir_entry.focus()                                                              # activate as initial input box
root.mainloop()