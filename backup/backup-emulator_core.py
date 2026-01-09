global lcount
    # isZip = True    # testwise fix
    lcount  = 0
    if isZip:
        with zipfile.ZipFile(fn) as z:
            for filename in z.namelist():
                lf = z.open(filename)           # has only 1 member file
    else:
        lf = open(fn, 'r')

    notEOF = True                               # needed because "for zeile in lf" does not work with AAPS 2.5
    
    cont = 'MORE'                               # in case nothing found
    sequenceBLANK = 0                           # needed for AIMI
    while notEOF:                               # needed because "for zeile in lf" does not work with AAPS 2.5
        try:                                    # needed because "for zeile in lf" does not work with AAPS 2.5
            while True:
                try:
                    zeile = lf.readline()       # needed because "for zeile in lf" does not work with AAPS 2.5
                    break
                except FileNotFoundError:
                    if isAndroid:               # assume old logfile is recycled; wait for new one
                        try:
                            lf.Close()
                        except:
                            pass                # was already closed / had disappeared
                        log_msg('\nwaiting 10s for logfile housekeeping')
                        time.sleep(10)
                        lf = open(fn, 'r')
            if isZip:   zeile = str(zeile)[2:-3]# strip off the "'b....'\n" remaining from the bytes to str conversion
            #if zeile == '':                     # needed because "for zeile in lf" does not work with AAPS 2.5
            #    notEOF = False                  # needed because "for zeile in lf" does not work with AAPS 2.5
            #    break                           # needed because "for zeile in lf" does not work with AAPS 2.5
            if zeile == '':                     # needed for AIMI
                sequenceBLANK +=1               # needed for AIMI
                if sequenceBLANK >10:           # needed for AIMI
                    notEOF = False              # needed for AIMI
                    break                       # needed for AIMI
            else:                               # needed for AIMI
                sequenceBLANK = 0               # needed for AIMI
                
            lcount +=  1
            # print(zeile)
            if parser_debug:
                try:
                    snippet = zeile.strip().replace('\n','\\n')
                    if len(snippet) > 300:
                        snippet = snippet[:300] + '...'
                    parser_debug_log(f"LINE {lcount}: isZip={isZip} preview={snippet}")
                except Exception:
                    pass
            if lcount>100000:  
                sub_issue('no end found at row '+str(lcount)+ ' reading /'+zeile+'/')
                return 'STOP'
            if len(zeile)>13:
                headerKey = zeile[2] + zeile[5] + zeile[8] + zeile[12]
                if parser_debug:
                    try:
                        parser_debug_log(f"LINE {lcount}: headerKey={headerKey}")
                    except Exception:
                        pass
                if headerKey == '::. ':
                    sLine = zeile[13:]
                    Action = hole(sLine, 0, '[', ']')
                    sOffset = len(Action)
                    Block2 = hole(sLine, 1+sOffset, '[', ']')
                    if Block2 == '[DataService.onHandleIntent():54]' \
                    or Block2 == '[DataService.onHandleIntent():55]' \
                    or Block2 == '[DataService.onHandleIntent():69]':               # token :54 added for AAPS versions <2.7, :69 for V2.7
                        pass
                    elif Block2[:-3] == '[DetermineBasalAdapterAMAJS.invoke():':                                                   # various input items for loop
                        log_msg('\nSorry, this tool is currently only available for oref1 with SMB\n')
                        return 'STOP'
                    elif re.match(r"\[DetermineBasalAdapter[A-Za-z]+\.invoke\(\)", Block2) \
                      or re.match(r"\[OpenAPSAutoISFPlugin\.invoke\(\)", Block2) \
                      or re.match(r"\[OpenAPSSMBPlugin.invoke\(\)", Block2):  # loop inputs or result record
                        key_anf = Block2.find('):')
                        key_end = Block2.find(']:')
                        dataType= eval(Block2[key_anf+2:key_end])
                        dataStr = sLine[sLine.find(']: ')+3:]
                        dataTxt = dataStr[:17]                              # make it dataTxt based rather than dataType (more robust)
                        if dataType_offset <-99 and newLoop:                            # not yet initialized for known AAPS version
                            if   dataType == 75 \
                            and newLoop :                                   # V 2.3 ?
                                log_msg('\nSorry, cannot extract required data from logfiles before AAPS version 2.5\n')
                                return 'STOP'
                            dataType_offset = dataType-79                   # "0" was lowest in V2.5.1
                            if dataType_offset >= 15:                       AAPS_Version = '2.7'    # same as 2.8
                            elif dataType_offset < 0:                       AAPS_Version = '2.7'    # same as 3.0
                            elif dataType_offset >=2:                       AAPS_Version = '2.7'    # v 3.2
                            #elif dataType == 79:    dataType_offset =  0    # V 2.5.1
                            #elif dataType == 80:    dataType_offset =  1    # V 2.6.1
                            #elif dataType == 94:    dataType_offset = 15    # V 2.8.0    >>> Invoking detemine_basal <<< / Wolfgang Spänle
                            #elif dataType == 98:    dataType_offset = 19    # V 2.8.0    >>> Invoking detemine_basal <<< / Phillip
                            #elif dataType == 97:
                            #                        dataType_offset = 18    # V 2.7
                            #                        AAPS_Version = '2.7'
                            #elif dataType == 108:   pass                    # V 2 7:     MicroBolusAllowed:  true
                            #elif dataType == 109:   pass                    # V 2 7:     SMBAlwaysAllowed:  true
                            #elif dataType == 110:   pass                    # V 2 7:     CurrentTime: 1604776609511
                            #elif dataType != 163:   print('unhandled dataType:', str(dataType), 'row', str(lcount), 'of file',fn) # any but 2.7 RESULT
                            #version_set = True                              # keep until next logfile is loaded
                            pass
                        if Block2.find('AutoISF')>0:                         AAPS_Version = '3.3'    # during dev only?
                        if   dataTxt[:16] == 'RhinoException: ' :           code_error(lcount, dataStr)
                        elif dataTxt[:16] == 'Glucose status: ' :           get_glucose_status(lcount, dataStr)
                        elif dataTxt[:16] == 'IOB data:       ' and AAPS_Version!='3.3':     get_iob_data(lcount, dataStr, log, zeile[:8])
                        elif dataTxt[:16] == 'Current temp:   ' and AAPS_Version!='3.3':     get_currenttemp(lcount, dataStr)
                        elif dataTxt[:16] == 'Profile:        ' and AAPS_Version!='3.3':     get_profile(lcount, dataStr)
                        elif dataTxt[:16] == 'Meal data:      ' and AAPS_Version!='3.3':     get_meal_data(lcount, dataStr)
                        elif dataTxt[:16] == 'Autosens data:  ' and AAPS_Version!='3.3':     get_autosens_data(lcount, dataStr)
                        elif dataTxt      == 'AutoIsfMode:     ' :          get_AutoIsfMode(lcount, dataStr)
                        elif dataTxt      == 'flatBGsDetected: ' :          get_flatBGsDetected(lcount, dataStr)
                        elif dataTxt      == 'MicroBolusAllowed' :          get_MicroBolusAllowed(lcount, dataStr)
                        #elif dataTxt     == 'Result: RT(algori' :          cont = TreatLooop33(dataStr, log, lcount, fn)
                        elif dataTxt[:16] == 'AutoISF extras: ' :           get_autoISF_extras(lcount, hole(sLine, 1+sOffset+len(Block2), '{', '}'))
                        elif dataTxt      == 'Result: {"temp":"' :
                                                                            checkCarbsNeeded(dataStr[8:], lcount)   # result record in AAPS2.6.1
                                                                            cont = TreatLoop(dataStr[8:], log, lcount, fn)
                                                                            if cont=='STOP' or cont=='SYNTAX':     return cont
                        #elif dataType == dataType_offset+145:               checkCarbsNeeded(dataStr[8:], lcount)   # result record in AAPS2.7
                        #elif dataType == dataType_offset+147:               checkCarbsNeeded(dataStr[8:], lcount)   # result record in AAPS2.8 Wolfgang Spänle
                        #elif dataType == dataType_offset+146:               checkCarbsNeeded(dataStr[8:], lcount)   # result record in AAPS2.8 / Phillip
                        #else:   print('unknown', dataTxt)
                        #else:   print (str(lcount), str(dataType), str(dataType_offset), '/'+dataTxt+'/' + dataStr[17:60])
                        pass
                    elif Block2 == '[LoggerCallback.jsFunction_log():39]' \
                    or   Block2 == '[LoggerCallback.jsFunction_log():42]' \
                    or   Block2 == '[LoggerCallback.jsFunction_log():21]':          # from console.error; '42' is for >= V2.7, '21' for V3
                        PrepareSMB(sLine, log, lcount)   
                    elif Block2 == '[DbLogger.dbAdd():29]':                             ################## flag for V2.5.1
                        Curly =  hole(sLine, 1+sOffset+len(Block2), '{', '}')
                        #print('calling TreatLoop in row '+str(lcount)+' with\n'+Curly)
                        if Curly.find('{"device":"openaps:')==0:   
                            cont = TreatLoop(Curly, log, lcount, fn)
                            if cont=='STOP' or cont=='SYNTAX':     return cont
                    elif zeile.find('[NSClientPlugin.onStart$lambda-5():124]') > 0 :    ################## flag for V3.0dev
                        Curly =  hole(zeile, 5, '{', '}')
                        #print('calling TreatLoop in row '+str(lcount)+' with\n'+Curly)
                        #if  Curly.find('{"device":"openaps:')==0 \
                        #and Curly.find('"openaps":{"suggested":{')>0 :
                        if  Curly.find('"openaps":{"suggested":{')>0 :
                            #and 'lastTempAge' in SMBreason :   
                            cont = TreatLoop(Curly, log, lcount, fn)
                            if cont=='STOP' or cont=='SYNTAX':     return cont
                    elif zeile.find('Activity Monitor json:') > 0 :
                        activityMonitorCurly = hole(zeile, 20, '{', '}')
                    elif zeile.find('[PersistenceLayerImpl$insertOrUpdateApsResult$2.apply():') > 0:
                                                                            cont = TreatLoop33(zeile, log, lcount,fn)
                                                                            if cont=='STOP' or cont=='SYNTAX':     return cont
                    elif zeile.find(']: State json') > 0 :
                        Curly = hole(sLine, 1+sOffset+len(Block2), '{', '}')
                        getStateValue(Curly)
                    elif zeile.find(']: Calibration json') > 0 :
                        getCalibrationJson(zeile[zeile.find('{'):], lcount)           # drop <CR> ?
                    #elif lcount>1400 and lcount<2000:   print('no match in row'+str(lcount)+':', Block2)
                elif zeile.find('data:{"device":"openaps:') == 0 :                      ################## flag for V2.6.1 ff
                    Curly =  hole(zeile, 5, '{', '}')
                    #print('calling TreatLoop in row '+str(lcount)+' with\n'+Curly)
                    if  Curly.find('{"device":"openaps:')==0 \
                    and Curly.find('"openaps":{"suggested":{')>0 :
                        #and 'lastTempAge' in SMBreason :   
                        cont = TreatLoop(Curly, log, lcount, fn)
                        if cont=='STOP' or cont=='SYNTAX':     return cont

        except UnicodeDecodeError:              # needed because "for zeile in lf" does not work with AAPS 2.5 containing non-printing ASCII codes
            lcount +=  1                        # skip this line, it contains non-ASCII characters!
            
    try:
        lf.close()
    except:
        time.sleep(10)                          # wait for zip conversion
    return cont
