import React, {Component} from 'react'
import { Routes, Route } from "react-router-dom";
import LoginPage from './pages/LoginPage'
import ProfilePage from './pages/ProfilePage'


export default class App extends Component {
  constructor(props) {
    super(props)
    this.state = {
      loading: true
    }
  }
  componentDidMount = () => {}
  render() {
    return (
      <div className="App">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/" element={<ProfilePage />} />
        </Routes>
      </div>
    );
  }
}  
