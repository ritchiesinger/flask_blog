import React, {Component} from 'react'
import { Link } from "react-router-dom"
import { getProfile } from '../api/Api'
import Cookies from 'js-cookie'

export default class Header extends Component {
  constructor(props) {
    super(props)
    this.state = {}
  }
  componentDidMount = () => {
      const token = Cookies.get('token')
      getProfile(this, token)
  }
  logOut = () => {
    const {parentComponent} = this.props
    Cookies.remove('token')
    Cookies.remove('user')
    parentComponent.forceUpdate()
  }
  render() {
    const {activePage} = this.props
    const user = this.props.user ? this.props.user : {login: null, id: null, roles: []}
    const {roles, login} = user
    return (
      <header className="App-header">
        <nav className="navbar navbar-expand-lg navbar-light bg-light">
          <div className="container-fluid">
            <span className="navbar-brand btn">Web App</span>
            <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
                <span className="navbar-toggler-icon"></span>
            </button>
            <div className="collapse navbar-collapse" id="navbarSupportedContent">
              <div className="navbar-nav me-auto mb-2 mb-lg-0">
                {roles.includes("admin") ? <Link to='/admin_users' style={{ textDecoration: 'none' }}><span className={`nav-link btn ${activePage === 'users' ? ' active' : ''}`} aria-current="page">Пользователи</span></Link> : null}
                {roles.includes("admin") ? <span className="nav-link btn">Роли</span> : null}
              </div>
              <div className="navbar-nav d-flex">
                <Link to='/profile' style={{ textDecoration: 'none' }}><span className={`nav-link btn${activePage === 'profile' ? ' active' : ''}`}>{login}</span></Link>
                <span className="nav-link btn" onClick={this.logOut}>Выйти</span>
              </div>
            </div>
          </div>
        </nav>
      </header>
    );
  }
}  
