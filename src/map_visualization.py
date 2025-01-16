import folium
import webbrowser  # Import the webbrowser module
import pandas as pd

from folium import plugins
from branca.colormap import LinearColormap
from data_manager import AgriculturalDataManager

class AgriculturalMap:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.map = None
        self.yield_colormap = LinearColormap(
            colors=["red", "yellow", "green"],
            vmin=0,
            vmax=12
        )

    
    def create_base_map(self):
        """
        Crée la carte de base avec les couches appropriées
        """
        try:
            # Load the data
            self.data_manager.load_data()
            features = self.data_manager.prepare_features()

            # Calculate the average latitude and longitude to center the map
            avg_latitude = features['latitude'].mean()
            avg_longitude = features['longitude'].mean()

            # Initialize the Folium map
            self.map = folium.Map(
                location=[avg_latitude, avg_longitude],
                zoom_start=13,
                tiles='OpenStreetMap'
            )

            # Add a layer control to the map
            folium.LayerControl().add_to(self.map)

            print("Base map created successfully.")
            return self.map

        except Exception as e:
            print(f"Error creating base map: {e}")
            return None

    def add_yield_history_layer(self):
        try:
            if self.map is None:
                raise ValueError("Base map not initialized. Call create_base_map first.")

            # Load the features data
            features = self.data_manager.prepare_features()

            # Ensure the data is loaded and contains the necessary columns
            if features is None or features.empty:
                raise ValueError("Yield history data is not loaded or is empty.")

            # Add yield history data to the map
            for _, row in features.iterrows():
                folium.CircleMarker(
                    location=(row['latitude'], row['longitude']),
                    radius=5,
                    color=self.yield_colormap(row['rendement']),
                    fill=True,
                    fill_color=self.yield_colormap(row['rendement']),
                    fill_opacity=0.7,
                    popup=f"Parcelle: {row['parcelle_id']}<br>Rendement: {row['rendement']} t/ha"
                ).add_to(self.map)

            print("Yield history layer added successfully.")
            return self.map

        except Exception as e:
            print(f"Error adding yield history layer: {e}")
            return None

    def add_current_ndvi_layer(self):
        try:
            if self.map is None:
                raise ValueError("Base map not initialized. Call create_base_map first.")

            # Load the features data
            features = self.data_manager.prepare_features()

            # Ensure the data is loaded and contains the necessary columns
            if features is None or features.empty:
                raise ValueError("NDVI data is not loaded or is empty.")

            # Create a colormap for NDVI values
            ndvi_colormap = LinearColormap(
                colors=["red", "yellow", "green"],
                vmin=features['ndvi'].min(),
                vmax=features['ndvi'].max()
            )

            # Add NDVI data to the map
            for _, row in features.iterrows():
                folium.CircleMarker(
                    location=(row['latitude'], row['longitude']),
                    radius=5,
                    color=ndvi_colormap(row['ndvi']),
                    fill=True,
                    fill_color=ndvi_colormap(row['ndvi']),
                    fill_opacity=0.7,
                    popup=f"Parcelle: {row['parcelle_id']}<br>NDVI: {row['ndvi']:.2f}"
                ).add_to(self.map)

            print("Current NDVI layer added successfully.")
            return self.map

        except Exception as e:
            print(f"Error adding current NDVI layer: {e}")
            return None

    def add_risk_heatmap(self):
        try:
            if self.map is None:
                raise ValueError("Base map not initialized. Call create_base_map first.")

            # Load the features data
            features = self.data_manager.prepare_features()

            # Ensure the data is loaded and contains the necessary columns
            if features is None or features.empty:
                raise ValueError("Risk data is not loaded or is empty.")

            # If 'risk_index' is missing, calculate it dynamically
            if 'risk_index' not in features.columns:
                print("Calculating risk metrics dynamically...")
                risk_metrics = self.data_manager.calculate_risk_metrics(features)
                if risk_metrics is not None:
                    features = pd.merge(features, risk_metrics, how='left', on=["parcelle_id", "culture"])

            # Check again if 'risk_index' exists
            if 'risk_index' not in features.columns:
                raise KeyError("Required column 'risk_index' is missing from the data.")

            # Prepare data for the heatmap
            heat_data = []
            for _, row in features.iterrows():
                try:
                    heat_data.append([row['latitude'], row['longitude'], row['risk_index']])
                except Exception as e:
                    print(f"Error adding row to heatmap: {e}, Row: {row}")

            # Convert all keys in the data to strings to prevent the camelize error
            heat_data = [
                [float(x[0]), float(x[1]), float(x[2])] for x in heat_data
            ]

            # Add the heatmap layer to the map
            folium.plugins.HeatMap(
                heat_data,
                name="Risk Heatmap",
                min_opacity=0.5,
                max_val=features['risk_index'].max(),
                radius=15,
                blur=10,
                gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1: 'red'}
            ).add_to(self.map)

            # Add a layer control to toggle the heatmap
            folium.LayerControl().add_to(self.map)

            print("Risk heatmap layer added successfully.")
            return self.map

        except Exception as e:
            print(f"Error adding risk heatmap layer: {e}")
            return None

if __name__ == "__main__":
    # Initialize the data manager and load data
    data_manager = AgriculturalDataManager()
    data_manager.load_data()

    # Create an instance of AgriculturalMap
    agri_map = AgriculturalMap(data_manager)

    # Create the base map
    agri_map.create_base_map()

    # Add the yield history layer
    agri_map.add_yield_history_layer()

    # Add the current NDVI layer
    agri_map.add_current_ndvi_layer()

    # Add the risk heatmap layer
    agri_map.add_risk_heatmap()

    # Save the map to an HTML file
    if agri_map.map:
        map_file = "agricultural_map.html"
        agri_map.map.save(map_file)
        print(f"Agricultural map saved to '{map_file}'.")

        # Automatically open the map in the default web browser
        webbrowser.open(map_file)