'use client'
import React from 'react';
import Logo from './public/logo.png';
import { MdUploadFile } from "react-icons/md";
import { LuClipboardList } from "react-icons/lu";
import { MdOutlineChat } from "react-icons/md";
import { usePathname } from "next/navigation";
import { GiProcessor } from "react-icons/gi";

export default function Navbar() {
    const pathname = usePathname();
    const isActive = (path: string) => pathname === path ? "active" : "";
return (
    <nav>
            <div className='pb-6'>
                <img src='https://itviec.com/rails/active_storage/representations/proxy/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBBeVV3REE9PSIsImV4cCI6bnVsbCwicHVyIjoiYmxvYl9pZCJ9fQ==--19d97db48a220fd99592dd064d605d8f039e1a70/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaDdCem9MWm05eWJXRjBTU0lJY0c1bkJqb0dSVlE2RkhKbGMybDZaVjkwYjE5c2FXMXBkRnNIYVFJc0FXa0NMQUU9IiwiZXhwIjpudWxsLCJwdXIiOiJ2YXJpYXRpb24ifX0=--15c3f2f3e11927673ae52b71712c1f66a7a1b7bd/solazu-logo.png' alt="Logo" />
            </div>
            <button onClick={() => window.location.href = '/ask'} className={isActive('/ask')}>
                <MdOutlineChat className='img'/>
                Ask
            </button>
            <button onClick={() => window.location.href = '/portal'} className={isActive('/portal')}>
                <MdUploadFile className='img'/>
                Portal
            </button>
            <button onClick={() => window.location.href = '/'} className={isActive('/')}>
                <LuClipboardList className='img'/>
                Req
            </button>
            <button onClick={() => window.location.href = '/prompt'} className={isActive('/prompt')}>
                <GiProcessor  className='img'/>
                Prompt    
            </button>
    </nav>
);
}

