import multiprocessing
import requests
import xml_parser
import time
from datetime import datetime

def upload_data(filename, data, url, headers):
    try:
        response = requests.post(url, json=data, headers=headers, verify=False)
        if response.status_code == 200:
            print(f"[INFO] Uploaded: {filename}")
        else:
            print(f"[WARNING] Failed to upload {filename}. Status Code: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Exception occurred during upload of {filename}: {e}")


def upload_files_in_batches(data_list, batch_size, url, headers):
    print("[INFO] Starting batch upload of data...")

    # Create a pool of workers based on the number of CPU cores
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        for i in range(0, len(data_list), batch_size):
            batch_data = data_list[i:i + batch_size]
            for index, data in enumerate(batch_data):
                try:
                    if data is not None:
                        filename = f"data_{i + index + 1}.json"
                        pool.apply_async(upload_data, args=(filename, data, url, headers))
                    else:
                        print(f"[WARNING] Skipping upload for data index {i + index + 1} because it is None")
                except Exception as e:
                    print(f"[ERROR] Exception occurred while preparing upload for data index {i + index + 1}: {e}")

        
        pool.close()
        pool.join()

    print("[INFO] Completed batch upload.")

if __name__ == "__main__":
    batch_size = 50
    urlPROD = 'https://gsrs.fda.gov/api/v1/products'  
    headersPROD = {'auth-key':"CWHG1Lrkri5uMyjiJeOP",'auth-username':'Arunasri.Nishtala', 'Content-Type':'application/json'}
    try:
        
        data_zip_path = 'C:\\Users\\Arunasri.Nishtala\\Desktop\\Products\\SPLxml7-11-24\\only_xmls\\data9_productlevel_123k2.zip'
        parsed_data = xml_parser.load_data_from_zip(data_zip_path)

        # Check if parsed_data is empty or None
        if not parsed_data:
            print("[ERROR] No data available to upload. Please check the data.zip file.")
        else:
            # Upload data in batches
            upload_files_in_batches(parsed_data, batch_size, urlPROD, headersPROD)
    except Exception as e:
        print(f"[ERROR] An error occurred in the main upload process: {e}")

