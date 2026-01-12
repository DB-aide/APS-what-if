APS Emulator (Debian / Linux ready)

This version has been modified and tested on Debian 13 (Linux).

This branch targets AAPS 3.3.3.0.
The previously planned release for AAPS 3.3.2 is discontinued.

⚠️ The emulator documentation is not yet fully updated.

Major changes in this branch
Includes AAPS 3.2.0.4 capabilities
Full support for AAPS 3.3.3.x
Includes recent bug fixes from AutoISF 3.0.3
Includes the new autoISF 3.1.0 capabilities

This branch is not yet fully tested and may still contain bugs.
If you encounter issues, please contact ga-zelle.

See also: change.log
What is this emulator?

APS-emulator is a Python translation of the original JavaScript code
determineSMB-basal.js.
It allows running the APS loop offline on a PC, using historical AAPS log files.

This makes it possible to:
Travel back in time to any moment in a logfile
Re-run the APS loop with modified settings
Safely evaluate changes before applying them in AAPS itself
This provides a safe and reproducible environment to experiment with APS settings.

What can be modified?
The historical AAPS log files contain enough information to re-run the APS loop with, for example:
Changed glucose target
Changed ISF
SMB on / off
Different autosens behavior
Other APS-related parameters
Output and results

The emulator produces:
Tabular output (CSV / TXT)
Graphical output (PDF)
Delta analysis of insulin differences
Main results include:
Difference in total insulin delivery
SMB and TBR changes

Related values such as:
SGV
target
autosens ratio
IOB, COB, etc.
Flowchart output (logic tracing)

A special output is the flowchart view, which visualizes:

The execution path through determineSMB-basal
Which decisions were taken
Which branches were skipped
The reasoning behind each decision
This is extremely useful to understand why APS behaved the way it did.

Linux / Debian usage (recommended)
This project works best on Linux / Debian.
Directory usage

aapsLogs/
→ Input directory
→ Copy AAPS .zip log files here (from your phone)

your_working_directory/
→ Output directory
→ Generated emulator results (CSV, PDF, TXT, etc.)

All paths are configured in:

software/config.py
Android usage (optional)
Running the emulator directly on Android is optional.

A new app called QPythonPlus is required for Android 14 and above.
Older Android versions can still use QPython 3L / 3S, even with these updated scripts.

Download QPythonPlus (Android 14+):
https://drive.google.com/drive/u/3/folders/1lFqvlmArrV35ikcdW61MdVAx2UUWMcLh

⚠️ On Linux / PC, Android path detection is disabled by default.
Users are expected to manually copy log files from the phone to aapsLogs/.

Important notes for Git users
Do not commit:
aapsLogs/
your_working_directory/
These directories contain large generated files and are ignored by .gitignore
Only source code and documentation should be committed

Status

✅ Debian 13 tested

⚠️ Documentation still evolving

⚠️ Not fully regression-tested

🧪 Intended for advanced users who understand AAPS behavior
