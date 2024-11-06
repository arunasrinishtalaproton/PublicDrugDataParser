import os
import json
import csv
import xml.etree.ElementTree as ET
from datetime import datetime
import zipfile

# HL7
HL7 = {'hl7': 'urn:hl7-org:v3'}

# Log file
def log_to_file(log_file, message):
    with open(log_file, 'a') as log:
        log.write(message + '\n')

# UNII to UUID
def csv_to_transformed_dict(csv_file, key_column, value_column):
    data_dict = {}
    with open(csv_file, mode='r', newline='', encoding='utf-8-sig') as file:
        csv_reader = csv.DictReader(file)
        first_row = next(csv_reader)
        if key_column not in first_row or value_column not in first_row:
            print(f"Error: Column '{key_column}' or '{value_column}' not found in the CSV file.")
            return None
        file.seek(0)
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            try:
                key = row[key_column].strip()
                value = row[value_column].strip()
                data_dict[key] = value
            except KeyError as e:
                print(f"KeyError: {e}. Row data: {row}")
    return data_dict

# Function to parse XML file and extract data

def parse_xml_file(file_path, data_dictionary, log_file_path):
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        GSRSProduct={}
        #log_message=f"{file_path}"
        #log_to_file(log_file_path, log_message)
    except ET.ParseError:
        print('unable to parse')
        return None

    # Initialize dictionary to store extracted XML data
    try:
        #GSRSProduct={}
        XML_values = {}
        error=0

        # Extract author information
        Author={'RepresentativeOrgDUNS':'','RepresentativeOrg':''}
        represented_org_element=root.find('.//hl7:author/hl7:assignedEntity/hl7:representedOrganization',HL7)
        try:
            Author['RepresentativeOrgDUNS'] = represented_org_element.find('.//hl7:id',HL7).attrib['extension'] if represented_org_element is not None else ''
            Author['RepresentativeOrg'] = represented_org_element.find('.//hl7:name',HL7).text if represented_org_element is not None else ''
        except:
            Author['RepresentativeOrgDUNS'] =''
            Author['RepresentativeOrg'] =''
            pass
        substring_to_remove = "LABEL"
        for component in root.findall('.//hl7:component/hl7:section/hl7:subject', HL7):           
            for manufacturedProduct in component.findall('.//hl7:manufacturedProduct', HL7):                                                         
                XML_values={ 'routeAdmin':'','Ingredients': [],'ActiveMoiety':[], 'SPLSHAPE':'','SPLSCORE':'', 'SPLSIZE': '','SPLIMPRINT':'', 'Application_ID':'', 'Application_Type':'','SPLCOLOR':'','RepresentativeOrgDUNS': Author['RepresentativeOrgDUNS'], 'RepresentativeOrg': Author['RepresentativeOrg']} 
                for subjectOf in manufacturedProduct.findall('.//hl7:subjectOf',HL7):
                    for approval in subjectOf.findall('.//{urn:hl7-org:v3}approval'):
                        XML_values['Application_Type'] = subjectOf.find('.//hl7:approval',HL7).find('.//hl7:code',HL7).get('displayName')if subjectOf.find('.//hl7:approval', HL7) is not None else 'na'
                        #XML_values['Application_Type'] = subjectOf.find('.//hl7:approval',HL7).find('.//hl7:code',HL7).get('code')if subjectOf.find('.//hl7:approval', HL7) is not None else 'na'
                        try:
                            XML_values['Application_ID'] = subjectOf.find('.//hl7:approval',HL7).find('.//hl7:id',HL7).get('extension')if subjectOf.find('.//hl7:approval',HL7) is not None else 'na'
                        except:
                            XML_values['Application_ID']=''
                    for marketingAct in subjectOf.findall('.//{urn:hl7-org:v3}marketingAct'):        
                        try:
                            marketingActstatus = marketingAct.find('.//{urn:hl7-org:v3}statusCode')
                            status_code = marketingActstatus.get('code')
                            XML_values['marketingStatus'] = marketingActstatus.get('code')
                            XML_values['marketingdate_low'] = (datetime.strptime(marketingAct.find('.//hl7:low',HL7).get('value'),'%Y%m%d')).strftime('%m/%d/%Y')
                        except:
                            XML_values['marketingStatus']=''
                            XML_values['marketingdate_low']=''                                                    
                    for characteristic in subjectOf.findall('.//hl7:characteristic',HL7):
                        XML_values[characteristic.find('.//hl7:code',HL7).get('code') ]=characteristic.find('.//hl7:value',HL7).get('displayName') if characteristic is not None else 'na'                                                                                     
                for consumedIn in manufacturedProduct.findall('.//hl7:consumedIn',HL7):
                    for substanceAdministration in consumedIn.findall('.//hl7:substanceAdministration', HL7):       
                        Administcode = substanceAdministration.find('.//hl7:routeCode', HL7)if substanceAdministration is not None else 'na'                                               
                        XML_values['routeAdmin']=Administcode.get('displayName')
                for manufacturedProduct in manufacturedProduct.findall('.//hl7:manufacturedProduct',HL7):                    
                    #key= manufacturedProduct.find('.//hl7:code',HL7).get('code') if manufacturedProduct.find('.//hl7:code',HL7) is not None else 'na'
                    XML_values['ProductName'] = manufacturedProduct.find('.//hl7:name',HL7).text if manufacturedProduct.find('.//{urn:hl7-org:v3}name',HL7) is not None else 'na'
                    print('ProductName',XML_values['ProductName'])
                    
                    XML_values['DosageForm'] = manufacturedProduct.find('.//hl7:formCode',HL7).get('displayName') if manufacturedProduct.find('.//hl7:formCode',HL7) is not None else 'na'                                                                                          
                    XML_values['Generic Name'] ='na'
                    for asEntityWithGeneric in manufacturedProduct.findall('.//{urn:hl7-org:v3}asEntityWithGeneric'):                                                                                                                    
                        XML_values['Generic Name'] = asEntityWithGeneric.find('.//{urn:hl7-org:v3}name').text if asEntityWithGeneric is not None else 'na'
                    ingredientType=''                    
                    for ingredient in manufacturedProduct.findall('.//hl7:ingredient',HL7):
                        ingredient_substance = ingredient.find('.//hl7:ingredientSubstance',HL7)
                        ingredientTypeXML = ingredient.get('classCode')    
                        if ingredientTypeXML == 'ACTIB' or ingredientTypeXML == 'ACTIM' or ingredientTypeXML == 'ACTIR':
                            ingredientType = 'Active Ingredient'
                        else:
                            ingredientType = 'Inactive Ingredient'                        
  
                        quantity = ingredient.find('.//hl7:quantity',HL7)
                        active_moiety = ingredient.find('.//hl7:activeMoiety', HL7)
                        
                        basis_of_strength_unii = ingredient_substance.find('.//hl7:code',HL7).get('code')
                        #print(basis_of_strength_unii)
                        if ingredientTypeXML == 'ACTIM':
                            basis_of_strength_unii = active_moiety.find('.//hl7:code',HL7).get('code')
                            #print('ACTIM',basis_of_strength_unii)
                        else:
                            if ingredientTypeXML == 'ACTIR':
                                asEquivalentSubstance = ingredient_substance.find('.//hl7:asEquivalentSubstance', HL7)
                                asEquivalentSubstance_code = asEquivalentSubstance.find('.//hl7:code',HL7).get('code')
                                basis_of_strength_unii = asEquivalentSubstance_code
                                #print('ACTIR',basis_of_strength_unii)
                        
                        try:
                            #log_message=ingredient_substance.find('.//hl7:name', HL7).text
                            #log_to_file(log_file_path, log_message)
                            #print('applicantIngredName',ingredient_substance.find('.//hl7:name', HL7).text)
                            
                            if ingredient_substance is not None or quantity is not None or active_moiety is not None:                            
                                Substance = {
                                    'applicantIngredName': ingredient_substance.find('.//hl7:name', HL7).text,
                                    'substanceKeyType': 'UUID',
                                    'ingredientType' : ingredientType.upper(),
                                    'substanceKey': ingredient_substance.find('.//hl7:code',HL7).get('code'),
                                    'basisOfStrengthSubstanceKey': basis_of_strength_unii,
                                    'basisOfStrengthSubstanceKeyType': 'UUID',
                                    'originalNumeratorNumber': quantity.find('.//hl7:numerator',HL7).get('value') if quantity is not None else '',
                                    'originalNumeratorUnit': (quantity.find('.//hl7:numerator',HL7).get('unit')).upper() if quantity is not None else '',
                                    'originalDenominatorNumber': quantity.find('.//hl7:denominator',HL7).get('value','na') if quantity is not None else '',
                                    'originalDenominatorUnit': (quantity.find('.//hl7:denominator',HL7).get('unit')).upper() if quantity is not None else ''                
                                    }                               
                            XML_values['Ingredients'].append(Substance)
                        except:
                            log_message=f"[ERROR]IgredientIssue: {file_path}. Error: {e}"
                            log_to_file(log_file_path, log_message)
                            pass
                    #GSRSProduct={}
                    key=manufacturedProduct.find('.//hl7:code',HL7).get('code')
                    log_message=f"{key, file_path}"
                    log_to_file(log_file_path, log_message)
                    XML_values['Product_Type']=root.find('.//hl7:code',HL7).get('displayName')
                    XML_values['Set_Id']= root.find('.//hl7:setId', HL7).get('root')    
                    XML_values['URL']='https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid='+ XML_values['Set_Id']
                    XML_values['version_number'] = root.find('.//hl7:versionNumber',HL7).get('value')
                    if root.find('.//hl7:effectiveTime', HL7).get('value') is not None:
                        try:
                            XML_values['effective_time'] = (datetime.strptime(root.find('.//hl7:effectiveTime', HL7)).get('value'),'%Y%m%d').strftime('%m/%d/%Y')
                            
                        except:
                            
                            pass
                    #else:    
                        #print('except',XML_values['Set_Id'])                    
                    for asContent in component.findall('.//hl7:asContent',HL7):   
                        XML_values['formCode_Name']= asContent.find('.//hl7:containerPackagedProduct',HL7).find('.//hl7:formCode',HL7).get('displayName','na')  
                        XML_values['Package_Numerator']=asContent.find('.//hl7:quantity',HL7).find('.//hl7:numerator',HL7).get('value','na')
                        XML_values['Package_Denominator']=asContent.find('.//hl7:quantity',HL7).find('.//hl7:denominator',HL7).get('value','na')
                        XML_values['Package_NumeratorUnit']=asContent.find('.//hl7:quantity',HL7).find('.//hl7:numerator',HL7).get('unit','na')
                        XML_values['Package_DenominatorUnit']=asContent.find('.//hl7:quantity',HL7).find('.//hl7:denominator',HL7).get('unit','na')
                        #XML_values['Characteristic_Code']=asContent.find('.//hl7:characteristic',HL7).find('.//hl7:code',HL7)#.get('code','na')                                                
                        #XML_values['Characteristic_Display']=asContent.find('.//hl7:characteristic',HL7).find('.//hl7:value',HL7)#.get('displayName','na')
                        NDC_xml = {key: XML_values}                            
                    try:   
                        GSRSProduct = {
                                    "pharmacedicalDosageForm": XML_values.get('formCode_Name', '').upper(),
                                    "routeAdmin": XML_values.get('routeAdmin', '').upper(),
                                    "countryCode": "United States (USA)",
                                    "language": "en",
                                    "manufacturerName": XML_values.get('RepresentativeOrg', ''),
                                    "manufacturerCode": XML_values.get('RepresentativeOrgDUNS', ''),
                                    "manufacturerCodeType": "DUNS NUMBER",
                                    "productProvenances": [
                                        {
                                            "productNames": [
                                                {
                                                    "productName": XML_values.get('ProductName', ''),
                                                    "displayName": True,
                                                    "language": "en",
                                                    "productNameType": "PRODUCT NAME"
                                                },
                                                {
                                                    "productName": XML_values.get('Generic Name', ''),
                                                    "displayName": False,
                                                    "language": "en",
                                                    "productNameType": "GENERIC NAME"
                                                }
                                            ],
                                            "productCodes": [
                                                {
                                                    "productCode": key,
                                                    "productCodeType": "NDC CODE"
                                                }
                                            ],
                                            "productCompanies": [
                                                {
                                                    "productCompanyCodes": [
                                                        {
                                                            "companyCode": XML_values.get('RepresentativeOrgDUNS', ''),
                                                            "companyCodeType": "DUNS NUMBER"
                                                        }
                                                    ],
                                                    "provenanceDocumentId": XML_values.get('Set_Id', ''),
                                                    "companyName": XML_values.get('RepresentativeOrg', '')
                                                }
                                            ],
                                            "productDocumentations": [
                                                {
                                                    "documentId": XML_values.get('Set_Id', ''),
                                                    "setIdVersion": XML_values.get('version_number', ''),
                                                    "jurisdictions": "United States (USA)",
                                                    "documentType": "SET ID"
                                                }
                                            ],
                                            "provenance": "XML_SPL",
                                            "productStatus": XML_values.get('marketingStatus', '').upper(),
                                            "productType": XML_values.get('Product_Type', '').upper().replace(substring_to_remove, ''),
                                            "applicationType": XML_values.get('Application_Type', ''),
                                            "applicationNumber": XML_values.get('Application_ID', ''),
                                            "jurisdictions": "United States (USA)",
                                            "productUrl": XML_values.get('URL', ''),
                                            "publicDomain": "YES",
                                            "isListed": "YES"
                                        }
                                    ],
                                    "productManufactureItems": [
                                        {
                                            "productManufacturers": [
                                                {
                                                    "manufacturerRole": "REPRESENTATIVE ORGANIZATION",
                                                    "manufacturerName": XML_values.get('RepresentativeOrg', ''),
                                                    "manufacturerCodeType": "DUNS NUMBER",
                                                    "manufacturerCode": XML_values.get('RepresentativeOrgDUNS', '')
                                                }
                                            ],
                                            "productLots": [
                                                {
                                                    "productIngredients": XML_values.get('Ingredients', [])
                                                }
                                            ],
                                            "dosageForm": XML_values.get('DosageForm', '').upper(),
                                            "charNumFragments": XML_values.get('SPLIMPRINT', ''),
                                            "charShape": XML_values.get('SPLSHAPE', '').upper(),
                                            "charSize": XML_values.get('SPLSIZE', ''),
                                            "charColor": XML_values.get('SPLCOLOR', '').upper(),
                                            "routeOfAdministration": XML_values.get('routeAdmin', '').upper()
                                        }
                                    ]
                                }
                    except Exception as e:
                        print(f"[ERROR] Failed to create GSRSProduct. Error: {str(e)}")
                        GSRSProduct = {}
        log_message=f"[SUCCESS] parse XML file: {file_path}"
        log_to_file(log_file_path, log_message)                
    except Exception as e:
        print('key', file_path)
        log_message=f"[ERROR] Failed to parse XML file: {file_path}. Error: {e}"
        log_to_file(log_file_path, log_message)
        GSRSProduct = {}    
        #print(error,f"[ERROR] Failed to parse XML file: {file_path}. Error: {e}")
        #GSRSProduct = None
    # Return the constructed GSRSProduct JSON
    return GSRSProduct

# Function to process multiple XML files
def process_xml_files(folder_path, data_dictionary, log_file_path):
    xml_files = [filename for filename in os.listdir(folder_path) if filename.endswith(".xml")]
    parsed_data = []
    for filename in xml_files:
        file_path = os.path.join(folder_path, filename)
        parsed_data.append(parse_xml_file(file_path, data_dictionary, log_file_path))
    return parsed_data

# Function to save parsed data as JSON files in a zip archive
def save_data_as_zip(data_list, output_zip):
    with zipfile.ZipFile(output_zip, 'w') as zipf:
        for index, data in enumerate(data_list):
            if data:
                json_filename = f"data_{index + 1}.json"
                with zipf.open(json_filename, 'w') as json_file:
                    json_file.write(json.dumps(data).encode('utf-8'))
    #print(f"[INFO] Created zip file: {output_zip}")

# Function to load data from a zip file containing JSON files
def load_data_from_zip(zip_file_path):
    data_list = []
    with zipfile.ZipFile(zip_file_path, 'r') as zipf:
        for file_name in zipf.namelist():
            if file_name.endswith(".json"):
                with zipf.open(file_name) as json_file:
                    data = json.load(json_file)
                    data_list.append(data)
    #print(f"[INFO] Loaded {len(data_list)} JSON files from the zip archive.")
    return data_list

# Entry point for XML parsing
if __name__ == "__main__":
    folder_path = 'C:\\Users\\Arunasri.Nishtala\\Desktop\\Products\\SPLxml7-11-24\\only_xmls\\only_xmls'
    log_file_path = 'C:\\Users\\Arunasri.Nishtala\\Desktop\\Products\\SPLxml7-11-24\\only_xmls\\log_11-1-5_34pm.txt'
    output_zip = 'C:\\Users\\Arunasri.Nishtala\\Desktop\\Products\\SPLxml7-11-24\\only_xmls\\complete_product11-1-5_34pm.zip'

    # Load your CSV data if needed
    csv_file_path = 'C:\\Users\\Arunasri.Nishtala\\Desktop\\Products\\Substance_UUID_UNII_Production.csv'
    key_column = 'UNII'
    value_column = 'UUID'
    data_dictionary = csv_to_transformed_dict(csv_file_path, key_column, value_column)

    # Process XML files and create zip archive with JSONs
    parsed_data = process_xml_files(folder_path, data_dictionary, log_file_path)
    save_data_as_zip(parsed_data, output_zip)

    # Example of loading data from the created zip file
    loaded_data = load_data_from_zip(output_zip)
