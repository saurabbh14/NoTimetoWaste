import zipfile
import os
import tempfile
import geopandas as gpd
import folium
import fiona

def analyze_atkis_widths(zip_path, output_map="atkis_widths_map.html"):
    print(f"Extracting ATKIS data from {zip_path}...")
    
    with tempfile.TemporaryDirectory() as tmpdirname:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdirname)
            
        print("Searching for shapefiles containing road widths (checking schemas quickly)...")
        target_shp = None
        brf_col_name = None
        
        # Walk through extracted files to find shapefiles
        for root, dirs, files in os.walk(tmpdirname):
            for file in files:
                if file.endswith('.shp'):
                    shp_path = os.path.join(root, file)
                    try:
                        # Use fiona to quickly check the columns without loading data
                        with fiona.open(shp_path, 'r') as src:
                            schema_props = [c.upper() for c in src.schema['properties'].keys()]
                            if 'BRF' in schema_props or 'BREITEDERFAHRBAHN' in schema_props:
                                target_shp = shp_path
                                print(f"Found width data in: {file}")
                                # Get the exact original column name
                                original_cols = list(src.schema['properties'].keys())
                                brf_col_name = [c for c in original_cols if c.upper() in ['BRF', 'BREITEDERFAHRBAHN']][0]
                                break
                    except Exception as e:
                        pass
            if target_shp:
                break
                
        if not target_shp:
            print("Could not find any shapefiles with valid 'BRF' (breiteDerFahrBahn) attribute.")
            return

        print(f"Loading data from {os.path.basename(target_shp)}...")
        
        # Load the shapefile
        gdf = gpd.read_file(target_shp)
        
        # Ensure we have the width column and it's numeric
        gdf['BRF_VALUE'] = gdf[brf_col_name].astype(float)
        
        # Filter out null or zero widths
        target_gdf = gdf[gdf['BRF_VALUE'] > 0].copy()
        
        print(f"Total road segments with width data: {len(target_gdf)}")
        
        # Convert CRS to EPSG:4326 for Folium
        if target_gdf.crs is not None:
            print(f"Converting from {target_gdf.crs} to EPSG:4326...")
            target_gdf = target_gdf.to_crs(epsg=4326)
        
        # Now clip data to Jena's bounding box to speed up map rendering
        # Jena Bounding Box: (West, South, East, North)
        minx, miny, maxx, maxy = 11.5746, 50.9231, 11.5945, 50.9324
        print(f"Clipping data to Jena Bounding Box...")
        target_gdf = target_gdf.cx[minx:maxx, miny:maxy]
        
        print(f"Road segments within Jena: {len(target_gdf)}")

        # Create map centered around Jena
        m = folium.Map(location=[50.927, 11.583], zoom_start=14)
        
        print("Adding geometries to map...")
        # Truck width is 2.55m. Add a safety margin (e.g., 0.2m)
        min_width = 2.55
        
        def color_by_width(width):
            if width < min_width:
                return '#FF0000'      # Red: Too narrow
            elif width < 3.5:
                return '#FFA500'   # Orange: Tight
            else:
                return '#008000'    # Green: Good
                
        # Optimize map rendering by adding them as a single GeoJson layer
        # Apply style function
        def style_function(feature):
            w = feature['properties']['BRF_VALUE']
            color = color_by_width(w)
            return {
                'color': color,
                'weight': 4 if color == '#FF0000' else 2,
                'opacity': 0.8
            }
            
        folium.GeoJson(
            target_gdf,
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(fields=['BRF_VALUE'], aliases=['Width (m):'])
        ).add_to(m)
            
        map_path = os.path.join(os.path.dirname(__file__), output_map)
        m.save(map_path)
        print(f"\nSuccess! Map saved to {map_path}")
        print("Red: < 2.55m | Orange: 2.55m - 3.5m | Green: > 3.5m")

if __name__ == "__main__":
    zip_location = os.path.join(os.path.dirname(__file__), '..', 'Challenge No Time To Waste', 'Daten', 'atkis.basis-dlm.ver.zip')
    analyze_atkis_widths(zip_location)
