import requests
from bs4 import BeautifulSoup

# ===========================
# Extract Content from URL
# ===========================
"""
这部分代码用于从给定的URL中提取正文。
使用BeautifulSoup和requests库对网页进行解析并获取所需的内容。
"""

def get_web_page(url):
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"获取网页失败: {e}")
        return None

def extract_main_content(html):
    soup = BeautifulSoup(html, "html.parser")
    print(soup)
    
    # 移除无关的标签
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # 提取标题和正文
    content_dict = {}
    current_title = None
    #print(soup)
    
    # 查找rich_media_content div，如果不存在，则使用整个soup
    #content_container = soup.find("div", class_="rich_media_content") or soup
    content_containers = soup.find_all(lambda tag: tag.name == 'div' and 'rich_media_content' in tag.get('class', ''))
    #print(content_containers)
    content_container = content_containers[0] if content_containers else soup
    #print(content_container)
    current_title = "default"
    content_dict = {"default": ""}
    for tag in content_container.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "span", "section"]):
        if tag.name.startswith("h"):
            current_title = tag.get_text().strip()
            if current_title not in content_dict:
                content_dict[current_title] = ""
        elif tag.name in ["p", "span", "section"] and current_title is not None:
            text = tag.get_text()
            if text not in content_dict[current_title]:
                content_dict[current_title] += text + "\n"
    return content_dict

def extract_content_from_url(url):
    html = get_web_page(url)
    main_content = {}

    if html:
        main_content = extract_main_content(html)
    else:
        print("无法提取网页正文。")
    
    return main_content

# ===========================
# Summarize Extracted Content
# ===========================
"""
这部分代码基于langchain库对从URL提取的正文进行总结。
首先对每个标题及其对应的内容进行总结，然后再对所有标题的总结进行一次总结。
"""

from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
from langchain.docstore.document import Document

def merge_content(content_dict, chunk_size):
    split_content = {}

    # 检查 content_dict 中的每个值是否大于 chunk_size，如果是，则拆分为多个新值
    for key, value in content_dict.items():
        chunk_counter = 1
        while len(value) > chunk_size:
            new_key = f"{key}_{chunk_counter}"
            new_value, value = value[:chunk_size], value[chunk_size:]
            split_content[new_key] = new_value
            chunk_counter += 1
        split_content[key] = value

    merged_content = {}
    current_key = None
    current_value = ""

    for key, value in split_content.items():
        title_and_content = key + "\n" + value

        if not current_key:
            current_key = key
            current_value = title_and_content
        else:
            if len(current_value) + len(title_and_content) <= chunk_size:
                current_value += "\n" + title_and_content
            else:
                merged_content[current_key] = current_value
                current_key = key
                current_value = title_and_content

    if current_key:
        merged_content[current_key] = current_value

    return merged_content


def process_webhook(url: str) -> str:
    content_dict = extract_content_from_url(url)
    print(content_dict)

    webpage_content = merge_content(content_dict, chunk_size=2800)

    # 初始化 LLM
    llm = ChatOpenAI(
        model_name='gpt-3.5-turbo',
        temperature=0.5,
        max_tokens=1000,
    )

    # 提示模板
    templates = {
        "map_prompt_template": "Summarise the following section 请务必注意如果接下来的文本是中文那么就用中文回答，如果是英文那么就用英文回答，并且保留2条你觉得最受启发的原文，以枚举形式放在最后面，在回答中请务必以以下形式作区分'总结：你对这段文章的总结\n原文：你觉得比较好的原文': \n {text}",
        "combine_prompt_template": "这是一段对一篇文章分段的总结，请根据这些信息生成一个大纲，大纲将以层次化的方式组织信息，包含I（主要主题）、II（子主题）、III（关键论点）和IV（支持论据或详细信息），这一部分请用最精简的中文以结构化的形式输出，并在末尾附上对这篇文章的概要性总结；同时请根据'原文'中的内容，输出3条你觉得最有insight的原句，放在回答最后面, 尽量用中文回答，但不要损害原文意思：\n {text}",
    }

    map_prompt = PromptTemplate(template=templates["map_prompt_template"], input_variables=["text"])
    combine_prompt = PromptTemplate(template=templates["combine_prompt_template"], input_variables=["text"])

    chain = load_summarize_chain(
        llm=llm, chain_type="map_reduce",
        map_prompt=map_prompt,
        combine_prompt=combine_prompt,
        verbose=True,
        return_intermediate_steps=False,
    )

    # 对每个标题及其对应的内容进行摘要
    summaries = {}
    input_documents = []
    for title, content in webpage_content.items():
        input_documents = input_documents + [Document(page_content=title+"\n"+content)]

    chain = load_summarize_chain(llm, chain_type="map_reduce", return_intermediate_steps=False, map_prompt=map_prompt, combine_prompt=combine_prompt)
    final_summary = chain({"input_documents": input_documents}, return_only_outputs=True)
    return final_summary

if __name__ == "__main__":
    url = input("请输入网址: ")
    summary = process_webhook(url)
    print("Final Summary:\n", summary)

