import os
import pprint
import csv
import xml.etree.ElementTree as ET

# Folder path for XML files
folder_path = r'.//Only_xmls//Sample_forTest'
HL7 = {'hl7': 'urn:hl7-org:v3'}
c = 0

# Track fieldnames for each CSV file separately
csv_fieldnames = {}

# Function to append dictionary to the appropriate CSV file
def append_dict_to_csv(new_dict, csv_file, csv_key):
    # Update fieldnames set for each CSV file as needed
    if csv_key not in csv_fieldnames:
        csv_fieldnames[csv_key] = set(new_dict.keys())
        update_csv_headers(csv_file, csv_key)
    else:
        new_keys = set(new_dict.keys())
        if not csv_fieldnames[csv_key].issuperset(new_keys):
            # There are new keys, we need to update the CSV file headers
            csv_fieldnames[csv_key].update(new_keys)
            update_csv_headers(csv_file, csv_key)

    # Write the new dictionary as a row in the CSV
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=sorted(csv_fieldnames[csv_key]))
        writer.writerow(new_dict)

# Function to update the CSV headers when new keys are found
def update_csv_headers(csv_file, csv_key):
    # Read the current content of the file
    try:
        with open(csv_file, mode='r') as file:
            existing_data = list(csv.reader(file))
    except FileNotFoundError:
        # If the file doesn't exist yet, we just create it
        existing_data = []

    # Write back the file with updated headers
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=sorted(csv_fieldnames[csv_key]))
        
        # Write the header
        writer.writeheader()
        
        # Write back the old data if present (without the old header)
        if len(existing_data) > 1:
            for row in existing_data[1:]:
                writer.writerow(dict(zip(existing_data[0], row)))

# Process XML files
for file_name in os.listdir(folder_path):
    file = os.path.join(folder_path, file_name)
    c += 1
    print(c)
    try:
        tree = ET.parse(file)
        root = tree.getroot()
    except:
        continue

    XML_values = {}
    Author = {'MAH*': ''}
    represented_org_element = root.find('.//hl7:author/hl7:assignedEntity/hl7:representedOrganization', HL7)
    try:
        Author['MAH*'] = represented_org_element.find('.//hl7:name', HL7).text if represented_org_element is not None else ''
    except:
        pass

    for component in root.findall('.//hl7:component/hl7:section/hl7:subject', HL7):
        for manufacturedProduct in component.findall('.//hl7:manufacturedProduct', HL7):
            XML_values = {'Route of Administration': '', 'MAH*': Author['MAH*']}
            for consumedIn in manufacturedProduct.findall('.//hl7:consumedIn', HL7):
                for substanceAdministration in consumedIn.findall('.//hl7:substanceAdministration', HL7):
                    Administcode = substanceAdministration.find('.//hl7:routeCode', HL7) if substanceAdministration is not None else 'na'
                    XML_values['Route of Administration'] = Administcode.get('displayName')
                    
            XML_values['Medicinal Product Name'] = manufacturedProduct.find('.//hl7:name', HL7).text if manufacturedProduct.find('.//hl7:name', HL7) is not None else 'na'
            XML_values['County Code'] = 'USA'
            XML_values['Dosa Form Terminology'] = 'NA'
            XML_values['Pharmaceutical Dosa Form'] = manufacturedProduct.find('.//hl7:formCode', HL7).get('displayName') if manufacturedProduct.find('.//hl7:formCode', HL7) is not None else 'na'

            substance = 0
            for ingredient in manufacturedProduct.findall('.//hl7:ingredient', HL7):
                ingredient_substance = ingredient.find('.//hl7:ingredientSubstance', HL7)
                ingredientTypeXML = ingredient.get('classCode')
                
                if ingredientTypeXML in ['ACTIB', 'ACTIM', 'ACTIR']:
                    substance += 1
                    quantity = ingredient.find('.//hl7:quantity', HL7)
                    active_moiety = ingredient.find('.//hl7:activeMoiety', HL7)
                    try:
                        if ingredient_substance is not None and quantity is not None:
                            XML_values[f'{substance} Substance Type'] = ingredientTypeXML
                            XML_values[f'{substance} Substance'] = ingredient_substance.find('.//hl7:name', HL7).text
                            XML_values[f'{substance} Strength Value'] = f"{quantity.find('.//hl7:numerator', HL7).get('value')}/{quantity.find('.//hl7:denominator', HL7).get('value')}"
                            XML_values[f'{substance} Strength Unit'] = f"{quantity.find('.//hl7:numerator', HL7).get('unit')}/{quantity.find('.//hl7:denominator', HL7).get('unit')}"
                            XML_values[f'{substance} Reference Substance'] = active_moiety.find('.//hl7:name', HL7).text
                            XML_values[f'{substance} Reference Strength Value'] = 'na'
                            XML_values[f'{substance} Reference Strength Unit'] = 'na'
                    except:
                        pass

            for asContent in component.findall('.//hl7:asContent', HL7):
                try:
                    key = asContent.find('.//hl7:containerPackagedProduct', HL7).find('.//hl7:code', HL7).get('code', 'na')
                    XML_values['formCode_Name'] = asContent.find('.//hl7:containerPackagedProduct', HL7).find('.//hl7:formCode', HL7).get('displayName', 'na')
                    
                    if XML_values['formCode_Name'] != "CARTON":
                        key = asContent.find('.//hl7:containerPackagedProduct', HL7).find('.//hl7:code', HL7).get('code', 'na')
                        XML_values['NDC Code'] = asContent.find('.//hl7:containerPackagedProduct', HL7).find('.//hl7:code', HL7).get('code', 'na')
                        print(key)
                    else:
                        key = manufacturedProduct.find('.//hl7:code', HL7).get('code')
                        XML_values['NDC Code'] = manufacturedProduct.find('.//hl7:code', HL7).get('code')
                        print('except', key)
                except:
                    key = manufacturedProduct.find('.//hl7:code', HL7).get('code')
                    
                XML_values['Product_Type'] = root.find('.//hl7:code', HL7).get('displayName')
                XML_values['DailyMed Reference (Set_Id)'] = root.find('.//hl7:setId', HL7).get('root')
                XML_values['URL'] = 'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=' + XML_values['DailyMed Reference (Set_Id)']
                
                # Determine the CSV file name dynamically based on substance count
                csv_file = f'.//substance{substance}.csv'

                NDC_xml = {key: XML_values}
                pp = pprint.PrettyPrinter(indent=4)
                pp.pprint(NDC_xml)
                
                # Append the XML values to the appropriate CSV file
                append_dict_to_csv(XML_values, csv_file, substance)
                
            break
