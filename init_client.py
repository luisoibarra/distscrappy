import streamlit as st
"""
Start a DistscrappyClient connected to specified server in config.py
"""
from client.client import DistcrappyClient
import logging as log
from config import *



def start():
    st.info('''Availables commands:\n
             fetch URL1 URL2 URL3 [...] \n
            Example:\n 
             fetch www.wikipedia.org www.instagram.com''')
    urls = st.text_input('url(s) input', value='evea.uh.cu').split(" ")

    if st.button('fetch'):
        log.basicConfig(level=log.INFO)
        client = DistcrappyClient([x for x,_,_ in SERVER_NS_ZMQ_ADDRS])
        client.start(urls)
    
if __name__ == "__main__":
    start()
