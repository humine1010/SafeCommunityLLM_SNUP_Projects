# step1. 관련 패키지 및 모듈 불러오기
from selenium import webdriver
from  selenium.webdriver.common.by  import  By
import time
import pandas as pd
from bs4 import BeautifulSoup
from tabulate import tabulate
from tavily import TavilyClient

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_upstage import ChatUpstage

import gradio as gr

from langchain_upstage import ChatUpstage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import AIMessage, HumanMessage


# step2. 네이버 뉴스 댓글정보 수집 함수
def get_naver_news_comments(url, wait_time=5, delay_time=0.1):

    # 크롬 드라이버로 해당 url에 접속
    driver = webdriver.Chrome()

    # (크롬)드라이버가 요소를 찾는데에 최대 wait_time 초까지 기다림 (함수 사용 시 설정 가능하며 기본값은 5초)
    driver.implicitly_wait(wait_time)

    # 인자로 입력받은 url 주소를 가져와서 접속
    driver.get(url)

    # 더보기가 안뜰 때 까지 계속 클릭 (모든 댓글의 html을 얻기 위함)
    while True:

        # 예외처리 구문 - 더보기 광클하다가 없어서 에러 뜨면 while문을 나감(break)
        try:
            more  =  driver.find_element(By.CLASS_NAME,  'u_cbox_btn_more')
            more.click()
            time.sleep(delay_time)

        except:
            break

    # 본격적인 크롤링 타임

    # selenium으로 페이지 전체의 html 문서 받기
    html = driver.page_source

    # 위에서 받은 html 문서를 bs4 패키지로 parsing
    soup = BeautifulSoup(html, 'lxml')

    # 1)작성자
    nicknames = soup.select('span.u_cbox_nick')
    list_nicknames = [nickname.text for nickname in nicknames]

    # 2)댓글 시간
    datetimes = soup.select('span.u_cbox_date')
    list_datetimes = [datetime.text for datetime in datetimes]

    # 3)댓글 내용
    contents = soup.select('span.u_cbox_contents') 
    list_contents = [content.text for content in contents]

    # 4)기사 본문
    articles = soup.select('article') 
    list_articles = [article.text.replace('\n', '') for article in articles]

    # 4)기사 본문
    titles = soup.select('h2.media_end_head_headline') 
    list_titles = [title.text for title in titles]

    # 4)작성자, 댓글 시간, 내용을 셋트로 취합
    list_sum = list(zip(list_nicknames,list_datetimes,list_contents))

    # 드라이버 종료
    driver.quit()

    # 함수를 종료하며 list_sum을 결과물로 제출
    return list_titles[0], list_articles[0], list_sum

def fact_check(text):
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    context = tavily.search(query=text)
    prompt_template = """너는 매우 훌륭하고 내가 100% 신뢰하는 믿음직스러운 어시스턴트야.
    context 내용을 참고해서 너가 할 수 있는 최고의 역량을 발휘해서 다음 텍스트가 사실인지 판단해줘.
    사실이라면 "참"라고 대답하고, 만약 context와 상충된 의견이 있다면 "거짓" 이라고 대답해줘.
    그리고 context에서 "참" 또는 "거짓"으로 판단한 근거를 함께 알려줘.
    "근거"는 개조식으로 간결하게 사실만 써주고 너의 어떠한 생각이나 사상을 덧붙이지 말아줘
    결과는 python dictionary 형태로 만들어줘. key 는 "결과"와 "근거" 이고 "근거"의 개조식 부분은 array로 구성해줘.
    할 수 있는 최선을 다해줘. 여기 텍스트와 대답 형식을 줄게:
    ---
    텍스트 : {text}
    ---
    context : {context}
    ---
    대답 : "결과" : (참 or 거짓), "근거": []
    """

    prompt = PromptTemplate.from_template(prompt_template)
    chain = prompt | ChatUpstage(api_key=UPSTAGE_API_KEY) | StrOutputParser()

    response = chain.invoke({"text": text, "context": context})
    return response

def classify_intent_of_message(message):
    prompt_template = """너는 매우 훌륭하고 내가 100% 신뢰하는 믿음직스러운 어시스턴트야.
    너가 할 수 있는 최고의 판단을 해서 다음 텍스트에서 많은 사람들에게 도움이 되는 정보가 포함되어 있는지 판단해줘.
    만약 이 글이 사람들에게 몰랐던 새로운 사실을 알려주는 이로운 글이라면 "예"라고 대답해줘.
    만약 이 글이 단순한 개인의 감정 표출이거나, 다른사람에게 질문하는 내용이거나, 개인적인 사항만 진술하고 있어서 사람들에게 도움이 되지 않는다면 "아니오" 라고 말해줘.
    너는 "예" 또는 "아니오"로만 대답해야 하고, 어떤 추가적인 정보를 이야기할 필요는 없어.
    할 수 있는 최선을 다해줘. 여기 텍스트를 줄게:
    ---
    텍스트: {message}
    ---
    대답 (예 또는 아니오): 
    """

    prompt = PromptTemplate.from_template(prompt_template)
    chain = prompt | ChatUpstage(api_key=UPSTAGE_API_KEY) | StrOutputParser()

    response = chain.invoke({"message": message})
    return response

def change_beauty_words(message):
    prompt_template = """너는 매우 훌륭하고 내가 100% 신뢰하는 믿음직스러운 어시스턴트야.
        너가 할 수 있는 최고의 판단을 해서 다음 텍스트에서 사실과 작성자의 의견으로 구분해서 따로 다시 작성해줘.
        "사실"이 포함된 부분은 개조식으로 간결하게 사실만 써주고 어떤 분야에 대한 정보인지도 알려주면 좋겠어.
        대신 작성자의 의견에 대해서는 아래의 작업을 거치려고해
        "의견" 부분은 너의 생각이나 사상을 덧붙이지 말고 순수하게 작성자의 의견만 담백하게 제공해줘
        안전한 커뮤니티를 위해 몇가지 작업을 거치려고해
        발언에서는 광고 / 정치 / 타인의 비방 / 감정적 글 여부 판단해서, 각 항목에 속하는 발언이 있다면 경고 문구를 작성해줘
        그리고, 해당 글의 목적을 간략하게 요약해줘
        또한 문맥을 파악해서 성적인 발언이나, 성희롱은 아예 삭제해줘.
        사회적으로 민감한 문장은 아예 삭제해줘
        그리고 삭제된 내용을 바탕으로 정보의 왜곡없이 최종적으로 한줄씩 존댓말인 종결 어미를 사용해서 누구도 상처받지 않을 공손한 문장으로 바꿔서 작성해줘.
        수정된 문장 제시해줘
        ---
        텍스트: {message}
        ---
    """

    prompt = PromptTemplate.from_template(prompt_template)
    chain = prompt | ChatUpstage(api_key=UPSTAGE_API_KEY) | StrOutputParser()

    response = chain.invoke({"message": message})
    return response






# 데이터 프레임을 엑셀로 저장 (파일명은 'news.xlsx', 시트명은 '뉴스 기사 제목')
# df.to_excel('news.xlsx', sheet_name='뉴스 기사 제목')


def chat(url, message):
        
    # 원하는 기사 url 입력
    #url = 'https://n.news.naver.com/article/214/0001349332?cds=news_media_pc'

    # 함수 실행
    title, article, replys = get_naver_news_comments(url)

    # 엑셀의 첫줄에 들어갈 컬럼명
    col = ['작성자','시간','내용']

    fact_res = fact_check(title)

    # pandas 데이터 프레임 형태로 가공
    df = pd.DataFrame(replys, columns=col)
    # print(tabulate(df, headers='firstrow', tablefmt='grid'))
    
    final_result = ''
    for index, row in df.iterrows():
        res = change_beauty_words(row['내용'])
        final_result += f"{index+1}. {res}"+"\n\n"

    final_res = '**해당 페이지 팩트 체크 정보는 아래와 같습니다. \n\n\n'+fact_res+'\n\n\n댓글 클린화 작업 결과: \n\n'+final_result
    return final_res
    
with gr.Blocks() as demo:
    chatbot = gr.ChatInterface(
        chat,
        examples=[
            "How to eat healthy?",
            "Best Places in Korea",
            "How to make a chatbot?",
        ],
        title="세이프 인터넷 커뮤니티",
        description="안전하고 클린한 인터넷 커뮤니티 문화 만들기! url을 입력하시면, 클린화 작업을 진행하겠습니다.",
        #textbox="클린화 작업을 하실 웹페이지 url을 입력해주세요."
    )
    chatbot.chatbot.height = 500



# step3. 실제 함수 실행 및 엑셀로 저장
if __name__ == '__main__': # 설명하자면 매우 길어져서 그냥 이렇게 사용하는 것을 권장

    demo.launch()


