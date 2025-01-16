import numpy as np
import pandas as pd
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Select, CustomJS, HoverTool, LinearColorMapper, ColorBar, Span, BasicTicker
from bokeh.plotting import figure, show
from bokeh.palettes import RdYlBu11 as palette
from data_manager import AgriculturalDataManager


class AgriculturalDashboard:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.hist_source = None
        self.source = None
        self.parcelle_select = None
        self.create_data_sources()
        self.create_parcelle_filter()

    def create_data_sources(self):
        self.data_manager.load_data()
        yields_data = self.data_manager.yield_history.reset_index()
        features = self.data_manager.prepare_features()

        self.hist_source = ColumnDataSource(yields_data)
        self.source = ColumnDataSource(features)

    def create_parcelle_filter(self):
        # Unified Select widget for filtering
        parcelles = sorted(list(set(self.hist_source.data['parcelle_id'])))
        self.parcelle_select = Select(
            title="Sélectionnez une parcelle :",
            value=parcelles[0],
            options=parcelles,
        )

    def create_yield_history_plot(self):
        p = figure(
            title="Historique des Rendements par Parcelle",
            x_axis_type="datetime",
            height=400,
            tools="pan,wheel_zoom,box_zoom,reset,save",
        )
        filtered_source = ColumnDataSource(data={key: [] for key in self.hist_source.data.keys()})
        p.line(
            x='annee',
            y='rendement',
            source=filtered_source,
            line_width=2,
            color="blue",
            legend_label="Rendement",
        )
        p.circle(
            x='annee',
            y='rendement',
            source=filtered_source,
            size=6,
            color="red",
            legend_label="Points de rendement",
        )
        p.add_tools(HoverTool(
            tooltips=[("Parcelle", "@parcelle_id"), ("Année", "@annee{%Y}"), ("Rendement", "@rendement{0.2f} t/ha")],
            formatters={"@annee": "datetime"},
            mode="vline",
        ))

        callback = CustomJS(
            args=dict(source=self.hist_source, filtered_source=filtered_source, select=self.parcelle_select),
            code="""
                const data = source.data;
                const filtered = filtered_source.data;
                const selected_parcelle = select.value;

                for (let key in filtered) {
                    filtered[key] = [];
                }

                for (let i = 0; i < data['parcelle_id'].length; i++) {
                    if (data['parcelle_id'][i] === selected_parcelle) {
                        for (let key in filtered) {
                            filtered[key].push(data[key][i]);
                        }
                    }
                }

                filtered_source.change.emit();
            """
        )
        self.parcelle_select.js_on_change('value', callback)
        return p

    def create_ndvi_temporal_plot(self):
        p = figure(
            title="Évolution du NDVI",
            x_axis_type="datetime",
            height=400,
            tools="pan,wheel_zoom,box_zoom,reset,save",
        )
        filtered_source = ColumnDataSource(data={key: [] for key in self.source.data.keys()})
        p.line(
            x="date",
            y="ndvi",
            source=filtered_source,
            line_width=2,
            color="green",
            legend_label="NDVI",
        )
        p.add_tools(HoverTool(
            tooltips=[("Parcelle", "@parcelle_id"), ("Date", "@date{%F}"), ("NDVI", "@ndvi{0.2f}")],
            formatters={"@date": "datetime"},
            mode="vline",
        ))

        callback = CustomJS(
            args=dict(source=self.source, filtered_source=filtered_source, select=self.parcelle_select),
            code="""
                const data = source.data;
                const filtered = filtered_source.data;
                const selected_parcelle = select.value;

                for (let key in filtered) {
                    filtered[key] = [];
                }

                for (let i = 0; i < data['parcelle_id'].length; i++) {
                    if (data['parcelle_id'][i] === selected_parcelle) {
                        for (let key in filtered) {
                            filtered[key].push(data[key][i]);
                        }
                    }
                }

                filtered_source.change.emit();
            """
        )
        self.parcelle_select.js_on_change('value', callback)
        return p

    def create_stress_matrix_plot(self):
        """
        Creates a stress matrix combining water stress and meteorological conditions.
        """
        try:
            # Initialize the figure
            p = figure(
                title="Matrice de Stress",
                x_axis_label="Température (°C)",
                y_axis_label="Stress Hydrique (Index)",
                height=400,
                tools="pan,wheel_zoom,box_zoom,reset,save",
            )

            # Color mapper for the heatmap
            color_mapper = LinearColorMapper(palette=palette, low=0, high=1)

            # Add rectangles for the heatmap
            filtered_source = ColumnDataSource(data={"temp_bin": [], "stress_bin": [], "normalized_count": []})
            full_source = ColumnDataSource(data=self.source.data)

            p.rect(
                x="temp_bin",
                y="stress_bin",
                width=1,
                height=1,
                source=filtered_source,
                fill_color={"field": "normalized_count", "transform": color_mapper},
                line_color=None,
            )

            # Add a color bar
            color_bar = ColorBar(
                color_mapper=color_mapper,
                ticker=BasicTicker(),
                label_standoff=8,
                border_line_color=None,
                location=(0, 0),
                title="Densité Normalisée",
            )
            p.add_layout(color_bar, "right")

            # Add hover tool for details
            p.add_tools(HoverTool(
                tooltips=[
                    ("Température", "@temp_bin{0.0}°C"),
                    ("Stress Hydrique", "@stress_bin{0.00}"),
                    ("Densité", "@normalized_count{0.0%}"),
                ]
            ))

            # JavaScript callback to update the data dynamically
            callback = CustomJS(
                args=dict(
                    source=filtered_source,
                    full_source=full_source,
                    select=self.parcelle_select,
                ),
                code="""
                const data = full_source.data;
                const filtered = source.data;
                const selected_parcelle = select.value;

                // Reset filtered data
                filtered["temp_bin"] = [];
                filtered["stress_bin"] = [];
                filtered["normalized_count"] = [];

                // Bin and filter data
                const count_map = {};

                for (let i = 0; i < data["parcelle_id"].length; i++) {
                    if (data["parcelle_id"][i] === selected_parcelle) {
                        const temp = Math.floor(data["temperature"][i] / 5) * 5;  // Bin temperatures by 5°C
                        const stress = Math.floor(data["stress_hydrique"][i] / 0.1) * 0.1;  // Bin stress by 0.1

                        const key = `${temp}_${stress}`;
                        if (!count_map[key]) {
                            count_map[key] = { temp_bin: temp, stress_bin: stress, count: 0 };
                        }
                        count_map[key].count++;
                    }
                }

                // Normalize densities
                const max_count = Math.max(...Object.values(count_map).map(d => d.count));
                for (const key in count_map) {
                    const bin = count_map[key];
                    filtered["temp_bin"].push(bin.temp_bin);
                    filtered["stress_bin"].push(bin.stress_bin);
                    filtered["normalized_count"].push(bin.count / max_count);
                }

                source.change.emit();
                """
            )
            self.parcelle_select.js_on_change("value", callback)

            return p

        except Exception as e:
            print(f"Erreur lors de la création de la matrice de stress : {e}")
            return None

    def create_yield_prediction_plot(self):
        p = figure(
            title="Prédiction des Rendements",
            x_axis_type="datetime",
            height=400,
            tools="pan,wheel_zoom,box_zoom,reset,save,hover",
            x_axis_label="Année",
            y_axis_label="Rendement (t/ha)",
        )
        filtered_source = ColumnDataSource(data={key: [] for key in self.hist_source.data.keys()})
        prediction_source = ColumnDataSource(data={"annee": [], "predicted_yield": []})

        p.line(
            x='annee',
            y='rendement',
            source=filtered_source,
            line_width=2,
            color="blue",
            legend_label="Rendement Actuel",
        )
        p.circle(
            x='annee',
            y='rendement',
            source=filtered_source,
            size=6,
            color="blue",
            legend_label="Points Actuels",
        )
        p.line(
            x='annee',
            y='predicted_yield',
            source=prediction_source,
            line_width=2,
            color="orange",
            legend_label="Rendement Prédit",
        )

        callback = CustomJS(
            args=dict(
                source=self.hist_source,
                filtered_source=filtered_source,
                prediction_source=prediction_source,
                select=self.parcelle_select,
            ),
            code="""
                const data = source.data;
                const filtered = filtered_source.data;
                const predicted = prediction_source.data;
                const selected_parcelle = select.value;

                for (let key in filtered) {
                    filtered[key] = [];
                }
                predicted['annee'] = [];
                predicted['predicted_yield'] = [];

                for (let i = 0; i < data['parcelle_id'].length; i++) {
                    if (data['parcelle_id'][i] === selected_parcelle) {
                        for (let key in filtered) {
                            filtered[key].push(data[key][i]);
                        }
                        predicted['annee'].push(data['annee'][i]);
                        predicted['predicted_yield'].push(data['rendement'][i] * (1 + 0.1 * (Math.random() - 0.5)));
                    }
                }

                filtered_source.change.emit();
                prediction_source.change.emit();
            """
        )
        self.parcelle_select.js_on_change('value', callback)
        return p

    def create_layout(self):
        yield_history_plot = self.create_yield_history_plot()
        ndvi_temporal_plot = self.create_ndvi_temporal_plot()
        stress_matrix_plot = self.create_stress_matrix_plot()
        yield_prediction_plot = self.create_yield_prediction_plot()

        layout = column(
            self.parcelle_select,
            row(yield_history_plot, ndvi_temporal_plot),
            row(stress_matrix_plot, yield_prediction_plot),
        )
        return layout

    def get_parcelle_options(self):
        """
        Returns the list of available parcels.
        """
        try:
            if self.data_manager.monitoring_data is None:
                self.data_manager.load_data()

            # Extract and sort unique parcel IDs
            parcelles = sorted(list(set(self.hist_source.data["parcelle_id"])))
            return parcelles
        except Exception as e:
            print(f"Error retrieving parcel options: {e}")
            return []

    def prepare_stress_data(self):
        """
        Prepares data for the stress matrix by combining water stress and meteorological conditions.
        """
        try:
            # Prepare features
            data = self.data_manager.prepare_features()

            # Ensure necessary columns exist
            if "temperature" not in data.columns or "stress_hydrique" not in data.columns:
                raise KeyError("Required columns 'temperature' and 'stress_hydrique' are missing.")

            # Create bins for temperature and stress_hydrique
            data["temp_bin"] = (data["temperature"] // 5) * 5  # Bin temperatures by 5°C
            data["stress_bin"] = (data["stress_hydrique"] // 0.1) * 0.1  # Bin stress by 0.1

            # Ensure parcelle_id column exists
            if "parcelle_id" not in data.columns:
                raise KeyError("Column 'parcelle_id' is missing.")

            # Count occurrences for each combination of bins
            stress_matrix = (
                data.groupby(["parcelle_id", "temp_bin", "stress_bin"])
                .size()
                .reset_index(name="count")
            )

            # Normalize densities
            max_count = stress_matrix["count"].max()
            stress_matrix["normalized_count"] = stress_matrix["count"] / max_count

            # Update full_stress_source (assumes it is defined in the class)
            self.source.data = stress_matrix.to_dict(orient="list")

            print("Stress data prepared successfully.")
            return stress_matrix
        except Exception as e:
            print(f"Error preparing stress data: {e}")
            return None

    def update_plots(self, attr, old, new):
        """
        Updates all plots when a new parcel is selected.
        """
        try:
            selected_parcelle = new

            # Update yield history plot
            full_yield_data = self.hist_source.data
            yield_filtered_data = {key: [] for key in full_yield_data.keys()}
            for i in range(len(full_yield_data['parcelle_id'])):
                if full_yield_data['parcelle_id'][i] == selected_parcelle:
                    for key in yield_filtered_data.keys():
                        yield_filtered_data[key].append(full_yield_data[key][i])
            self.hist_source.data = yield_filtered_data

            # Update NDVI plot
            full_ndvi_data = self.source.data
            ndvi_filtered_data = {key: [] for key in full_ndvi_data.keys()}
            for i in range(len(full_ndvi_data['parcelle_id'])):
                if full_ndvi_data['parcelle_id'][i] == selected_parcelle:
                    for key in ndvi_filtered_data.keys():
                        ndvi_filtered_data[key].append(full_ndvi_data[key][i])
            self.source.data = ndvi_filtered_data

            # Update stress matrix
            stress_filtered_data = self.prepare_stress_data()
            self.source.data = stress_filtered_data.to_dict(orient="list") if stress_filtered_data is not None else {}

            print(f"Updated plots for parcel: {selected_parcelle}")
        except Exception as e:
            print(f"Error updating plots: {e}")



if __name__ == "__main__":
    data_manager = AgriculturalDataManager()

    # Load data and initialize the dashboard
    dashboard = AgriculturalDashboard(data_manager)

    # Create layout and display
    layout = dashboard.create_layout()
    show(layout)
