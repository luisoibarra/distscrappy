import streamlit as st
"""
Start a  Streamlit DistScrappyClient connected to specified server in config.py
"""
from client.client import DistScrappyClient
import logging as log
from config import *
import streamlit.components.v1 as components  # Import Streamlit


def start():
    st.info('''Availables commands:\n
             URL1 URL2 URL3 [...] \n
            Example:\n 
            -write your urls in the url(s) input zone with a space as separator
             www.wikipedia.org  http://www.instagram.com  \n
            - then click the fetch button to fetch those url\n
            -(Optional) mark the Show HTML Code before clicking fetch button to show the html code of the fetched page''')

    urls = st.text_input('url(s) input', value='evea.uh.cu').split(" ")
    
    html_code_chckbx = st.checkbox('Show html code', value=False)

    if st.button('fetch'):
        log.basicConfig(level=log.INFO)

        client = DistScrappyClient([x for x,_,_ in SERVER_NS_ZMQ_ADDRS])

        result = client.start(urls)

        urls_html_dict, errors = result.values()

        for url, html in urls_html_dict.items():

            # Render the result, contained in a frame of size 200x200.
            components.html(html, width=800, height=600, scrolling=True)

            if html_code_chckbx:
                st.write(html)

        for url, error in errors.items():
            st.error(url+" : "+error)
    
if __name__ == "__main__":
    start()
