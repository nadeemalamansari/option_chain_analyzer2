"""
Chart generation
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


class ChartGenerator:
    """Generate charts for analysis"""
    
    def __init__(self, data: pd.DataFrame, spot_price: float):
        self.data = data
        self.spot_price = spot_price if spot_price else 0
    
    def create_oi_chart(self):
        """Create OI chart"""
        fig = go.Figure()
        
        if 'CE_OI' in self.data.columns:
            fig.add_trace(go.Bar(
                x=self.data['STRIKE'], y=self.data['CE_OI'],
                name='CE OI', marker_color='#4CAF50', opacity=0.7
            ))
        
        if 'PE_OI' in self.data.columns:
            fig.add_trace(go.Bar(
                x=self.data['STRIKE'], y=self.data['PE_OI'],
                name='PE OI', marker_color='#F44336', opacity=0.7
            ))
        
        if self.spot_price > 0:
            fig.add_vline(x=self.spot_price, line_dash="dash", line_color="blue")
        
        fig.update_layout(
            title="Open Interest Distribution",
            xaxis_title="Strike Price",
            yaxis_title="Open Interest",
            barmode='group',
            height=400
        )
        
        return fig
    
    def create_pcr_chart(self):
        """Create PCR chart"""
        fig = go.Figure()
        
        if 'STRIKE_PCR' in self.data.columns:
            fig.add_trace(go.Scatter(
                x=self.data['STRIKE'], y=self.data['STRIKE_PCR'],
                mode='lines+markers', name='PCR',
                line=dict(color='#FF9800', width=2)
            ))
        
        fig.add_hline(y=1, line_dash="dash", line_color="gray")
        fig.add_hline(y=0.5, line_dash="dash", line_color="green")
        fig.add_hline(y=1.5, line_dash="dash", line_color="red")
        
        fig.update_layout(
            title="Put-Call Ratio",
            xaxis_title="Strike Price",
            yaxis_title="PCR",
            height=400
        )
        
        return fig
    
    def create_volume_chart(self):
        """Create volume chart"""
        fig = go.Figure()
        
        if 'CE_VOLUME' in self.data.columns:
            fig.add_trace(go.Bar(
                x=self.data['STRIKE'], y=self.data['CE_VOLUME'],
                name='CE Volume', marker_color='#4CAF50', opacity=0.6
            ))
        
        if 'PE_VOLUME' in self.data.columns:
            fig.add_trace(go.Bar(
                x=self.data['STRIKE'], y=self.data['PE_VOLUME'],
                name='PE Volume', marker_color='#F44336', opacity=0.6
            ))
        
        fig.update_layout(
            title="Volume Distribution",
            xaxis_title="Strike Price",
            yaxis_title="Volume",
            barmode='group',
            height=400
        )
        
        return fig
    
    def create_support_resistance_chart(self, supports, resistances):
        """Create support/resistance chart"""
        fig = go.Figure()
        
        if 'TOTAL_OI' in self.data.columns:
            fig.add_trace(go.Bar(
                x=self.data['STRIKE'], y=self.data['TOTAL_OI'],
                name='Total OI', marker_color='lightgray', opacity=0.5
            ))
        
        for level in supports[:3]:
            fig.add_vline(
                x=level['strike'], line_dash="dash", line_color="green",
                annotation_text=f"S: {level['strike']}"
            )
        
        for level in resistances[:3]:
            fig.add_vline(
                x=level['strike'], line_dash="dash", line_color="red",
                annotation_text=f"R: {level['strike']}"
            )
        
        if self.spot_price > 0:
            fig.add_vline(
                x=self.spot_price, line_color="blue", line_width=2,
                annotation_text=f"Spot: {self.spot_price}"
            )
        
        fig.update_layout(height=400, title="Support & Resistance")
        
        return fig
    
    def create_heatmap(self):
        """Create OI heatmap"""
        if 'STRIKE' not in self.data.columns:
            return go.Figure()
        
        strikes = self.data['STRIKE'].values
        ce_oi = self.data.get('CE_OI', pd.Series([0]*len(strikes))).values
        pe_oi = self.data.get('PE_OI', pd.Series([0]*len(strikes))).values
        
        matrix = np.array([ce_oi, pe_oi])
        
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=strikes,
            y=['CE', 'PE'],
            colorscale='RdYlGn',
            showscale=True
        ))
        
        fig.update_layout(height=300, title="OI Heatmap")
        
        return fig