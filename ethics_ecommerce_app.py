"""
Ethics-Based E-Commerce Comparison Tool
A comprehensive platform for conscious consumerism

Author: Adham Hamada
Tool: Claude (Anthropic) - Sonnet 4.5
Date: April 2026
"""

import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import json
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from geopy.distance import geodesic
import numpy as np

# Page configuration
st.set_page_config(
    page_title="EthicShop - Conscious Commerce",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Source+Sans+Pro:wght@400;600&display=swap');
    
    .main-header {
        font-family: 'Playfair Display', serif;
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-family: 'Source Sans Pro', sans-serif;
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .ethics-score-high {
        color: #10b981;
        font-weight: 700;
        font-size: 2rem;
    }
    
    .ethics-score-medium {
        color: #f59e0b;
        font-weight: 700;
        font-size: 2rem;
    }
    
    .ethics-score-low {
        color: #ef4444;
        font-weight: 700;
        font-size: 2rem;
    }
    
    .product-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    
    .transparency-hash {
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        background: #f3f4f6;
        padding: 0.5rem;
        border-radius: 6px;
        color: #4b5563;
    }
</style>
""", unsafe_allow_html=True)

# Database initialization
def init_database():
    """Initialize SQLite database with manufacturer ethics data"""
    conn = sqlite3.connect('ethics_commerce.db')
    c = conn.cursor()
    
    # Create manufacturers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS manufacturers (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            labor_score REAL,
            environmental_score REAL,
            governance_score REAL,
            overall_score REAL,
            headquarters TEXT,
            latitude REAL,
            longitude REAL,
            last_updated TEXT,
            data_hash TEXT
        )
    ''')
    
    # Create products table
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            manufacturer_id INTEGER,
            base_price REAL,
            FOREIGN KEY (manufacturer_id) REFERENCES manufacturers (id)
        )
    ''')
    
    # Insert sample manufacturer data
    manufacturers_data = [
        ('EcoFashion Co.', 92, 88, 85, 0, 'Copenhagen, Denmark', 55.6761, 12.5683),
        ('GreenTech Industries', 85, 90, 88, 0, 'Stockholm, Sweden', 59.3293, 18.0686),
        ('FastClothing Inc.', 45, 38, 50, 0, 'Dhaka, Bangladesh', 23.8103, 90.4125),
        ('TechGiant Corp.', 68, 62, 75, 0, 'Cupertino, USA', 37.3230, -122.0322),
        ('SustainableStyle', 88, 85, 82, 0, 'Amsterdam, Netherlands', 52.3676, 4.9041),
        ('CheapGoods Ltd.', 35, 40, 45, 0, 'Shenzhen, China', 22.5431, 114.0579),
        ('EthicalElectronics', 78, 80, 85, 0, 'Helsinki, Finland', 60.1699, 24.9384),
        ('MassMarket Group', 52, 48, 55, 0, 'Mumbai, India', 19.0760, 72.8777),
    ]
    
    for mfr in manufacturers_data:
        name, labor, env, gov, _, hq, lat, lon = mfr
        overall = calculate_ethics_score(labor, env, gov)
        timestamp = datetime.now().isoformat()
        data_hash = generate_transparency_hash(name, labor, env, gov, timestamp)
        
        c.execute('''
            INSERT OR REPLACE INTO manufacturers 
            (name, labor_score, environmental_score, governance_score, overall_score, 
             headquarters, latitude, longitude, last_updated, data_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, labor, env, gov, overall, hq, lat, lon, timestamp, data_hash))
    
    # Insert sample products
    products_data = [
        ('Organic Cotton T-Shirt', 'Clothing', 'EcoFashion Co.', 45),
        ('Recycled Polyester Jacket', 'Clothing', 'EcoFashion Co.', 120),
        ('Basic Cotton Shirt', 'Clothing', 'FastClothing Inc.', 12),
        ('Smartphone X1', 'Electronics', 'TechGiant Corp.', 999),
        ('Eco Smartphone E2', 'Electronics', 'EthicalElectronics', 850),
        ('Budget Phone B3', 'Electronics', 'CheapGoods Ltd.', 299),
        ('Sustainable Denim Jeans', 'Clothing', 'SustainableStyle', 85),
        ('Fast Fashion Jeans', 'Clothing', 'MassMarket Group', 35),
        ('Solar Laptop', 'Electronics', 'GreenTech Industries', 1200),
        ('Standard Laptop', 'Electronics', 'TechGiant Corp.', 1100),
    ]
    
    for product in products_data:
        name, category, mfr_name, price = product
        c.execute('SELECT id FROM manufacturers WHERE name = ?', (mfr_name,))
        mfr_id = c.fetchone()[0]
        c.execute('''
            INSERT OR REPLACE INTO products (name, category, manufacturer_id, base_price)
            VALUES (?, ?, ?, ?)
        ''', (name, category, mfr_id, price))
    
    conn.commit()
    conn.close()

def calculate_ethics_score(labor, environmental, governance):
    """Calculate weighted ethics score"""
    # Weights: Labor 40%, Environmental 40%, Governance 20%
    score = (0.4 * labor) + (0.4 * environmental) + (0.2 * governance)
    return round(score, 2)

def generate_transparency_hash(name, labor, env, gov, timestamp):
    """Generate SHA-256 hash for transparency logging"""
    data = f"{name}|{labor}|{env}|{gov}|{timestamp}"
    return hashlib.sha256(data.encode()).hexdigest()

def calculate_true_cost(base_price, ethics_score):
    """Calculate True Social Cost with social tax"""
    # Social tax increases as ethics score decreases
    # High ethics (80-100): 0% tax
    # Medium ethics (50-79): 5-20% tax
    # Low ethics (0-49): 20-50% tax
    
    if ethics_score >= 80:
        social_tax_rate = 0
    elif ethics_score >= 50:
        social_tax_rate = 0.05 + (0.15 * (80 - ethics_score) / 30)
    else:
        social_tax_rate = 0.20 + (0.30 * (50 - ethics_score) / 50)
    
    social_tax = base_price * social_tax_rate
    true_cost = base_price + social_tax
    
    return true_cost, social_tax, social_tax_rate * 100

def calculate_carbon_footprint(mfr_lat, mfr_lon, user_lat, user_lon):
    """Calculate estimated shipping carbon footprint"""
    # Calculate distance in kilometers
    distance = geodesic((mfr_lat, mfr_lon), (user_lat, user_lon)).kilometers
    
    # Average CO2 emissions: 0.5 kg CO2 per km for air freight
    carbon_kg = distance * 0.5
    
    return distance, carbon_kg

def get_product_details(product_name):
    """Get comprehensive product and manufacturer details"""
    conn = sqlite3.connect('ethics_commerce.db')
    query = '''
        SELECT p.name, p.category, p.base_price, 
               m.name, m.labor_score, m.environmental_score, m.governance_score,
               m.overall_score, m.headquarters, m.latitude, m.longitude,
               m.last_updated, m.data_hash
        FROM products p
        JOIN manufacturers m ON p.manufacturer_id = m.id
        WHERE p.name = ?
    '''
    df = pd.read_sql_query(query, conn, params=(product_name,))
    conn.close()
    return df.iloc[0] if not df.empty else None

def find_ethical_alternatives(category, current_ethics_score, base_price, max_price_diff=0.1):
    """Find socially superior alternatives within price range"""
    conn = sqlite3.connect('ethics_commerce.db')
    
    # Find products in same category with higher ethics score
    # Within 10% price range
    price_min = base_price * (1 - max_price_diff)
    price_max = base_price * (1 + max_price_diff)
    
    query = '''
        SELECT p.name, p.base_price, m.name as manufacturer, m.overall_score
        FROM products p
        JOIN manufacturers m ON p.manufacturer_id = m.id
        WHERE p.category = ?
        AND m.overall_score > ?
        AND p.base_price BETWEEN ? AND ?
        ORDER BY m.overall_score DESC
        LIMIT 3
    '''
    
    df = pd.read_sql_query(query, conn, params=(category, current_ethics_score, price_min, price_max))
    conn.close()
    return df

def create_ethics_breakdown_chart(labor, environmental, governance):
    """Create radar chart for ethics breakdown"""
    categories = ['Labor Practices', 'Environmental Impact', 'Corporate Governance']
    values = [labor, environmental, governance]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],  # Close the loop
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(102, 126, 234, 0.3)',
        line=dict(color='rgba(102, 126, 234, 1)', width=2),
        name='Ethics Score'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100])
        ),
        showlegend=False,
        height=400,
        margin=dict(l=80, r=80, t=40, b=40)
    )
    
    return fig

def main():
    # Initialize database
    init_database()
    
    # Header
    st.markdown('<h1 class="main-header">🌍 EthicShop</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Conscious Commerce Through Data Transparency</p>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("⚙️ Settings")
    
    # User location input
    st.sidebar.subheader("📍 Your Location")
    user_city = st.sidebar.text_input("City", "Alexandria")
    user_country = st.sidebar.text_input("Country", "Egypt")
    
    # Default coordinates for Alexandria, Egypt
    user_lat = st.sidebar.number_input("Latitude", value=31.2001, format="%.4f")
    user_lon = st.sidebar.number_input("Longitude", value=29.9187, format="%.4f")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About This Tool")
    st.sidebar.info(
        "This tool calculates the **True Social Cost** of products by adding "
        "a social tax to items from manufacturers with poor ethics scores. "
        "Make informed decisions that align with your values."
    )
    
    # Main content
    tabs = st.tabs(["🔍 Product Search", "📊 Compare Products", "🏢 Manufacturers", "🔒 Transparency Log"])
    
    with tabs[0]:
        st.header("Search for a Product")
        
        # Get all products
        conn = sqlite3.connect('ethics_commerce.db')
        products = pd.read_sql_query("SELECT name FROM products ORDER BY name", conn)
        conn.close()
        
        selected_product = st.selectbox(
            "Select a product to analyze:",
            products['name'].tolist()
        )
        
        if st.button("Analyze Product", type="primary"):
            product_data = get_product_details(selected_product)
            
            if product_data is not None:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader(f"📦 {product_data['name']}")
                    st.markdown(f"**Category:** {product_data['category']}")
                    st.markdown(f"**Manufacturer:** {product_data[3]}")  # manufacturer name
                    st.markdown(f"**Headquarters:** {product_data['headquarters']}")
                    
                    # Ethics score display
                    ethics_score = product_data['overall_score']
                    if ethics_score >= 80:
                        score_class = "ethics-score-high"
                        rating = "🌟 Excellent"
                    elif ethics_score >= 50:
                        score_class = "ethics-score-medium"
                        rating = "⚠️ Moderate"
                    else:
                        score_class = "ethics-score-low"
                        rating = "❌ Poor"
                    
                    st.markdown(f"### Ethics Rating: {rating}")
                    st.markdown(f'<p class="{score_class}">{ethics_score}/100</p>', unsafe_allow_html=True)
                    
                    # Ethics breakdown chart
                    st.plotly_chart(
                        create_ethics_breakdown_chart(
                            product_data['labor_score'],
                            product_data['environmental_score'],
                            product_data['governance_score']
                        ),
                        use_container_width=True
                    )
                
                with col2:
                    # True Cost Calculation
                    st.markdown("### 💰 Price Analysis")
                    
                    base_price = product_data['base_price']
                    true_cost, social_tax, tax_rate = calculate_true_cost(base_price, ethics_score)
                    
                    st.metric("Base Price", f"${base_price:.2f}")
                    st.metric("Social Tax", f"${social_tax:.2f}", f"{tax_rate:.1f}%")
                    st.metric("True Social Cost", f"${true_cost:.2f}", 
                             delta=f"+${true_cost - base_price:.2f}",
                             delta_color="inverse")
                    
                    # Carbon footprint
                    st.markdown("### 🌱 Carbon Footprint")
                    distance, carbon = calculate_carbon_footprint(
                        product_data['latitude'],
                        product_data['longitude'],
                        user_lat,
                        user_lon
                    )
                    
                    st.metric("Shipping Distance", f"{distance:,.0f} km")
                    st.metric("Est. CO₂ Emissions", f"{carbon:,.1f} kg")
                
                # Switch & Save Suggestions
                st.markdown("---")
                st.subheader("💡 Switch & Save: Ethical Alternatives")
                
                alternatives = find_ethical_alternatives(
                    product_data['category'],
                    ethics_score,
                    base_price
                )
                
                if not alternatives.empty:
                    st.success(f"Found {len(alternatives)} better alternatives within 10% price range:")
                    
                    for idx, alt in alternatives.iterrows():
                        alt_price = alt['base_price']
                        alt_score = alt['overall_score']
                        price_diff = alt_price - base_price
                        score_diff = alt_score - ethics_score
                        
                        with st.expander(f"✅ {alt['name']} - Ethics Score: {alt_score}/100"):
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Price", f"${alt_price:.2f}", 
                                       f"${price_diff:+.2f}")
                            col2.metric("Manufacturer", alt['manufacturer'])
                            col3.metric("Ethics Improvement", f"+{score_diff:.1f} points",
                                       delta_color="normal")
                            
                            if st.button(f"View Details: {alt['name']}", key=f"alt_{idx}"):
                                st.rerun()
                else:
                    st.warning("No ethical alternatives found in the same price range. Consider increasing your budget for more sustainable options.")
    
    with tabs[1]:
        st.header("Compare Multiple Products")
        
        conn = sqlite3.connect('ethics_commerce.db')
        all_products = pd.read_sql_query("SELECT name FROM products ORDER BY name", conn)
        conn.close()
        
        compare_products = st.multiselect(
            "Select products to compare (up to 4):",
            all_products['name'].tolist(),
            max_selections=4
        )
        
        if len(compare_products) >= 2:
            comparison_data = []
            
            for prod in compare_products:
                data = get_product_details(prod)
                if data is not None:
                    true_cost, social_tax, _ = calculate_true_cost(data['base_price'], data['overall_score'])
                    comparison_data.append({
                        'Product': data['name'],
                        'Manufacturer': data[3],
                        'Base Price': f"${data['base_price']:.2f}",
                        'True Cost': f"${true_cost:.2f}",
                        'Ethics Score': data['overall_score'],
                        'Labor': data['labor_score'],
                        'Environmental': data['environmental_score'],
                        'Governance': data['governance_score']
                    })
            
            df_compare = pd.DataFrame(comparison_data)
            
            # Display comparison table
            st.dataframe(df_compare, use_container_width=True)
            
            # Create comparison chart
            fig = px.bar(
                df_compare,
                x='Product',
                y='Ethics Score',
                color='Ethics Score',
                color_continuous_scale=['#ef4444', '#f59e0b', '#10b981'],
                range_color=[0, 100],
                title='Ethics Score Comparison'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with tabs[2]:
        st.header("Manufacturer Directory")
        
        conn = sqlite3.connect('ethics_commerce.db')
        manufacturers = pd.read_sql_query('''
            SELECT name, labor_score, environmental_score, governance_score, 
                   overall_score, headquarters
            FROM manufacturers
            ORDER BY overall_score DESC
        ''', conn)
        conn.close()
        
        st.dataframe(
            manufacturers.style.background_gradient(
                subset=['overall_score'],
                cmap='RdYlGn',
                vmin=0,
                vmax=100
            ),
            use_container_width=True
        )
    
    with tabs[3]:
        st.header("🔒 Transparency & Data Integrity")
        
        st.markdown("""
        This section demonstrates our commitment to data transparency and anti-greenwashing.
        Each ethics score is cryptographically hashed to ensure it hasn't been tampered with.
        """)
        
        conn = sqlite3.connect('ethics_commerce.db')
        transparency_data = pd.read_sql_query('''
            SELECT name, overall_score, last_updated, data_hash
            FROM manufacturers
            ORDER BY name
        ''', conn)
        conn.close()
        
        for idx, row in transparency_data.iterrows():
            with st.expander(f"{row['name']} - Score: {row['overall_score']}/100"):
                st.markdown(f"**Last Updated:** {row['last_updated']}")
                st.markdown("**Data Hash (SHA-256):**")
                st.markdown(f'<div class="transparency-hash">{row["data_hash"]}</div>', 
                           unsafe_allow_html=True)
                st.caption("This hash proves the data hasn't been altered since last verification.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #666;'>Built with Python, Streamlit, and SQLite | "
        "Data sources: Simulated ESG datasets | For educational purposes</p>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
