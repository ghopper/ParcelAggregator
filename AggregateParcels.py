# ---------------------------------------------------------------------------
# AggregateParcel.py
# Description: Used to aggregate parcel data into a "common data model"...see the process add field for the standard schema.
# If you want to append the processed data to another layer, it's up to you to make sure the target layer has the correct schema already setup.
#This script is meant to be run from an ArcGIS toolbox.
# 
# By. Ian Grasshoff
# Created: 5/8/2012
# Modified:  
# ArcGIS 10 Compatiable:  Yes
# ---------------------------------------------------------------------------

#Imports
import arcpy, os, re, time, sys
from time import gmtime,strftime

###################### Functions ####################

def cleanStr(myStr):
    myStr1 = myStr.replace("\"","")
    return myStr1
        
def checkInput(inputArg):
    length = len(inputArg)
    if length > 0:
        return 1
    else:
        return 0

def printMsg(myMsg):
    arcpy.AddMessage(myMsg)
    print myMsg

def loginfo(logMsg,logTime):
    timestamp = time.strftime('%I:%M:%S %p', time.localtime())
    log = open(log_file,'a')
    # Do you want to time stamp?
    if logTime == 1:
        log.write('\n----' + timestamp)
    else:
        log.write('\n----')

    log.write('\n' + logMsg)
    log.close()

def fieldCalc(inField, updateField, dataType):
    rows = arcpy.UpdateCursor(Input_Parcel_Layer)
    #print inField
    for row in rows:
        val = row.getValue(inField)

        # Handle Strings
        if dataType == "string":
            if val is None:
                val = ""
            else:
                try:
                    val = val.replace('\"','')
                    val = val.replace('\'','')
                    val = val.strip()
                except:
                    val = str(val)
                    val = val.replace('\"','')
                    val = val.replace('\'','')
                    val = val.strip()
                
            row.setValue(updateField, val)
                
        # Handle long/short integer, not used...been using float instead
        elif dataType == "int":
            # Handle Null or none
            if val is None:
                val = 0
                val = int(val)
            else:
                # Deal with data as a string to clean it...this is to handle counties that are storing numerica values as text
                val = str(val)
                val = val.strip()
                # If string is empty
                if len(val) == 0:
                    val = "0"
                    val = int(val)
                else:
                    val = int(val)
                    
            row.setValue(updateField, val)
            
        # handle floating point decimal (double data type in ArcGIS)
        elif dataType == "float":
            # Handle Null or none
            if val is None:
                val = 0
                val = float(val)  
            # Deal with data as a string to clean it...this is to handle counties that are storing numeric values as text
            else:
                val = str(val)
                val = val.strip()
                # If string is empty
                if len(val) == 0:
                    val = "0"
                    val = float(val)
                else:
                    val = float(val)
                    
            row.setValue(updateField, val)
        else:
            printMsg("no records to calculate")
            
        rows.updateRow(row)

    del row
    del rows

def concatField(inField1, inField2, updateField, dataType):
    rows = arcpy.UpdateCursor(Input_Parcel_Layer)
    for row in rows:
        val1 = row.getValue(inField1)
        val2 = row.getValue(inField2)
        if dataType == "string":
            if val1 is None:
                val1 = ""
                print inField1 + ": Contains Null data"
            else:
                val1 = val1.replace('\"','')
            if val2 is None:
                val2 = ""
                print inField2 + ": Contains Null data"
            else:
                val2 = val2.replace('\"','')
                
            concatVal = val1 + " " + val2
            #print concatVal
            row.setValue(updateField, concatVal)
        elif dataType == "int":
            concatVal = val1 + val2
            #print concatVal
            row.setValue(updateField, concatVal)
        else:
            printMsg("no records to calculate")
        rows.updateRow(row)
        
    del row
    del rows

# usage example writeXML("",open) writes the document root tag
# usage example writeXML("GISPIN,"") writes the intermediate tags
# usage exmaple writeXML("",close) writes the document closing tag
def writeXML(xml,type):
    xmlfile = open(xml_file,'a')
    if type == "open":
        xmlfile.write('<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>')
        xmlfile.write('\n' + "<fieldmapping>")
    elif type == "close":
        xmlfile.write('\n' + "</fieldmapping>")
    else:
        xmlfile.write('\n' + xml)
        
    xmlfile.close()

################ End Functions ########################

################ Variables ########################

# Check for shapefile...
desc = arcpy.Describe(arcpy.GetParameterAsText(0))
if hasattr(desc, "dataType"):
    printMsg("Input Data Type:    " + desc.dataType)
    if str(desc.dataType) == "ShapeFile":
        printMsg("!!Warning!!  This script will only work with geodatabase feature classes due to shapefile field length limitations..please load into geodatabase first")
        printMsg("Exiting script....")
        sys.exit()
        # To Do...at the start of the script check for shapefile, then load it into a geodatabase...continue processing

# Handle whether to backup data, then build the input layer path
keep_copy = arcpy.GetParameter(1)
timestamp = time.strftime('%I%M%S', time.localtime())
if keep_copy is True:
    try:
        printMsg("Keeping original data...")
        original = arcpy.GetParameterAsText(0)
        base_path = original.split('\\')
        new_layer = "agg_" + timestamp + "_" + base_path.pop()
        base_path.append(new_layer)
        Input_Parcel_Layer = '\\'.join(map(str, base_path))
        arcpy.Copy_management(original, Input_Parcel_Layer)
        printMsg("Done copying...")
    except:
        printMsg("!!!!!!! Failed to keep original data...exiting")
        sys.exit()
        
else:
    printMsg("Not keeping a backup of original...")
    Input_Parcel_Layer = arcpy.GetParameterAsText(0)    
# End building the input path..

    
# Bulk of input field variables from the ArcGIS Script tool
Muni_Name = arcpy.GetParameterAsText(2)
Input_PARCEL_ID = arcpy.GetParameterAsText(3)
Input_OWN_LST = arcpy.GetParameterAsText(4)
Input_OWN_FST = arcpy.GetParameterAsText(5)
Input_OWN_MAIL1 = arcpy.GetParameterAsText(6)
Input_OWN_MAIL2 = arcpy.GetParameterAsText(7)
Input_OWN_CITY = arcpy.GetParameterAsText(8)
Input_OWN_ST = arcpy.GetParameterAsText(9)
Input_OWN_ZIP = arcpy.GetParameterAsText(10)
Input_PROPERTY_ADDR = arcpy.GetParameterAsText(11)
Input_TX_CLASS = arcpy.GetParameterAsText(12)
Input_TX_LAND_VAL = arcpy.GetParameterAsText(13)
Input_TX_IMP_VAL = arcpy.GetParameterAsText(14)
Input_TX_ACRES = arcpy.GetParameterAsText(15)
Input_TX_YEAR = arcpy.GetParameterAsText(16)
Input_CTY_DATE = arcpy.GetParameterAsText(17)
Input_URL = arcpy.GetParameterAsText(18)

# Feature classes for Apppend
fcList = [Input_Parcel_Layer]
# Append target
StateWide_Layer = arcpy.GetParameterAsText(19)

# Logging information
log_file_folder = arcpy.GetParameterAsText(20)
input_schema_mod = arcpy.GetParameter(21)
input_processing_notes = arcpy.GetParameterAsText(22)

# Handle whether the input parameter is check on/off
if input_schema_mod is True:
    input_schema_mod = "Y"
else:
    input_schema_mod = "N"

timestamp = time.strftime('%I_%M_%S_%p', time.localtime())
log_file_name = Muni_Name + "_processing_" + timestamp + ".log"
log_file = log_file_folder + "\\" + log_file_name
xml_file_name = Muni_Name + "_fieldmapping_" + timestamp + ".xml"
xml_file = log_file_folder + "\\" + xml_file_name

################ End Variables ########################

try:
    datestamp = time.strftime('%m/%d/%Y', time.localtime())
    timestamp = time.strftime('%I:%M:%S %p', time.localtime())    
    # Write the opening XML tag
    writeXML("","open")
    writeXML("<process_dt>" + datestamp + " " + timestamp + "</process_dt>", "")
    
    # Write XML tag
    writeXML("<layer>" + Input_Parcel_Layer + "</layer>","")
    writeXML("<JDI_MUNI_NAME>" + Muni_Name + "</JDI_MUNI_NAME>","")
    
    printMsg(Muni_Name + " - Starting to Aggregate Parcels...")
    printMsg("Processing Log: " + log_file)
    printMsg("XML field mapping: " + xml_file)
    printMsg("Modified Schema?  " + input_schema_mod)
    printMsg("--- Adding common fields")
    
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_MUNI_NAME", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field (3)
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_PARCEL_ID", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_OWN_LST", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_OWN_FST", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_OWN_LST_FST", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_OWN_MAIL1", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_OWN_MAIL2", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_OWN_CITY", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_OWN_ST", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_OWN_ZIP", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_PROPERTY_ADDR", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_TX_CLASS", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_TX_LAND_VAL", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_TX_IMP_VAL", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_TX_TOTAL_VAL", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_TX_ACRES", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_TX_YEAR", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_CTY_DATE", "DATE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_PUB_DATE", "DATE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Add Field
    arcpy.AddField_management(Input_Parcel_Layer, "JDI_URL", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
    
    printMsg("=== Finished Adding common fields")
    printMsg("=== Started calculating fields")
    
    # Process fields...

    # Process: JDI_CTY_NAME - Required
    expr = "'" + Muni_Name + "'"
    arcpy.CalculateField_management(Input_Parcel_Layer, "JDI_MUNI_NAME", expr, "PYTHON_9.3", "")

    # Process: JDI_PARCEL_ID - Optional
    if checkInput(Input_PARCEL_ID) == 1:
        writeXML("<JDI_PARCEL_ID>" + Input_PARCEL_ID + "</JDI_PARCEL_ID>", "")
        # Cursor
        fieldCalc(Input_PARCEL_ID, "JDI_PARCEL_ID", "string")
        printMsg("JDI_PARCEL_ID - Complete")
    else:
        writeXML("<JDI_PARCEL_ID>SKIPPED</JDI_PARCEL_ID>", "")
        printMsg("!!! Skipped JDI_PARCEL_ID Calc")

    # Process: JDI_OWN_LST - Optional
    if checkInput(Input_OWN_LST) == 1:
        writeXML("<JDI_OWN_LST>" + Input_OWN_LST + "</JDI_OWN_LST>", "")
        # Cursor
        fieldCalc(Input_OWN_LST, "JDI_OWN_LST", "string")
        printMsg("JDI_OWN_LST - Complete")
    else:
        writeXML("<JDI_OWN_LST>SKIPPED</JDI_OWN_LST>", "")
        printMsg("!!! Skipped JDI_OWN_LST Calc")
        
    # Process: JDI_OWN_FST - Optional
    if checkInput(Input_OWN_FST) == 1:
        writeXML("<JDI_OWN_FST>" + Input_OWN_FST + "</JDI_OWN_FST>", "")
        # Cursor
        fieldCalc(Input_OWN_FST, "JDI_OWN_FST", "string")
        printMsg("JDI_OWN_FST - Complete")
    else:
        writeXML("<JDI_OWN_FST>SKIPPED</JDI_OWN_FST>", "")
        printMsg("!!! Skipped JDI_OWN_FST Calc")
        
    # Process: JDI_OWN_LST_FST - Optional - Concatenated
    if checkInput(Input_OWN_LST) == 1 and checkInput(Input_OWN_FST) == 1:
        writeXML("<JDI_OWN_LST_FST>CONCATENATED</JDI_OWN_LST_FST>", "")
        # Cursor
        concatField(Input_OWN_FST, Input_OWN_LST, "JDI_OWN_LST_FST", "string")
        printMsg("JDI_OWN_LST_FST - Complete")
    else:
        writeXML("<JDI_OWN_LST_FST>SKIPPED</JDI_OWN_LST_FST>", "")
        printMsg("!!! Skipped JDI_OWN_LST_FST Calc")
        
    # Process: JDI_OWN_MAIL1 - Optional
    if checkInput(Input_OWN_MAIL1) == 1:
        writeXML("<JDI_OWN_MAIL1>" + Input_OWN_MAIL1 + "</JDI_OWN_MAIL1>", "")
        # Cursor
        fieldCalc(Input_OWN_MAIL1, "JDI_OWN_MAIL1", "string")
        printMsg("JDI_OWN_MAIL1 - Completed")
    else:
        writeXML("<JDI_OWN_MAIL1>SKIPPED</JDI_OWN_MAIL1>", "")
        printMsg("!!! Skipped JDI_OWN_MAIL1 Calc")
        
    # Process: JDI_OWN_MAIL2 - Optional
    if checkInput(Input_OWN_MAIL2) == 1:
        writeXML("<JDI_OWN_MAIL2>" + Input_OWN_MAIL2 + "</JDI_OWN_MAIL2>", "")
        fieldCalc(Input_OWN_MAIL2, "JDI_OWN_MAIL2", "string")
        printMsg("JDI_OWN_MAIL2 - Complete")
    else:
        writeXML("<JDI_OWN_MAIL2>SKIPPED</JDI_OWN_MAIL2>", "")
        printMsg("!!! Skipped JDI_OWN_MAIL2 Calc")
        
    # Process: JDI_OWN_CITY - Optional
    if checkInput(Input_OWN_CITY) == 1:
        writeXML("<JDI_OWN_CITY>" + Input_OWN_CITY + "</JDI_OWN_CITY>", "")
        fieldCalc(Input_OWN_CITY, "JDI_OWN_CITY", "string")
        printMsg("JDI_OWN_CITY - Complete")
    else:
        writeXML("<JDI_OWN_CITY>SKIPPED</JDI_OWN_CITY>", "")
        printMsg("!!! Skipped JDI_OWN_CITY Calc")
        
    # Process: JDI_OWN_ST - Optional
    if checkInput(Input_OWN_ST) == 1:
        writeXML("<JDI_OWN_ST>" + Input_OWN_ST + "</JDI_OWN_ST>", "")
        fieldCalc(Input_OWN_ST, "JDI_OWN_ST", "string")
        printMsg("JDI_OWN_ST - Complete")
    else:
        writeXML("<JDI_OWN_ST>SKIPPED</JDI_OWN_ST>", "")
        printMsg("!!! Skipped JDI_OWN_ST Calc")
        
    # Process: JDI_OWN_ZIP - Optional
    if checkInput(Input_OWN_ZIP) == 1:
        writeXML("<JDI_OWN_ZIP>" + Input_OWN_ZIP + "</JDI_OWN_ZIP>", "")
        # Cursor
        fieldCalc(Input_OWN_ZIP, "JDI_OWN_ZIP", "string")
        printMsg("JDI_OWN_ZIP - Complete")
    else:
        writeXML("<JDI_OWN_ZIP>SKIPPED</JDI_OWN_ZIP>", "")
        printMsg("!!! Skipped JDI_OWN_ZIP Calc")
        
    # Process: JDI_PROPERTY_ADDR - Optional
    if checkInput(Input_PROPERTY_ADDR) == 1:
        writeXML("<JDI_PROPERTY_ADDR>" + Input_PROPERTY_ADDR + "</JDI_PROPERTY_ADDR>", "")
        # Cursor
        fieldCalc(Input_PROPERTY_ADDR, "JDI_PROPERTY_ADDR", "string")
        printMsg("JDI_PROPERTY_ADDR - Complete")
    else:
        writeXML("<JDI_PROPERTY_ADDR>SKIPPED</JDI_PROPERTY_ADDR>", "")
        printMsg("!!! Skipped JDI_PROPERTY_ADDR Calc")
        
    # Process: JDI_TX_CLASS - Optional
    if checkInput(Input_TX_CLASS) == 1:
        writeXML("<JDI_TX_CLASS>" + Input_TX_CLASS + "</JDI_TX_CLASS>", "")
        # Cursor
        fieldCalc(Input_TX_CLASS, "JDI_TX_CLASS", "string")
        printMsg("JDI_TX_CLASS - Complete")
    else:
        writeXML("<JDI_TX_CLASS>SKIPPED</JDI_TX_CLASS>", "")
        printMsg("!!! Skipped JDI_TX_CLASS Calc")
        
    # Process: JDI_TX_LAND_VAL - Optional
    if checkInput(Input_TX_LAND_VAL) == 1:
        writeXML("<JDI_TX_LAND_VAL>" + Input_TX_LAND_VAL + "</JDI_TX_LAND_VAL>", "")
        fieldCalc(Input_TX_LAND_VAL, "JDI_TX_LAND_VAL", "float")
        printMsg("JDI_TX_LAND_VAL - Complete")
    else:
        writeXML("<JDI_TX_LAND_VAL>SKIPPED</JDI_TX_LAND_VAL>", "")
        printMsg("!!! Skipped JDI_TX_LAND_VAL Calc")

    # Process: JDI_TX_IMP_VAL - Optional
    if checkInput(Input_TX_IMP_VAL) == 1:
        writeXML("<JDI_TX_IMP_VAL>" + Input_TX_IMP_VAL + "</JDI_TX_IMP_VAL>", "")
        fieldCalc(Input_TX_IMP_VAL, "JDI_TX_IMP_VAL", "float")
        printMsg("JDI_TX_IMP_VAL - Complete")
    else:
        writeXML("<JDI_TX_IMP_VAL>SKIPPED</JDI_TX_IMP_VAL>", "")
        printMsg("!!! Skipped JDI_TX_IMP_VAL Calc")

    # Process: JDI_TX_TOTAL_VAL - Optional - Concatenated
    if checkInput(Input_TX_IMP_VAL) == 1 and checkInput(Input_TX_LAND_VAL) == 1:
        writeXML("<JDI_TX_TOTAL_VAL>CONCATENATED</JDI_TX_TOTAL_VAL>", "")
        expr = "!JDI_TX_LAND_VAL! + !JDI_TX_IMP_VAL!"
        arcpy.CalculateField_management(Input_Parcel_Layer, "JDI_TX_TOTAL_VAL", expr, "PYTHON_9.3", "")
        printMsg("JDI_TX_TOTAL_VAL - Complete")
    else:
        writeXML("<JDI_TX_TOTAL_VAL>SKIPPED</JDI_TX_TOTAL_VAL>", "")
        printMsg("!!! Skipped JDI_TX_TOTAL_VAL Calc")
        
    # Process: JDI_TX_ACRES - Optional
    if checkInput(Input_TX_ACRES) == 1:
        writeXML("<JDI_TX_ACRES>" + Input_TX_ACRES + "</JDI_TX_ACRES>", "")
        fieldCalc(Input_TX_ACRES, "JDI_TX_ACRES", "float")
        printMsg("JDI_TX_ACRES - Complete")
    else:
        writeXML("<JDI_TX_ACRES>SKIPPED</JDI_TX_ACRES>", "")
        printMsg("!!! Skipped JDI_TX_ACRES Calc")
        
    # Process: JDI_TX_YEAR - Optional
    if checkInput(Input_TX_YEAR) == 1:
        writeXML("<JDI_TX_YEAR>" + Input_TX_YEAR + "</JDI_TX_YEAR>", "")
        fieldCalc(Input_TX_YEAR, "JDI_TX_YEAR", "string")
        printMsg("JDI_TX_YEAR - Complete")
    else:
        writeXML("<JDI_TX_YEAR>SKIPPED</JDI_TX_YEAR>", "")
        printMsg("!!! Skipped JDI_TX_YEAR Calc")
        
    # Process: JDI_CTY_DATE - Optional
    if checkInput(Input_CTY_DATE) == 1:
        writeXML("<JDI_CTY_DATE>" + Input_CTY_DATE + "</JDI_CTY_DATE>", "")
        expr = "!" + Input_CTY_DATE + "!"
        arcpy.CalculateField_management(Input_Parcel_Layer, "JDI_CTY_DATE", expr, "PYTHON_9.3", "")
        printMsg("JDI_CTY_DATE - Complete")
    else:
        writeXML("<JDI_CTY_DATE>SKIPPED</JDI_CTY_DATE>", "")
        printMsg("!!! Skipped JDI_CTY_DATE Calc")
        
    # Process: JDI_PUB_DATE - Required - Calculated in background
    writeXML("<JDI_PUB_DATE>CALC</JDI_PUB_DATE>", "")
    expr = "\'" + str(datestamp) + " " + timestamp + "\'"
    arcpy.CalculateField_management(Input_Parcel_Layer, "JDI_PUB_DATE", expr, "PYTHON_9.3", "")

    # Process: JDI_URL - Optional
    if checkInput(Input_URL) == 1:
        writeXML("<JDI_URL>" + Input_URL + "</JDI_URL>", "")
        fieldCalc(Input_URL, "JDI_URL", "string")
        printMsg("JDI_URL - Complete")
    else:
        writeXML("<JDI_URL>SKIPPED</JDI_URL>", "")
        printMsg("!!! Skipped JDI_URL Calc")
    
    # Append normalized Parcel Layer to Statewide Layer - Optional
    # Check for inputs
    if checkInput(StateWide_Layer) == 1:
        schemaType = "NO_TEST"
        arcpy.Append_management(fcList, StateWide_Layer, schemaType, "", "")
        printMsg("County Layer Appended to: " + StateWide_Layer)

    else:
        printMsg("Nothing appended to Statewide Layer")

    # Write Closing XML
    writeXML("<status>success</status>", "")
    writeXML("<MOD_CTY_SCHEMA>" + input_schema_mod + "</MOD_CTY_SCHEMA>", "")
    writeXML("<PROCESSING_NOTES>" + input_processing_notes + "</PROCESSING_NOTES>", "")
    writeXML("","close")
    printMsg(" (: (: ! Script completed Successfully ! :) :) ")

except:
    writeXML("<status>fail</status>", "")
    msg = arcpy.GetMessages()
    writeXML("<gp_msg>" + msg + "</gp_msg>", "")
    writeXML("","close")
    
    printMsg("Script Failed!")
    printMsg(msg)
    
    print arcpy.GetMessages()
    print "Script Failed!"
    sys.exit()
