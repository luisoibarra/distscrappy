import streamlit as st

#Start a  Streamlit DistScrappyClient connected to specified server in config.py

from client.client import DistScrappyClient
import logging as log
from config import *
import streamlit.components.v1 as components  # Import Streamlit
import os.path


def start():
    st.title("DistScrappy")
    st.info('''Availables commands:\n
             URL1 URL2 URL3 [...] \n
            Example:\n 
            -write your urls in the url(s) input zone with a space as separator
             www.wikipedia.org  http://www.instagram.com  \n
            -select the depth level to scrape for \n
            -then click the fetch button to fetch those url\n
            Before clicking fetch button you can check this options:\n
            -(Optional) mark the Show HTML to show the html code of the fetched page(s)\n
            -(Optional) mark the Save HTML to save the html code of the fetched page(s)\n
            ''')


    st.info('''We strongly recommend to use free sites such as :\n
    evea.uh.cu www.uci.cu \n ''')



    urls = st.text_input(
        'url(s) input', value='evea.uh.cu').split()  # www.uci.cu www.cubadebate.cu evea.uh.cu

    depth = st.sidebar.slider('Depth Level',
                              min_value=0, max_value=3, value=1, step=1)

    st.info('Time to scrape depends of depth level ,\
         the amount (and complexity) of the urls sites, and the network speed')

    

    
    html_code_chckbx = st.sidebar.checkbox('Show html code', value=False)

    html_save_chckbx = st.sidebar.checkbox('Save html code', value=False)

    if st.sidebar.button('fetch'):
        st.warning(
            "This action could take several minutes depending of depth level")
        i = 0
        progress_bar = st.progress(i)
        frame_text=st.empty()

        log.basicConfig(level=log.INFO)

        client = DistScrappyClient([x for x,_,_ in SERVER_NS_ZMQ_ADDRS])

        level_result = client.start(urls,depth)

        total = float(sum([ sum( [len(item) for item in dictio.values()] ) for dictio in level_result.values() ] ))
        

        for level,result_by_level_dict in level_result.items():

            st.header(f"Scrape Level {level}")

            urls_html_dict, errors = result_by_level_dict.values()

            for url, html in urls_html_dict.items():

                i+= 1.0
                progress_bar.progress(i/total)
                frame_text.text(f"url(s) {i}/{total}")

                st.write(int(i),'-',url, "👇")

                # Render the result, contained in a frame of size 200x200.
                components.html(html, width=800, height=600, scrolling=True)

                if html_code_chckbx:
                    st.write(html)

                if html_save_chckbx:
                    path = url[7:] if url[:7]=="http://" else url[8:]
                    path = "".join([char if not char in ['/',':','?','='] else "_" for char in path])
                    path=path+'.html'
                    if os.path.exists(path):
                        with open(path,'w', encoding='UTF-8') as f:
                            f.write(html)
                            f.close()
                    else:
                        with open(path, 'x', encoding='UTF-8') as f:
                            f.write(html)
                            f.close()

            for url, error in errors.items():
                st.error(url+" : "+error)
    
if __name__ == "__main__":
    start()
