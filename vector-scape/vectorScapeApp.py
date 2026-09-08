# pip install streamlit transformers torch scikit-learn plotly numpy torchvision
import streamlit as st
import torch
import numpy as np
import string
from collections import Counter
from transformers import AutoTokenizer, AutoModel
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Ultimate VectorScape",
    page_icon="🌌",
    layout="wide"
)

# --- HARDCODED STOPWORDS ---
STOPWORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she",
    "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that",
    "these", "those", "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an",
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of",
    "at", "by", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s",
    "t", "can", "will", "just", "don", "should", "now"
}

# --- CACHED MODEL LOADING ---
@st.cache_resource
def load_nlp_models():
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    return tokenizer, model

tokenizer, model = load_nlp_models()

# --- HELPER FUNCTIONS ---
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def get_embeddings(chunks, tokenizer, model):
    encoded_input = tokenizer(chunks, padding=True, truncation=True, return_tensors='pt')
    with torch.no_grad():
        model_output = model(**encoded_input)
    return mean_pooling(model_output, encoded_input['attention_mask']).numpy()

# --- UI LAYOUT ---
st.title("🌌 Ultimate VectorScape")
st.markdown("A deep-space semantic visualizer with K-Means clustering, nearest-neighbor analysis, and layered cosmic graphics.")

# Sidebar Controls
with st.sidebar:
    st.header("📝 Input Context")
    user_input = st.text_area(
        "Enter Context Prompt:", 
        height=200, 
        placeholder="Paste a rich paragraph of text here..."
    )
    
    st.divider()
    
    st.header("🎛️ Galaxy Controls")
    similarity_threshold = st.slider(
        "Constellation Links (Base Similarity)", 
        min_value=0.0, max_value=1.0, value=0.55, step=0.05
    )
    
    num_clusters = st.slider(
        "Number of Semantic Clusters (K-Means)", 
        min_value=2, max_value=8, value=4,
        help="How many distinct color groups the AI should try to organize words into based on meaning."
    )
    
    theme_choice = st.selectbox(
        "Galaxy Color Palette", 
        ["Plasma", "Magma", "Inferno", "Twilight", "Viridis", "Turbo"]
    )
    
    show_labels = st.toggle("Show Word Labels", value=True)
    
    st.divider()
    generate_btn = st.button("Generate Ultimate Galaxy", type="primary", use_container_width=True)

# Main Execution block
if generate_btn:
    if not user_input.strip():
        st.warning("⚠️ Please enter some text in the sidebar.")
    else:
        # --- 1. METRICS ---
        st.subheader("📊 Token Statistics")
        char_count = len(user_input)
        word_count = len(user_input.split())
        
        full_tokens_encoded = tokenizer(user_input)
        raw_tokens = tokenizer.convert_ids_to_tokens(full_tokens_encoded.input_ids)
        token_count = len(raw_tokens)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Words", word_count)
        col2.metric("Total Tokens", token_count)
        col3.metric("Character Count", char_count)
        
        with st.expander("View Tokenization Output (Sub-word Arrays)"):
            st.markdown(" ".join([f"`{t}`" for t in raw_tokens]))
            
        st.divider()

        # --- 2. PREPROCESSING ---
        translator = str.maketrans('', '', string.punctuation)
        clean_words = [w.translate(translator).lower() for w in user_input.split()]
        valid_words = [w for w in clean_words if w and w not in STOPWORDS and len(w) > 2]
        
        word_counts = Counter(valid_words)
        unique_chunks = list(word_counts.keys())
        frequencies = list(word_counts.values())
        
        if len(unique_chunks) < num_clusters:
            st.error(f"❌ Not enough unique words. You need at least {num_clusters} words for {num_clusters} clusters.")
        else:
            with st.spinner("Calculating hyperspace embeddings, running K-Means, and mapping coordinates..."):
                
                # --- 3. NLP & ML PIPELINE ---
                embeddings = get_embeddings(unique_chunks, tokenizer, model)
                
                # PCA to 3D Space
                pca = PCA(n_components=3)
                embeddings_3d = pca.fit_transform(embeddings)
                
                # K-Means Clustering for Semantic Coloring
                kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init='auto')
                cluster_labels = kmeans.fit_predict(embeddings)
                
                # Pairwise Cosine Similarity
                sim_matrix = cosine_similarity(embeddings)
                
                # --- 4. ADVANCED DATA PREP ---
                
                # A. Nearest Neighbors for Hover Text
                nearest_neighbors_text = []
                for i in range(len(unique_chunks)):
                    sims = sim_matrix[i]
                    # Get top 4 indices (including self)
                    top_indices = np.argsort(sims)[-4:][::-1]
                    # Filter out self and get the words
                    top_words = [unique_chunks[idx] for idx in top_indices if idx != i][:3]
                    nearest_neighbors_text.append(", ".join(top_words))
                
                # B. Weighted Lines (Strong vs Weak Links)
                strong_x, strong_y, strong_z = [], [], []
                weak_x, weak_y, weak_z = [], [], []
                
                strong_threshold = min(similarity_threshold + 0.12, 1.0)
                
                for i in range(len(unique_chunks)):
                    for j in range(i + 1, len(unique_chunks)):
                        sim = sim_matrix[i, j]
                        if sim > strong_threshold:
                            strong_x.extend([embeddings_3d[i, 0], embeddings_3d[j, 0], None])
                            strong_y.extend([embeddings_3d[i, 1], embeddings_3d[j, 1], None])
                            strong_z.extend([embeddings_3d[i, 2], embeddings_3d[j, 2], None])
                        elif sim > similarity_threshold:
                            weak_x.extend([embeddings_3d[i, 0], embeddings_3d[j, 0], None])
                            weak_y.extend([embeddings_3d[i, 1], embeddings_3d[j, 1], None])
                            weak_z.extend([embeddings_3d[i, 2], embeddings_3d[j, 2], None])

                # --- 5. PLOTLY VISUALIZATION ---
                fig = go.Figure()

                # Layer 1: Background Starfield
                pad = 0.5
                bg_x = np.random.uniform(embeddings_3d[:,0].min()-pad, embeddings_3d[:,0].max()+pad, 300)
                bg_y = np.random.uniform(embeddings_3d[:,1].min()-pad, embeddings_3d[:,1].max()+pad, 300)
                bg_z = np.random.uniform(embeddings_3d[:,2].min()-pad, embeddings_3d[:,2].max()+pad, 300)
                
                fig.add_trace(go.Scatter3d(
                    x=bg_x, y=bg_y, z=bg_z, mode='markers',
                    marker=dict(size=1.5, color='rgba(255, 255, 255, 0.4)'),
                    hoverinfo='none', showlegend=False
                ))

                # Layer 2: Weak Constellation Lines (Faint/Thin)
                if weak_x:
                    fig.add_trace(go.Scatter3d(
                        x=weak_x, y=weak_y, z=weak_z, mode='lines',
                        line=dict(color='rgba(150, 200, 255, 0.15)', width=1),
                        hoverinfo='none', showlegend=False
                    ))
                    
                # Layer 3: Strong Constellation Lines (Bright/Thick)
                if strong_x:
                    fig.add_trace(go.Scatter3d(
                        x=strong_x, y=strong_y, z=strong_z, mode='lines',
                        line=dict(color='rgba(200, 240, 255, 0.6)', width=2.5),
                        hoverinfo='none', showlegend=False
                    ))

                # Dynamic sizes based on word frequency
                base_sizes = np.array([5 + (f * 1.5) for f in frequencies])

                # Layer 4: Luminous Glow Effect (Larger, Transparent)
                fig.add_trace(go.Scatter3d(
                    x=embeddings_3d[:, 0], y=embeddings_3d[:, 1], z=embeddings_3d[:, 2],
                    mode='markers',
                    marker=dict(
                        size=base_sizes * 2,  # Double size for glow
                        color=cluster_labels,
                        colorscale=theme_choice,
                        opacity=0.15,         # Highly transparent
                    ),
                    hoverinfo='none', showlegend=False
                ))

                # Layer 5: Main Stars & Text
                hover_text = [
                    f"<b>{w.upper()}</b><br>Frequency: {f}<br>Cluster Group: {c+1}<br>Closest Matches: <i>{nn}</i>" 
                    for w, f, c, nn in zip(unique_chunks, frequencies, cluster_labels, nearest_neighbors_text)
                ]

                fig.add_trace(go.Scatter3d(
                    x=embeddings_3d[:, 0], y=embeddings_3d[:, 1], z=embeddings_3d[:, 2],
                    mode='markers+text' if show_labels else 'markers',
                    text=unique_chunks,
                    textposition='top center',
                    textfont=dict(color='rgba(255,255,255,0.9)', size=12),
                    hovertext=hover_text,
                    hoverinfo='text',
                    marker=dict(
                        size=base_sizes,
                        color=cluster_labels,
                        colorscale=theme_choice,
                        opacity=1.0,
                        line=dict(color='white', width=1.5) # Hard inner border
                    ),
                    showlegend=False
                ))

                # Space Theme Layout Optimization
                fig.update_layout(
                    height=800,
                    paper_bgcolor='#020008',
                    plot_bgcolor='#020008',
                    margin=dict(l=0, r=0, b=0, t=0),
                    scene=dict(
                        bgcolor='#020008',
                        xaxis=dict(showbackground=False, visible=False),
                        yaxis=dict(showbackground=False, visible=False),
                        zaxis=dict(showbackground=False, visible=False),
                        camera=dict(eye=dict(x=1.3, y=1.3, z=0.6))
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.info("💡 **Analysis Tip:** Words sharing the same color belong to the same semantic K-Means cluster. Hover over any node to see its closest semantic matches from the text!")
else:
    st.info("👈 Enter text in the sidebar and click **Generate Ultimate Galaxy**.")