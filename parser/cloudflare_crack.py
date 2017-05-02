import re
import time
from functools import reduce

import requests
from bs4 import BeautifulSoup


def get_cookies_cloudflare():

    url_top = 'https://share.dmhy.org/'
    url_verify = 'https://share.dmhy.org/cdn-cgi/l/chk_jschl'

    s = requests.Session()

    r = s.get(url_top)
    lines = r.text.split('\n')

    def_line = lines[29].strip()
    var1,var2,origin = re.match('var s,t,o,p,b,r,e,a,k,i,n,g,f, ([A-Za-z]*)={"([A-Za-z]*)":(.*)};',def_line).groups()

    process_line = lines[36].strip()
    processes = list(map(lambda x:x[len(var1)+len(var2)+1:],process_line.split(';')[1:-3]))

    def conv2num(s):
        t = len(re.findall('\!\!',s))
        if s[0:2] == '!+':
            t += 1
        return t

    def split_digits(s):
        if s.find('(') == -1:
            return [s]
        else:
            return s[3:-2].split(')+(')

    def split_method(s):
        if s[1] == '=':
            method = s[0]
            process = s[2:]
        return method,process

    origin = [conv2num(i) for i in split_digits(origin)]
    origin_num = reduce(lambda x,y: 10*x+y,origin)

    for method_process in processes:
        method,process = split_method(method_process)
        digits = [conv2num(i) for i in split_digits(process)]
        num = reduce(lambda x,y: 10*x+y,digits)
        if method == '+':
            origin_num += num
        elif method == '-':
            origin_num -= num
        elif method == '*':
            origin_num *= num
        else:
            raise Exception

    jschl_answer = origin_num + 14

    soup = BeautifulSoup(r.text,'html.parser')
    jschl_vc = soup.find('input',attrs={'name':'jschl_vc'})['value']
    password = soup.find('input',attrs={'name':'pass'})['value']

    params = {'jschl_vc':jschl_vc,'pass':password,'jschl_answer':jschl_answer}
    time.sleep(5)
    r1 = s.get(url_verify,params = params)
    r2 = s.get(url_top)
    return dict(s.cookies)
