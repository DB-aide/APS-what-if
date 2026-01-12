import locale

"""
Version 1.0.0 12-01-2026 Error handling for the Manage Inputs and Outputs for Emulating AAPS Settings dialog. 
                         If there are no *.zip files yet, a message will be displayed to the user.
"""

LANGUAGE = locale.getdefaultlocale()[0][:2]   # "nl", "en", "de"

TRANSLATIONS = {
    "nl": {
        "no_logs_title": "Geen logbestanden gevonden",
        "no_logs_msg": (
            "Er zijn geen AAPS-logbestanden gevonden in:\n\n"
            "{path}\n\n"
            "Kopieer eerst de gewenste logbestanden van je telefoon uit:\n"
            "Documents/aapsLogs/\n\n"
            "naar deze map op de PC."
        ),
    },
    "en": {
        "no_logs_title": "No log files found",
        "no_logs_msg": (
            "No AAPS log files were found in:\n\n"
            "{path}\n\n"
            "Please copy the desired log files from your phone:\n"
            "Documents/aapsLogs/\n\n"
            "to this folder on your PC first."
        ),
    },
    "de": {
        "no_logs_title": "Keine Logdateien gefunden",
        "no_logs_msg": (
            "Es wurden keine AAPS-Logdateien gefunden in:\n\n"
            "{path}\n\n"
            "Bitte kopieren Sie zuerst die gewünschten Logdateien "
            "von Ihrem Smartphone aus:\n"
            "Documents/aapsLogs/\n\n"
            "in diesen Ordner auf dem PC."
        ),
    },
}

def _(key, **kwargs):
    lang = LANGUAGE if LANGUAGE in TRANSLATIONS else "en"
    text = TRANSLATIONS.get(lang, {}).get(key, key)
    return text.format(**kwargs)
