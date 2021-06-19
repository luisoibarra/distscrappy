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
            -(Optional) mark the Show HTML Code before clicking \n
            fetch button to show the html code of the fetched page''')


    urls = st.text_input(
        'url(s) input', value='www.uh.cu').split(" ")  # www.uci.cu www.cubadebate.cu evea.uh.cu

    depth = st.number_input('depth level number',min_value=0,value=1,max_value=2)
    
    html_code_chckbx = st.checkbox('Show html code', value=False)

    #if st.button('fetch'):
    if True:
        log.basicConfig(level=log.INFO)

        client = DistScrappyClient([x for x,_,_ in SERVER_NS_ZMQ_ADDRS])

        level_result = client.start(urls,depth)

        level,result_by_level_dict = level_result.values()

        urls_html_dict, errors = result_by_level_dict.values()

        for url, html in urls_html_dict.items():

            # Render the result, contained in a frame of size 200x200.
            components.html(html, width=800, height=600, scrolling=True)

            if html_code_chckbx:
                st.write(html)

        for url, error in errors.items():
            st.error(url+" : "+error)
    
if __name__ == "__main__":
    start()
