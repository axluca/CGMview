import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import io
from medical_data_parser import MedicalDataParser  # Import your existing parser

def create_plot(blocks):
    """Create time series plot with all specified elements"""
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Process glucose data
    glucose_df = blocks.get('Glucose_concentration', pd.DataFrame())
    if not glucose_df.empty:
        # Split glucose values into in-range and out-of-range
        in_range = glucose_df[
            (glucose_df['conc'] >= 3.9) & 
            (glucose_df['conc'] <= 10.0)
        ]
        out_range = glucose_df[
            (glucose_df['conc'] < 3.9) | 
            (glucose_df['conc'] > 10.0)
        ]
        
        # Add in-range glucose values (filled circles)
        fig.add_trace(
            go.Scatter(
                x=in_range['Time'],
                y=in_range['conc'],
                mode='markers',
                name='Glucose (In Range)',
                marker=dict(size=8, color='blue', symbol='circle'),
            ),
            secondary_y=True
        )
        
        # Add out-of-range glucose values (empty circles)
        fig.add_trace(
            go.Scatter(
                x=out_range['Time'],
                y=out_range['conc'],
                mode='markers',
                name='Glucose (Out of Range)',
                marker=dict(size=8, color='blue', symbol='circle-open'),
            ),
            secondary_y=True
        )
    
    # Add insulin infusion as continuous line
    infusion_df = blocks.get('Insulin_infusion', pd.DataFrame())
    if not infusion_df.empty:
        fig.add_trace(
            go.Scatter(
                x=infusion_df['Time'],
                y=infusion_df['Rate'],
                mode='lines',
                name='Insulin Infusion',
                line=dict(color='blue'),
            ),
            secondary_y=False
        )
    
    # Add meal data as labels on top
    meal_df = blocks.get('Meal', pd.DataFrame())
    if not meal_df.empty:
        for _, row in meal_df.iterrows():
            fig.add_annotation(
                x=row['Time'],
                y=1.1,
                text=f"Meal: {row['CHO']}g",
                showarrow=True,
                arrowhead=2,
                yref="paper"
            )
    
    # Add insulin bolus as labels
    bolus_df = blocks.get('Insulin_bolus', pd.DataFrame())
    if not bolus_df.empty:
        for _, row in bolus_df.iterrows():
            fig.add_annotation(
                x=row['Time'],
                y=1.05,
                text=f"Bolus: {row['Bolus']}U",
                showarrow=True,
                arrowhead=2,
                yref="paper"
            )
    
    # Update layout
    fig.update_layout(
        title="Glucose and Insulin Time Series",
        xaxis_title="Time (24H)",
        xaxis=dict(
            tickformat="%H:%M",
            tickmode="auto",
            nticks=24
        ),
        height=800,
        showlegend=True,
        margin=dict(t=150)  # Extra margin for annotations
    )
    
    # Update y-axes
    fig.update_yaxes(
        title_text="Basal Rate (U/h)",
        secondary_y=False
    )
    fig.update_yaxes(
        title_text="Glucose (mmol/L)",
        range=[0, 20],
        secondary_y=True
    )
    
    return fig

def main():
    st.title("Medical Data Visualization")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a file", 
        type=['txt', 'csv'],
        help="Upload your medical data file (TXT or CSV format)"
    )
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        with open("temp_file.txt", "wb") as f:
            f.write(uploaded_file.getvalue())
        
        # Process file with existing parser
        parser = MedicalDataParser("temp_file.txt")
        parser.process_blocks()
        
        # Show data summary
        st.subheader("Data Summary")
        for name, df in parser.blocks.items():
            with st.expander(f"Block: {name}"):
                st.write(f"Number of rows: {len(df)}")
                st.write(f"Number of columns: {len(df.columns)}")
                st.dataframe(df.head())
        
        # Create and display plot
        st.subheader("Time Series Visualization")
        fig = create_plot(parser.blocks)
        st.plotly_chart(fig, use_container_width=True)
        
        # Export to Excel
        if st.button("Export to Excel"):
            # Create Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for block_name, df in parser.blocks.items():
                    df.to_excel(writer, sheet_name=block_name, index=False)
            
            # Prepare download button
            st.download_button(
                label="Download Excel file",
                data=output.getvalue(),
                file_name="medical_data_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
