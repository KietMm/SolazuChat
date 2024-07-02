'use client'
import React, { useState, useRef, useEffect } from 'react';
import './home.css'; // Ensure this imports your CSS styles
import Select from './component/select';
import { LuClipboardList } from 'react-icons/lu'; // Import icon
import ReactMarkdown from 'react-markdown';
import { FaArrowLeftLong } from "react-icons/fa6";
import { FaArrowCircleUp } from "react-icons/fa";
import InputArea from './component/inputArea';
import { IoIosCheckmarkCircle } from "react-icons/io";
import { IoWarning } from "react-icons/io5";
import { IoIosArrowDown } from "react-icons/io";
import { IoIosArrowUp } from "react-icons/io";
import { Spinner } from "flowbite-react";

const Home: React.FC = () => {
  const [projects, setProjects] = useState<string[]>([]);
  const [epics, setEpics] = useState<{ key: string, name: string }[]>([]);
  const [tickets, setTickets] = useState<any[]>([]); // Adjust type as needed
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [selectedEpic, setSelectedEpic] = useState<string>('');
  const [selectedTicket, setSelectedTicket] = useState<{ url: string, key: string }>();
  const [contentData, setContentData] = useState<{ title: string, content: string } | null>(null);
  const [showChatGPT, setShowChatGPT] = useState<boolean>(false);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const chatHistoryRef = useRef(null);
  const questionRefs = useRef([]);
  const [focusedQuestionIndex, setFocusedQuestionIndex] = useState(null);
  const [isFetching, setIsFetching] = useState(false);

  const fetchProjects = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/getProjectsList');
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      setProjects(data);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const fetchEpics = async (projectName: string) => {
    try {
      const response = await fetch(`http://127.0.0.1:5000/getEpicsList?projectName=${projectName}`);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      setEpics(data.epics);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const fetchTickets = async (projectName: string, epicKey: string) => {
    try {
      const response = await fetch(`http://127.0.0.1:5000/getTicketsList?projectName=${projectName}&epicKey=${epicKey}`);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      setTickets(data.tickets);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const fetchContentData = async (projectName: string, epicKey: string, ticketKey: string, url: string) => {
    try {
      const response = await fetch('http://127.0.0.1:5000/getContentData', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ projectName, epicKey, ticketKey, url }),
      });
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      setContentData(data);
    } catch (error) {
      console.error('Error fetching content data:', error);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleProjectSelect = (projectName: string) => {
    setSelectedProject(projectName);
    fetchEpics(projectName);
    setSelectedEpic('');
    setSelectedTicket(undefined); // Fix: Pass undefined instead of null
    setContentData(null);
  };

  const handleEpicSelect = (epicName: string) => {
    const selectedEpic = epics.find(epic => epic.name === epicName);
    if (selectedEpic) {
      setSelectedEpic(selectedEpic.key);
      fetchTickets(selectedProject, selectedEpic.key);
      setSelectedTicket(undefined);
      setContentData(null);
    }
  };

  const handleTicketSelect = (ticketName: string) => {
    const selectedTicket = tickets.find(ticket => ticket.name === ticketName);
    if (selectedTicket) {
      setSelectedTicket(selectedTicket);
      fetchContentData(selectedProject, selectedEpic, selectedTicket.key, selectedTicket.url);
      console.log('Selected ticket:', selectedTicket);
    }
  };

  const handleReplyClick = (question) => {
    if (question.sessionID !== currentQuestion?.sessionID) {
      setCurrentQuestion(question);
      setShowChatGPT(true);
      fetchSessionHistory(question.sessionID);
    }
  };

  const handleSendMessage = (userMessage: string) => {
    sendMessageToGPT(userMessage);
  };

  const postQuestion = async () => {
    try {
      setIsFetching(true);
      const response = await fetch('http://127.0.0.1:5000/getQuestion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          projectName: selectedProject,
          epicKey: selectedEpic,
          url: selectedTicket.url,
          ticketKey: selectedTicket.key,
        })
      });
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const postData = await response.json();
      if (postData.success) {
        fetchQuestionsFromDatabase();
      }
      setIsFetching(false);
    } catch (error) {
      console.error('Error posting question:', error);
    }
  };

  const fetchQuestionsFromDatabase = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/getQuestionfromDatabase',{
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          projectName: selectedProject,
          epicKey: selectedEpic,
          url: selectedTicket.url,
          ticketKey: selectedTicket.key,
        })
      });
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const questionsData = await response.json();
      console.log('Questions:', questionsData);
      setQuestions(questionsData);
    } catch (error) {
      console.error('Error fetching questions:', error);
    }
  };

  const fetchSuggestions = async (sessionId) => {
    try {
      const response = await fetch('http://127.0.0.1:5000/getSuggestion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          projectName: selectedProject,
          epicKey: selectedEpic,
          url: selectedTicket.url,
          ticketKey: selectedTicket.key,
          sessionId
        })
      });
      const data = await response.json();
      console.log('Suggestions:', data);
      if (data.success === "Questions generated successfully") {
        setSuggestions([data.response]);  // Set the suggestions from the API response
      }
    } catch (error) {
      console.error('Error fetching suggestions:', error);
    }
  };

  const sendMessageToGPT = async (userMessage) => {
    const newUserMessage = { sender: 'Human', content: userMessage };
    setChatHistory(prev => [...prev, newUserMessage]);

    try {
      const response = await fetch('http://127.0.0.1:5000/getClarify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          projectName: selectedProject,
          epicKey: selectedEpic,
          url: selectedTicket.url,
          sessionId: currentQuestion.sessionID,
          userMessage
        })
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();
    } catch ( error ) {
      console.error('Error sending message to GPT:', error);
    }
  };

  const fetchSessionHistory = async (sessionId) => {
    try {
      const response = await fetch(`http://127.0.0.1:5000/getSessionHistory?sessionId=${sessionId}`);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      const formattedHistory = data.map(item => ({
        sender: item.Human ? 'Human' : 'Agent',
        content: item.Human || item.Agent,
      }));
      setChatHistory(formattedHistory);
    } catch (error) {
      console.error('Error fetching session history:', error);
    }
  };

  const handleResolveClick = async (index) => {
    const question = questions[index];
    const newStatus = question.status === null ? 'manual' : null;

    // Prepare the data to send in the POST request
    const requestData = {
        sessionID: question.sessionID,
        status: newStatus
    };

    try {
        const response = await fetch('http://127.0.0.1:5000/markResolved', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData) // Convert the JavaScript object to a JSON string
        });

        if (!response.ok) throw new Error('Network response was not ok');

        // If the POST is successful, update the local state to reflect the new status
        const updatedQuestions = questions.map((q, idx) => idx === index ? { ...q, status: newStatus } : q);
        setQuestions(updatedQuestions); // Update state to reflect the new status
    } catch (error) {
        console.error('Error updating question status:', error);
    }
};

  useEffect(() => {
    const intervalId = setInterval(() => {
      if (currentQuestion && currentQuestion.sessionID) {
        fetchSessionHistory(currentQuestion.sessionID);
      }
    }, 3000);  // Fetch every 5000 milliseconds (5 seconds)
  
    return () => clearInterval(intervalId);  // Clear the interval when the component unmounts
  }, [currentQuestion]);

  useEffect(() => {
    if (chatHistoryRef.current) {
      const { current } = chatHistoryRef;
      current.scrollTop = current.scrollHeight;
    }
  }, [chatHistory])

  useEffect(() => {
    questionRefs.current = questionRefs.current.slice(0, questions.length);
  }, [questions]);

  const scrollToQuestion = (index) => {
    questionRefs.current[index]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  const handleArrowClick = (direction) => {
    if (questions.length === 0) return;

    let currentIndex = focusedQuestionIndex !== null ? focusedQuestionIndex : (direction === 'down' ? -1 : questions.length);
    let newIndex = currentIndex;

    do {
        newIndex = direction === 'down' ? (newIndex + 1) % questions.length : (newIndex - 1 + questions.length) % questions.length;

        // If we loop around to the starting index, stop to prevent infinite loop
        if (newIndex === currentIndex) break;

    } while (questions[newIndex].status !== null);  // Skip over resolved questions

    if (questions[newIndex].status === null) {
        setFocusedQuestionIndex(newIndex);
        scrollToQuestion(newIndex);
    }
    // Optional: Automatically scroll to the new focused question
    document.querySelector(`#question-${newIndex}`).scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  return (
    <div className="outer">
      <div className="selectTicket">
        <Select options={projects} kind="project" onSelect={handleProjectSelect} />
        <Select options={epics.map(epic => epic.name)} kind="epic" onSelect={handleEpicSelect} />
        <Select options={tickets.map(ticket => ticket.name)} kind="ticket" onSelect={handleTicketSelect} />
        <button onClick={postQuestion}>{isFetching ? (<Spinner className='fill-cyan-600' aria-label="Warning spinner example" />):(null)} Clarify</button>
      </div>
      <div className="container">
        <div className="heading">
          <LuClipboardList className='img'/>
          <h1>Clarify Requirement</h1>
        </div>
        <div className="chat">
          <div className="document">
            <div className="title">
              {contentData && <h2>{contentData.title}</h2>}
            </div>
            <div className="doc" dangerouslySetInnerHTML={{ __html: contentData?.content || '' }}></div>
          </div>
          <div className="question">
            {showChatGPT ? (
              <div className="chatGPT">
                <div className='button'>
                  <button onClick={() => setShowChatGPT(false)}><FaArrowLeftLong /></button>
                  <div className='text-black font-bold text-lg'>Question: {currentQuestion ? currentQuestion.question : 'No question selected'}</div>
                </div>
                <div className='GPT'>
                    <div className='chatHistory' ref={chatHistoryRef}>
                      {chatHistory.map((entry, index) => (
                        <div key={index} className={`message ${entry.sender}`}>
                          <div>
                            <img src='https://itviec.com/rails/active_storage/representations/proxy/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBBeVV3REE9PSIsImV4cCI6bnVsbCwicHVyIjoiYmxvYl9pZCJ9fQ==--19d97db48a220fd99592dd064d605d8f039e1a70/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaDdCem9MWm05eWJXRjBTU0lJY0c1bkJqb0dSVlE2RkhKbGMybDZaVjkwYjE5c2FXMXBkRnNIYVFJc0FXa0NMQUU9IiwiZXhwIjpudWxsLCJwdXIiOiJ2YXJpYXRpb24ifX0=--15c3f2f3e11927673ae52b71712c1f66a7a1b7bd/solazu-logo.png'  alt="Logo" />
                            <p>{entry.content}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className='suggestions'>
                      {suggestions.map((suggestion, index) => (
                        <button key={index} onClick={() => sendMessageToGPT(suggestion)}></button>
                      ))}
                    </div>
                    <InputArea onSendMessage={handleSendMessage} />
                  </div>
              </div>
            ) : (
              <div className="clarify">
                {questions.length > 0 && (
                  <div className='clarifyHeading'>
                    <IoWarning className='warning'/>
                    <span>Unresolved questions: {questions.filter(q => q.status === null).length}/{questions.length} ||</span>
                    <button onClick={() => handleArrowClick('down')}><IoIosArrowDown className='arrow'/></button>
                    <button onClick={() => handleArrowClick('up')}><IoIosArrowUp className='arrow' /></button>
                  </div>
                )}
                  <div className='clarifyQuestion'>
                    {questions.map((question, index) => (
                      <div key={index} id={`question-${index}`} className={`questionBox ${index === focusedQuestionIndex ? 'focused' : ''}`}>
                        <p>Question {index + 1}: {question.question}</p>
                        <div className='buttonBox'>
                          <button className='reply' onClick={() => handleReplyClick(question)}>Reply</button>
                          <div>
                            <button className='resolve' onClick={() => handleResolveClick(index)}>
                              {question.status === null ? 'Unresolve' : 'Resolved Manual'}
                            </button>
                            {question.status === null ? <IoWarning className='warning'/> : <IoIosCheckmarkCircle className='checkmark'/>}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
            </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;