import zipfile
import shutil
import os

zip_path = os.path.join('Challenge No Time To Waste', 'Daten', 'valhalla.zip')
target_dir = os.path.join('backend', 'valhalla_data')

# Clean directory
if os.path.exists(target_dir):
    print(f"Cleaning {target_dir}...")
    shutil.rmtree(target_dir)

os.makedirs(target_dir, exist_ok=True)

# Extract
print(f"Extracting {zip_path} to {target_dir}...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(target_dir)
    
print("Extraction complete.")
