from shared.const import *
import json
import http.client as http_c
import random
from typing import List,Dict
import streamlit as st
import streamlit.components.v1 as components  # Import Streamlit
import random as r



class DistcrappyClient:
    
    def __init__(self, server_dirs:List[IP_DIR]):
        self.server_dirs = server_dirs
        
    def get_urls(self, urls:List[str])->URLHTMLDict:
        """
        Request given urls.
        """
        server_dirs = self.server_dirs.copy()
        errors = []
        random.shuffle(server_dirs)
        for host, port in server_dirs:
            conn = http_c.HTTPConnection(host, port)
            try:
                
                urls = [url if url.find("http://")!= -1 else'http://' + url for url in urls]

                content = self.build_json_string(urls)
                conn.request("GET", "urls", content, {"Content-Length":len(content)})
                resp = conn.getresponse()
                code = resp.getcode()
                body = resp.read()
                if code == 200:
                    json_body = json.loads(body.decode())
                    return json_body
                else:
                    errors.append(body.decode())
            except http_c.error as exc:
                errors.append(exc.args[0])
        raise ConnectionError("\n".join(errors))
        
    def build_json_string(self, urls:List[str])->str:
        """
        Builds the request json body given the urls
        """
        json_dict = {
            URLS_KEY: urls
        }
        return json.dumps(json_dict)

    def start(self,urls):
        
        try:
            result = self.get_urls(urls)

            urls_html_dict,errors = result.values()

            for url, html in urls_html_dict.items():
                
                # Render the result, contained in a frame of size 200x200.
                components.html(html, width=800, height=600, scrolling=True)
                st.write(html)

            for url,error in errors.items():
                st.warning(url+" : "+error)


        except Exception as exc:
            st.write(exc)
                


# fetch http://www.cubaeduca.cu http://www.etecsa.cu http://www.uci.cu http://evea.uh.cu http://www.uo.edu.cu http://www.uclv.edu.cu http://covid19cubadata.uh.cu http://www.uh.cu
