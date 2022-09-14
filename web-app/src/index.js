import React from 'react';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { BrowserRouter } from "react-router-dom";
import { createRoot } from 'react-dom/client';
import iconsCss from '../node_modules/bootstrap-icons/font/bootstrap-icons.css' // eslint-disable-line no-unused-vars
import mainCss from './index.css'

const container = document.getElementById('root');
const root = createRoot(container);
root.render(<BrowserRouter><App /></BrowserRouter>);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
