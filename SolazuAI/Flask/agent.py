import getpass
import os
import bs4
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.schema import HumanMessage
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from database import getPromptwithAgent, get_session_history, store_message
from dotenv import load_dotenv
from flask import jsonify
from langchain_core.documents import Document

# ------------------------ SETUP LANGCHAIN & OPENAI ------------------------
load_dotenv()
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
# ----------------------------------------------------------------------------



# ------------------------ SETUP LANGCHAIN & OPENAI ------------------------

def setup_prompts():
    prompt = getPromptwithAgent('CLARIFY')
    context = prompt.get('contextualize_q_system_prompt')
    qa = prompt.get('qa_system_prompt')
    contextualize_q_system_prompt = context
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    
    qa_system_prompt = qa + """\n\n{context}"""
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    return contextualize_q_prompt, qa_prompt

def setup_retriver():
    text_data = load_text_from_database()
    docs = [Document(page_content=f"Title: {entry['title']}\nContent: {entry['content']}") for entry in text_data]
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = []
    for doc in docs:
        splits.extend(text_splitter.split_documents([doc]))
    
    vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())
    retriever = vectorstore.as_retriever()
    return retriever

def rag_chains():
    retriever = setup_retriver()
    contextualize_q_prompt, qa_prompt = setup_prompts()
    history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt)
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    return rag_chain

# -------------------------------LOAD CONTEXT FROM DATABASE--------------------------------------------

def load_text_from_database():
    # Example text data
    text_data = [
        {
            "title": "Vietnamese Philosophical Thought",
            "content": "Vietnamese philosophical thought has evolved in a convoluted manner as a result of the country's vicissitudes past. Throughout this turbulent history, the Vietnamese have been influenced by many foreign cultures and religions. These impacts have changed the Vietnamese's consciousness, subsequently modified to create a unique Vietnamese traditional culture, among them is Confucianism. Confucianism, although it existed until the middle of the twentieth century, had a profound impact on its culture. Therefore, the core principles of Confucianism and its last long influence will be discussed in this essay. Then, this will illustrate the impacts of Confucianism on Vietnamese philosophical thinking in two aspects, which are ethics and education. Confucianisms origins and its core tenets Traced back to its history, in order to restore the rule of law and discipline of the Zhou Dynasty, Confucius established Confucianism in the Xuan Thu period (551 - 479 B.C). After Confucius dead, his disciples absorbed and passed it down to many generations. Therefore, understandably, it became the official ideology for China in both political and ethical. In addition, it was widespread and developed intensively in other Asian countries such as Japan, Korea, and, especially, Vietnam. As a long-standing doctrine in Vietnam, which had the opportunity to propagate and occupy a unique position in two periods: The later Le dynasty (1428-1527) and the Early Nguyen dynasty (1802 - 1883), Confucianism profoundly influenced all areas of Vietnamese social life. Confucianism is considered as a system of many saints ideologies, whose purposes are first, to centralize the role of people with ethics as its basement, and second, to use education as a tool for a peace, harmonious and, betterment society. Moreover, Confucianism perceived people's goodness includes: benevolence or ren.(仁), righteousness or yi (义), propriety or li (理), wisdom or zhi (智), and fidelity or xin (信) (Wang and Madson, 2013). Each individual must fulfill the Three Moral Bonds and the Five Key Relations to practice the Five Confucian virtues. Those who can do that would become a junzi (君子) - an ideal human model according to the Confucian worldview on life. There are three primary relationships: ruler-subject loyalty, father-son filial piety, and female devotion between husband and wife. The ruler to the subject, the father to the kid, the husband to the wife, the elder brother to the younger brother, and the friend to the friend are the five basic relationships under which all social contact occurs. Even inside friendship, a hierarchy is required to maintain peace. From its establishment, many basic disparities existed between Confucianism and other faiths' views, particularly in human affairs (Van, 2017). Confucianism places a strong emphasis on teaching people how to be human and training them to change evil into good. It can be seen that the Confucianism concept is a way to be human in a feudal society, but those moral concepts have helped it develop. Therefore, Confucianism has influenced the development of the Vietnam feudal society and has had a substantial impact on modern Vietnam's ethical and education systems. Influence of Confucianism on Vietnameses ethical consciousness As was mentioned previously, Confucian education centralized on ethics, and people's personalities, with the mission to develop ethical, intellectually comprehensive individuals who may serve as role models for others to study and emulate. Confucianism is distinguished by its emphasis on personal morality, with specific attention paid to the morals of people in positions of leadership. Indeed, Confucius instructs rulers to cultivate themselves to be a junzi to provide an example for those who follow them (Mai, 2010). As a result of fostering self-cultivation and considering it to be the core of personality training, Confucianism has established a class of ethical individuals. Furthermore, with the rigid system of regulations, Confucianism has made people treat each other with kindness, tolerance, and generosity. Confucian rites have a tremendous influence on sustaining order and discipline in society, which Vietnamese may inherit today. Confucianism argues that for a country to be severe, it is important to have laws; similarly, there must be upper and lower family laws in the family. Indeed, in The Luan Ngu (Luận Ngữ), Confucius once said: Children (or young people) at home are filial to their parents; when they go out, they respect their elders; be careful in their words but honest, love everyone and be close to benevolent people; If people can do that, or if people have enough aspiration, they can study literature (it is mean that to study poetry, letters, rituals, music, ...) (Mai, 2010). Confucius's words certainly encompass both a political and social philosophy of life. Filial piety or “xìao” (孝), a product of human moral development in the family, has evolved into a set of meritorious values that influence the nation's success or decline. Such a family is truly the foundation of the nation. It is clear that self-cultivation ideology has become an essential quality for not only individuals but also whole families and societies throughout the country. Legitimacy ideologies, understandably, assist people in identifying their responsibilities and obligations so that they can have thoughts and act appropriately in social situations. Thus, this ideology would be a proper strategy to educate the  Vietnamese in the long run. Influence of Confucianism on Vietnameses education In addition, education is a crucial part of Confucianism. With the motto of considering morality as the center of education, Confucianism especially emphasizes teaching and learning methods in the process of knowledge acquisition. Confucius consistently asserted, Reviewing old things and learning new things; then you may be a teacher, in the way he taught his students (Lan, 2013). This is fundamental, which means every learner has to revise and critically consider what was studied in the past. Students must exercise obtaining proficiency on a regular basis, according to Confucius, to make their thoughts more evident and lucid. However, there are some people who mistake that this way of learning is repetition, and rote memorization, even if they do not understand anything. They revised the lesson's content for months or years and did not attempt to research new knowledge. It is understandable that learning is a continuous process of seeking, learning, reviewing, freely seeing, willingly solidifying gained knowledge, and growing self-awareness, while also requiring the ability to think independently to find new things. Confucius thus advised learners to focus their minds after studying and implementing what they have learned to gain benefits from these. Confucius remarked: I will not educate those who do not want to learn; I will not teach those who do not strive to convey their thoughts. I shall stop teaching them if I reveal one part of the problem, but they do not bother to look for the other aspects (Lan, 2013). This is an evocative educational method, emphasizing the inherent personal capacity of learners in order to encourage learners to develop independence, promote their creativity, and at the same time show initiative and creativity of learners in the process of absorbing new knowledge. Therefore, learning requires not only complex study, revision, and repetition of what the instructor has taught, but also the ability to think, and reason about what has been learned. Learning must be linked to thinking to research causes and origins, learning to grasp social life principles and standards of behavior to become informed individuals, and learning to make systematic conclusions. So, what can Vietnam's modern education learn from Confucianism? Vietnam belongs to the group of countries with a high rate of expenditure on education compared to many countries in the world (Hoa, 2020). This illustrated that education is a central part of Vietnam society. Besides, as mentioned before, Confucianism strongly emphasizes the key role of education. Therefore, Vietnam has been undergoing educational reform in recent years, modernizing teaching techniques to allow students to investigate and reflect on their own, including learning methods paired with practice, initiative, and creativity. This instructional technique has truly aided students in not only grasping the lecture swiftly and thoroughly, but also in developing the habit of independent thinking through self-study, self-research, and self-solution. Consequently, learners will be able to optimize their own potential and be able to rely on the teacher's ideas to grow and enhance their knowledge. Confucian education also refers to the approach of motivating learners via interaction between instructors and learners, in addition to the learning method paired with practice. This is not merely passive, one-way receiving as in the past, but a process of interaction and reciprocal learning between teachers and learners, as well as learners and learners. Incorporating this lesson into the existing educational technique will help create a class of individuals who actively adapt to the market mechanism and satisfy the country's practical demands. There is also a way in traditional Confucianism-inspired teaching that is incredibly significant to Vietnamese education today: the approach of setting an example. This method is particularly crucial since the teacher's personal example has a significant influence on learners' awareness. The teacher is not only a person who imparts knowledge but also a shining example of moral development for pupils to emulate. Furthermore, instructors strive to motivate students by displaying Confucius' tireless learning attitude by continually improving their credentials, and updating new achievements and outcomes in their majors to impart to pupils. Thereby, the foundation for conventional education in human education and training is laid. In the current state of affairs in our nation, when signs of degradation in the moral quality of a portion of the teaching staff are on the rise, a return to traditional education, as well as an understanding and implementation of the exemplary method, is both essential and worthwhile. Conclusion To summarize, Confucianism has had several influences on Vietnamese philosophical thought over the course of the country's lengthy history. Despite the fact that Confucianism is a socio-political philosophy that dates back to ancient times, Confucius' Confucian thinking affected many elements of social life, greatly impacting people's ethics and education in modern Vietnamese society. Confucianism no longer exists; however, its principles will most likely continue to pervade the Vietnamese way of life in the future.",
        },
        {
            "title": "The Temple of Literature in Hanoi, Vietnam",
            "content": "The temple was built in 1070 during the Lý Thánh Tông period. In 1076, Vietnam's first university, the Quốc Tử Giám or Imperial Academy, was established within the temple during the reign of Lý Nhân Tông to educate Vietnam's bureaucrats, nobles, royalty, and other members of the elite. The space of the Temple of Literature is divided into 5 layers linked by brick walls with open doors (followed by 1, 2, 3, 4, and 5). All of them are designed according to a unified Shinto axis [1]. One of the first reasons when building the Temple of Literature is to ensure all the factors related to feng shui, especially to balance the yin and yang elements. Next to the building (with positive elements) is lake, behind is the mountain, and in front of the Temple of Literature, there is always a lake Hồ Văn (with negative elements) [1]. This is also one of the elements showing feng shui in Eastern architecture. Known as a place of worship of Confucius and Confucianism, how are the elements of feng shui and the philosophy of Yin and Yang reflected in the relic complex bearing the studious spirit of the Vietnamese people from time immemorial? "
        }
    ]
    return text_data

# ------------------------ CLARIFY AGENT ------------------------

def CLARIFY_AGENT(session_id, user_message):
    try:
        rag_chain = rag_chains()

        def get_session_history_wrapper(session_id: str) -> BaseChatMessageHistory:
            return get_session_history(session_id)

        with_message_history = RunnableWithMessageHistory(
            rag_chain,
            get_session_history_wrapper,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

        def get_response(message: str):
            store_message(session_id, 'human', message, 0, 0)
            human_message = HumanMessage(content=message)
            response = with_message_history.invoke({"input": human_message}, config={"configurable": {"session_id": session_id}})
            store_message(session_id, 'agent', response["answer"], 0, 0)
            return response["answer"]

        response = get_response(user_message)

        result = {
            "response": response,
        }

        return result

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {"error": str(e)}