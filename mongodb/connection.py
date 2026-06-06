from pymongo import MongoClient
import streamlit as st


@st.cache_resource
def get_database():
    """
    Create and return MongoDB database connection.
    """

    client = MongoClient(
        st.secrets["MONGO_URI"]
    )

    db = client["wifi_db"]

    return db


@st.cache_resource
def get_collection():
    """
    Return wifi_sessions collection.
    """

    db = get_database()

    collection = db["wifi_sessions"]

    return collection
