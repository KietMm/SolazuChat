'use client'
import { useEffect, useState } from 'react';
import './portal.css';
import CustomSelect from '../component/selectPortal';
import { SlCloudUpload } from "react-icons/sl";
import { BsFillArrowUpRightCircleFill } from "react-icons/bs";
import Tabs from '../component/inputTab';
import Loading from '../component/Loading';
import { FaRegTrashCan } from "react-icons/fa6";
import { Alert } from "flowbite-react";

const Portal = () => {
    const [projects, setProjects] = useState<string[]>([]);
    const [epics, setEpics] = useState<string[]>([]);
    const [tickets, setTickets] = useState<string[]>([]);
    const [selectedProject, setSelectedProject] = useState<string>('');
    const [selectedEpic, setSelectedEpic] = useState<string>('');
    const [selectedTicket, setSelectedTicket] = useState<string | null>(null);
    const [links, setLinks] = useState<{ [key: string]: string[] }>({
        jira: [],
        confluence: [],
        docs: [],
        github: []
    });
    const [tableData, setTableData] = useState<any[]>([]);
    const [isFetching, setIsFetching] = useState<boolean>(false);
    const [alertType, setAlertType] = useState<string | null>(null);
    const [alertMessage, setAlertMessage] = useState<string | null>(null);

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

    const fetchTableData = async (projectName: string, epicKey?: string, ticketKey?: string) => {
        try {
            const response = await fetch('http://127.0.0.1:5000/getLink', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ projectName, epicKey, ticketKey })
            });
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            setTableData(data[0].links_status);
            console.log('Table data:', data[0].links_status);
        } catch (error) {
            console.error('Error fetching table data:', error);
        }
    };

    useEffect(() => {
        fetchProjects();
    }, []);

    const handleProjectSelect = (projectName: string) => {
        setSelectedProject(projectName);
        fetchEpics(projectName);
        setSelectedEpic('');
        setSelectedTicket(null);
        fetchTableData(projectName); // Fetch table data for the selected project
    };

    const handleEpicSelect = (epicName: string) => {
        const selectedEpic = epics.find(epic => epic.name === epicName);
        if (selectedEpic) {
            setSelectedEpic(selectedEpic.key);
            fetchTickets(selectedProject, selectedEpic.key);
            setSelectedTicket(null);
            fetchTableData(selectedProject, selectedEpic.key); // Fetch table data for the selected epic
        }
    };

    const handleTicketSelect = (ticketName: string) => {
        const selectedTicket = tickets.find(ticket => ticket.name === ticketName);
        if (selectedTicket) {
            setSelectedTicket(selectedTicket);
            console.log('Selected ticket:', selectedTicket);
            fetchTableData(selectedProject, selectedEpic, selectedTicket.key); // Fetch table data for the selected ticket
        }
    };

    const handleLinkChange = (tab: string, index: number, value: string) => {
        // Categorize links based on their content
        const categorizeLink = (link: string) => {
            if (link.includes('.atlassian.net/jira')) {
                return 'jira';
            } else if (link.includes('https://github.com/')) {
                return 'github';
            } else if (link.includes('atlassian.net/wiki/pages')) {
                return 'confluence';
            } else if (link.includes('https://docs.google.com/')) {
                return 'docs';
            } else {
                return tab;
            }
        };

        const categorizedTab = categorizeLink(value);

        if (categorizedTab !== tab && value) {
            setAlertType(`Wrong type: `);
            setAlertMessage(`Check the ${categorizedTab.charAt(0).toUpperCase() + categorizedTab.slice(1)} Link`);
        }

        // Remove empty links
        setLinks((prevLinks) => {
            const updatedLinks = { ...prevLinks };
            updatedLinks[tab] = prevLinks[tab].filter((_, i) => i !== index);
            if (value) {
                updatedLinks[categorizedTab] = [...prevLinks[categorizedTab], value];
            }
            return updatedLinks;
        });
    };

    const handleAddLink = (tab: string) => {
        setLinks((prevLinks) => ({
            ...prevLinks,
            [tab]: [...prevLinks[tab], '']
        }));
    };

    const handleSubmit = async () => {
        const payload = {
            projectName: selectedProject,
            githubLink: links.github.filter(link => link !== ''),
            jiraLink: links.jira.filter(link => link !== ''),
            docsLink: links.docs.filter(link => link !== ''),
            confluenceLink: links.confluence.filter(link => link !== '')
        };

        try {
            setIsFetching(true);
            const response = await fetch('http://127.0.0.1:5000/addToDatabase', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            console.log(data);

            setLinks({
                jira: [''],
                confluence: [''],
                docs: [''],
                github: ['']
            });
            fetchTableData(selectedProject, selectedEpic, selectedTicket ? selectedTicket.key : undefined);
            setIsFetching(false);
        } catch (error) {
            console.error('Error submitting data:', error);
        }
    };

    const handleAlertDismiss = () => {
        setAlertType(null);
        setAlertMessage(null);
    };

    useEffect(() => {
        if (alertType && alertMessage) {
            const timer = setTimeout(() => {
                setAlertType(null);
                setAlertMessage(null);
            }, 5000); // 5 seconds
    
            return () => clearTimeout(timer); // Cleanup the timer on component unmount
        }
    }, [alertType, alertMessage]);

    return (
        <div className='portal'>
            <div className='heading'>
                <div className='text'>
                    <SlCloudUpload className='icon'/>
                    <h1><strong>Portal - Create & Update Dataset</strong></h1>
                </div>
                <div className='alert'>
                    {alertType && alertMessage && (
                        <Alert className='border-red-500 bg-red-100 rounded-lg flex flex-col gap-2 p-4 text-sm w-full mr-6' onDismiss={handleAlertDismiss}>
                            <span className="font-semibold text-red-700">{alertType}</span>
                            <span className='font-normal text-red-700 ml-1'>{alertMessage}</span>
                        </Alert>
                    )}
                </div>
            </div>
            <div className='input'>
                <div className='step1'>
                    <div className='description'>
                        <h1><strong>Step 1:</strong>Select existing projects and epics to update or type to create new one</h1>
                    </div>
                    <div className='select'>
                        <CustomSelect options={projects} kind="project" onSelect={handleProjectSelect} />
                        <CustomSelect options={epics.map(epic => epic.name)} kind="epic" onSelect={handleEpicSelect} />
                        <CustomSelect options={tickets.map(ticket => ticket.name)} kind="ticket" onSelect={handleTicketSelect} />
                    </div>
                </div>
                <div className='arrow'>
                    <BsFillArrowUpRightCircleFill className='upArrow'/>
                </div>
                <div className='step2'>
                    <div className='description'>
                        <h1><strong>Step 2:</strong>Input your data</h1>
                    </div>
                    <div className='link'>
                        <Tabs
                            links={links}
                            onLinkChange={handleLinkChange}
                            onAddLink={handleAddLink}
                        />
                    </div>
                    <button className='submit' onClick={handleSubmit}>Submit</button>
                </div>
            </div>
            <div className='dataset'>
                <div className='description'>
                    <h1><strong>Dataset in selected project</strong></h1>
                </div>
                {isFetching ? (<div className='w-screen'><Loading/></div>): null}
                {tableData.length === 0 ? (null):(
                    <div className='table'>
                        <div className='table-row'>
                            <div className='cell-index'></div>
                            <div className='cell-URL header'>File name</div>
                            <div className='cell-date header'>Date</div>
                            <div className='cell-status header'>Status</div>
                            <div className='cell-action'></div>
                        </div>
                        <div className='tableData'>
                        {tableData.map((item, index) => (
                            <div key={index} className='data'>
                                <div className='cell-index'>{index + 1}</div>
                                <div className='cell-URL'><a href={item.url} target="_blank" rel="noopener noreferrer">{item.url}</a></div>
                                <div className='cell-date'>{item.date}</div>
                                <div className={`cell-status ${item.status}`}>{item.status}</div>
                                <div className='cell-action'><button><FaRegTrashCan /></button></div>
                            </div>
                        ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
};

export default Portal;
