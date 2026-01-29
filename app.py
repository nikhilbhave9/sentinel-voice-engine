import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Sentinel Insurance Agent",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🛡️ Sentinel Insurance Agent")
    st.subheader("How can I help you today?")
    
    # Placeholder for future components
    st.info("Sentinel Insurance Agent is initializing...")
    st.write("This is the foundation for the conversational AI insurance agent.")
    
    # Basic sidebar placeholder
    with st.sidebar:
        st.header("Session Information")
        st.write("Session statistics will appear here")

if __name__ == "__main__":
    main()