import React, {Component} from 'react'
import { Routes, Route } from "react-router-dom";
import LoginPage from './pages/LoginPage'
import ProfilePage from './pages/ProfilePage'
import RegistrationPage from './pages/RegistrationPage'
import AdminUsersPage from './pages/AdminUsersPage'
import getToken from './api/Api'

export default class App extends Component {
  constructor(props) {
    super(props)
    this.state = {
      loading: false,
      profile: {login: null, id: null, roles: []}
    }
  }
  componentDidMount = () => {}
  singIn = (login, password) => {
    getToken(this, login, password)
  }
  render() {
    return (
      <div className="App">
        <Routes>
          <Route path="/login" element={<LoginPage singIn={this.singIn} />} />
          <Route path="/registration" element={<RegistrationPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/admin_users" element={<AdminUsersPage />} />
          <Route path="/" element={<ProfilePage />} />
        </Routes>
      </div>
    );
  }
}  
