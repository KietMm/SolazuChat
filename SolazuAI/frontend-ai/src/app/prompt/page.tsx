'use client'
import React, { useState, useEffect } from 'react';
import './prompt.css';
import { Alert } from "flowbite-react";

const Prompt = () => {
    const roles = ['CLARIFY', 'CHAT', 'SUGGESTION'];
    const [selectedRole, setSelectedRole] = useState('CLARIFY');
    const [prompt, setPrompt] = useState(null);
    const [isEditing, setIsEditing] = useState(false);
    const [alertMessage, setAlertMessage] = useState('');
    const [alertType, setAlertType] = useState(String);
    const [showAlert, setShowAlert] = useState(false);

    useEffect(() => {
        fetch(`http://127.0.0.1:5000/getPrompt?role=${selectedRole}`)
            .then(res => res.json())
            .then(data => {
                setPrompt(data);
                setIsEditing(false);
            })
            .catch(err => {
                console.error(`Failed to fetch prompts for ${selectedRole}:`, err);
                setAlertMessage('Failed to fetch prompts. Please try again.');
                setAlertType('Error fetching prompts!!');
                setShowAlert(true);
            });
    }, [selectedRole]);

    const handleRoleChange = (e) => {
        setSelectedRole(e.target.value);
    };

    const handleEditClick = () => {
        setIsEditing(true);
    };

    const handleSaveClick = () => {
        fetch('http://127.0.0.1:5000/setPrompt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ...prompt, role: selectedRole })
        })
        .then(response => response.json())
        .then(() => {
            setIsEditing(false);
            setAlertType('Prompt saved successfully!');
            setAlertMessage('The prompt has been updated');
            setShowAlert(true);
            setTimeout(() => setShowAlert(false), 3000);  
        })
        .catch(err => {
            console.error('Failed to save prompt:', err);
            setAlertMessage('Failed to save prompt. Please try again.');
            setShowAlert(true);
        });
    };

    return (
        <div className='promptManager'>
            <div className='heading'>
                <h1>Prompt Manager</h1>
                {showAlert && <Alert className='border-green-500 bg-green-100 rounded-lg flex flex-col gap-2 p-4 text-sm w-auto mr-6' onDismiss={() => alert('Alert dismissed!')}><span className="font-semibold text-green-700">{alertType}</span><span className='font-normal text-green-700 ml-1'>{alertMessage}</span></Alert>}
            </div>
            {prompt && (
                <div className='prompt'>
                    <div className='selection'>
                        <select value={selectedRole} onChange={handleRoleChange}>
                        {roles.map(role => (
                            <option key={role} value={role}>ROLE: {role}</option>
                        ))}
                        </select>
                        {isEditing ? (<span>Editing...</span>) : (<span>Viewing mode</span>)}
                    </div>
                    <div className='display'>
                        <div className='description'>
                            <h2>Contextualize Question System Prompt</h2>
                            <li><strong>Refocuses Questions:</strong> Converts user queries into self-contained questions that don't rely on chat history, making them clear and independent.</li>
                            <li><strong>Clarification:</strong> Sharpens the clarity of questions for better processing, ensuring the AI understands and responds more accurately.</li>
                            <li><strong>Consistency in Queries:</strong> Promotes a uniform query format that aids the AI in recognizing and responding to user inputs more efficiently.</li>
                        </div>
                        <textarea
                            value={prompt.contextualize_q_system_prompt}
                            onChange={(e) => setPrompt({...prompt, contextualize_q_system_prompt: e.target.value})}
                            disabled={!isEditing}
                        />
                        <div className='description'>
                            <h2>Question Answering System Prompt</h2>
                            <li><strong>Context Integration:</strong> Guides the AI to utilize all available context to formulate accurate and relevant answers.</li>
                            <li><strong>Concision and Relevance:</strong> Encourages brief and direct responses, limiting answers to three sentences for clarity and impact.</li>
                            <li><strong>Adaptive Responses:</strong> Prepares the system to acknowledge its limitations by explicitly stating if the answer is unknown, thus setting realistic expectations for the user.</li>
                        </div>
                        <textarea
                            value={prompt.qa_system_prompt}
                            onChange={(e) => setPrompt({...prompt, qa_system_prompt: e.target.value})}
                            disabled={!isEditing}
                        />
                        {isEditing ? (
                            <button onClick={handleSaveClick}>Save</button>
                        ) : (
                            <button onClick={handleEditClick}>Edit</button>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default Prompt;
